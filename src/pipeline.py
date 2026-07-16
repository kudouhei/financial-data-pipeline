from __future__ import annotations

import argparse
from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd
from jinja2 import Template

from src.config import PipelineConfig, ensure_output_dirs
from src.extract import extract_with_metadata
from src.load import load_to_postgres, write_processed_csv
from src.metrics import build_metric_outputs, render_kpi_markdown
from src.quality_checks import run_quality_checks
from src.transform import transform_all


QUALITY_REPORT_TEMPLATE = Template(
    """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Data Quality Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }
    table { border-collapse: collapse; width: 100%; margin-top: 16px; }
    th, td { border: 1px solid #d1d5db; padding: 8px; text-align: left; }
    th { background: #f3f4f6; }
    .score { font-size: 32px; font-weight: 700; }
    .high { color: #b91c1c; font-weight: 700; }
    .medium { color: #b45309; font-weight: 700; }
  </style>
</head>
<body>
  <h1>Financial Data Quality Report</h1>
  <p class="score">Quality score: {{ score }}</p>
  <p>Generated from daily customer, transaction, invoice, and FX source files.</p>
  <table>
    <thead>
      <tr>
        <th>Table</th>
        <th>Check</th>
        <th>Severity</th>
        <th>Total Rows</th>
        <th>Failed Rows</th>
        <th>Failed Rate</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {% for issue in issues %}
      <tr>
        <td>{{ issue.table_name }}</td>
        <td>{{ issue.check_name }}</td>
        <td class="{{ issue.severity }}">{{ issue.severity }}</td>
        <td>{{ issue.total_rows }}</td>
        <td>{{ issue.failed_rows }}</td>
        <td>{{ "%.2f%%"|format(issue.failed_rate * 100) }}</td>
        <td>{{ issue.status }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
"""
)


def run_pipeline(load_database: bool = False) -> dict[str, object]:
    config = PipelineConfig()
    ensure_output_dirs(config)

    run_id = str(uuid4())
    started_at = datetime.now(UTC)
    raw, extract_metadata = extract_with_metadata(config.raw_data_dir)
    transformed = transform_all(raw, config.as_of_date)
    quality_issues = run_quality_checks(raw, transformed, run_id, extract_metadata)
    metrics = build_metric_outputs(transformed, quality_issues)
    quality_score_value = metrics["kpis"].set_index("metric").loc[
        "data_quality_score", "value"
    ]
    pipeline_runs = extract_metadata.assign(
        run_id=run_id,
        started_at=started_at.isoformat(),
        completed_at=datetime.now(UTC).isoformat(),
        quality_score=quality_score_value,
    )
    pipeline_runs_path = config.processed_data_dir / "pipeline_runs.csv"
    if pipeline_runs_path.exists():
        previous_runs = pd.read_csv(pipeline_runs_path)
        pipeline_runs = pd.concat([previous_runs, pipeline_runs], ignore_index=True)

    output_datasets = {
        "raw_customers": raw["customers"],
        "raw_transactions": raw["transactions"],
        "raw_invoices": raw["invoices"],
        "raw_fx_rates": raw["fx_rates"],
        "stg_customers": transformed["customers"],
        "stg_transactions": transformed["transactions"],
        "stg_invoices": transformed["invoices"],
        "dim_customers": transformed["customers"],
        "fact_transactions": transformed["transactions"],
        "fact_invoices": transformed["invoices"],
        "data_quality_results": quality_issues,
        "pipeline_runs": pipeline_runs,
        "mart_kpis": metrics["kpis"],
        "mart_revenue_by_customer": metrics["revenue_by_customer"],
        "mart_aging_buckets": metrics["aging_buckets"],
        "mart_dso_by_segment": metrics["dso_by_segment"],
        "mart_dso_by_country": metrics["dso_by_country"],
        "mart_collection_priority": metrics["collection_priority"],
        "mart_fx_exposure": metrics["fx_exposure"],
        "mart_quality_by_dataset": metrics["quality_by_dataset"],
        "mart_quality_impact": metrics["quality_impact"],
    }

    write_processed_csv(output_datasets, config.processed_data_dir)

    report_html = QUALITY_REPORT_TEMPLATE.render(
        score=quality_score_value,
        issues=quality_issues.to_dict(orient="records"),
    )
    (config.reports_dir / "data_quality_report.html").write_text(report_html, encoding="utf-8")
    (config.reports_dir / "sample_kpi_report.md").write_text(
        render_kpi_markdown(metrics),
        encoding="utf-8",
    )

    if load_database:
        load_to_postgres(output_datasets, config.database_url)

    return {
        "raw": raw,
        "transformed": transformed,
        "quality_issues": quality_issues,
        "metrics": metrics,
        "pipeline_runs": pipeline_runs,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the financial data pipeline.")
    parser.add_argument(
        "--load-database",
        action="store_true",
        help="Load transformed data and marts into PostgreSQL.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(load_database=args.load_database)
