from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTING_VIEWS = [
    "v_dashboard_summary",
    "v_quality_issues_by_dataset",
    "v_customer_revenue_rank",
]


def write_processed_csv(datasets: dict[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for old_file in output_dir.glob("*.csv"):
        old_file.unlink()
    for name, frame in datasets.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)


def load_to_postgres(datasets: dict[str, pd.DataFrame], database_url: str) -> None:
    engine = create_engine(database_url)
    table_targets = {
        "raw_customers": ("finance_raw", "raw_customers"),
        "raw_transactions": ("finance_raw", "raw_transactions"),
        "raw_invoices": ("finance_raw", "raw_invoices"),
        "raw_fx_rates": ("finance_raw", "raw_fx_rates"),
        "stg_customers": ("finance_staging", "stg_customers"),
        "stg_transactions": ("finance_staging", "stg_transactions"),
        "stg_invoices": ("finance_staging", "stg_invoices"),
        "dim_customers": ("finance_mart", "dim_customers"),
        "fact_transactions": ("finance_mart", "fact_transactions"),
        "fact_invoices": ("finance_mart", "fact_invoices"),
        "mart_kpis": ("finance_mart", "mart_kpis"),
        "mart_revenue_by_customer": ("finance_mart", "mart_revenue_by_customer"),
        "mart_aging_buckets": ("finance_mart", "mart_aging_buckets"),
        "mart_dso_by_segment": ("finance_mart", "mart_dso_by_segment"),
        "mart_dso_by_country": ("finance_mart", "mart_dso_by_country"),
        "mart_collection_priority": ("finance_mart", "mart_collection_priority"),
        "mart_fx_exposure": ("finance_mart", "mart_fx_exposure"),
        "mart_quality_by_dataset": ("finance_mart", "mart_quality_by_dataset"),
        "mart_quality_impact": ("finance_mart", "mart_quality_impact"),
        "data_quality_results": ("finance_quality", "data_quality_results"),
        "pipeline_runs": ("finance_quality", "pipeline_runs"),
    }

    with engine.begin() as connection:
        for schema in {"finance_raw", "finance_staging", "finance_mart", "finance_quality"}:
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        for view_name in REPORTING_VIEWS:
            connection.execute(text(f"DROP VIEW IF EXISTS finance_mart.{view_name}"))

        for name, frame in datasets.items():
            schema, table_name = table_targets[name]
            frame.to_sql(
                table_name,
                connection,
                schema=schema,
                if_exists="replace",
                index=False,
            )

        views_sql = (PROJECT_ROOT / "sql" / "04_views.sql").read_text(encoding="utf-8")
        for statement in views_sql.split(";"):
            if statement.strip():
                connection.execute(text(statement))
