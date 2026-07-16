from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.charts import AMBER, RED, horizontal_bar, quality_trend
from dashboard.data import load_dashboard_data, missing_outputs
from dashboard.reliability import (
    add_quality_dimensions,
    pipeline_run_summary,
    reliability_by_dataset,
    reliability_by_dimension,
)
from dashboard.ui import (
    apply_theme,
    footer,
    format_eur,
    pipeline_lineage,
    priority_note,
    section,
)


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OPEN_STATUSES = ("FAIL", "WARNING")
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

st.set_page_config(
    page_title="Financial Data Reliability",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()

missing = missing_outputs(PROCESSED_DIR)
if missing:
    st.warning(
        "Dashboard data is not ready. Run `python generate_data.py` and "
        "`python -m src.pipeline`."
    )
    st.caption("Missing: " + ", ".join(missing))
    st.stop()

data = load_dashboard_data(PROCESSED_DIR)
kpis = data.kpis
quality = add_quality_dimensions(data.quality)
open_issues = quality[quality["status"].isin(OPEN_STATUSES)].copy()
run_history = pipeline_run_summary(data.runs)
latest_run = run_history.iloc[0]

st.markdown('<div class="eyebrow">Data reliability engineering</div>', unsafe_allow_html=True)
st.title("Financial Data Reliability Console")
st.markdown(
    '<p class="lede">Operational evidence that financial data is complete, '
    "consistent and traceable before it reaches reporting.</p>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="question"><small>Reliability question</small>'
    '<strong>Can this pipeline run be trusted, and can every failure be traced '
    "to a dataset, control and owner?</strong></div>",
    unsafe_allow_html=True,
)

overview_tab, controls_tab, runs_tab, impact_tab = st.tabs(
    ["Reliability overview", "Quality controls", "Pipeline runs", "Business impact"]
)

with overview_tab:
    metrics = st.columns(4)
    metrics[0].metric("Reliability score", f"{kpis['data_quality_score']:.1f} / 100")
    metrics[1].metric("Controls passing", f"{(quality['status'] == 'PASS').sum()} / {len(quality)}")
    metrics[2].metric("Schemas valid", f"{int(latest_run['schema_passed'])} / 1")
    metrics[3].metric("Latest run", latest_run["status"], f"{latest_run['duration_ms']:.0f} ms")

    section(
        "Processing path",
        "Each run records its source metadata, validation results and published outputs.",
    )
    pipeline_lineage()

    dimension_summary = reliability_by_dimension(quality)
    dataset_summary = reliability_by_dataset(quality)
    left, right = st.columns([1, 1.25])
    with left:
        section(
            "Reliability dimensions",
            "Pass rate across the four control families.",
        )
        st.dataframe(
            dimension_summary,
            width="stretch",
            hide_index=True,
            column_config={
                "dimension": "Dimension",
                "controls": "Controls",
                "passing": "Passing",
                "failed_rows": "Failed rows",
                "affected_amount_eur": st.column_config.NumberColumn(
                    "EUR affected", format="€ %.0f"
                ),
                "pass_rate": st.column_config.ProgressColumn(
                    "Pass rate", format="%.0f%%", min_value=0, max_value=1
                ),
            },
        )
    with right:
        section(
            "Dataset health",
            "Controls are tied to the dataset where the issue was detected.",
        )
        st.dataframe(
            dataset_summary,
            width="stretch",
            hide_index=True,
            column_config={
                "table_name": "Dataset",
                "controls": "Controls",
                "failed_controls": "Open controls",
                "failed_rows": "Failed rows",
                "affected_amount_eur": st.column_config.NumberColumn(
                    "EUR affected", format="€ %.0f"
                ),
                "status": "Health",
            },
        )

with controls_tab:
    section(
        "Control results",
        "Filter failures by reliability dimension, owner and execution status.",
    )
    filter_columns = st.columns(3)
    dimensions = sorted(quality["dimension"].dropna().unique())
    owners = sorted(quality["owner"].dropna().unique())
    selected_dimensions = filter_columns[0].multiselect(
        "Dimension", dimensions, default=dimensions
    )
    selected_owners = filter_columns[1].multiselect("Owner", owners, default=owners)
    selected_statuses = filter_columns[2].multiselect(
        "Status", ["FAIL", "WARNING", "PASS"], default=list(OPEN_STATUSES)
    )
    filtered = quality[
        quality["dimension"].isin(selected_dimensions)
        & quality["owner"].isin(selected_owners)
        & quality["status"].isin(selected_statuses)
    ].copy()
    filtered["severity_order"] = filtered["severity"].map(SEVERITY_ORDER).fillna(9)
    filtered = filtered.sort_values(
        ["severity_order", "affected_amount_eur"], ascending=[True, False]
    )

    counters = st.columns(3)
    counters[0].metric("Matching controls", len(filtered))
    counters[1].metric("Failed rows", f"{filtered['failed_rows'].sum():,.0f}")
    counters[2].metric("Affected value", format_eur(filtered["affected_amount_eur"].sum()))
    control_columns = [
        "status", "severity", "dimension", "check_name", "table_name", "owner",
        "failed_rows", "failed_rate", "affected_amount_eur",
    ]
    st.dataframe(
        filtered[control_columns],
        width="stretch",
        hide_index=True,
        column_config={
            "status": "Status",
            "severity": "Severity",
            "dimension": "Dimension",
            "check_name": "Control",
            "table_name": "Dataset",
            "owner": "Owner",
            "failed_rows": "Failed rows",
            "failed_rate": st.column_config.ProgressColumn(
                "Failure rate", format="%.1f%%", min_value=0, max_value=1
            ),
            "affected_amount_eur": st.column_config.NumberColumn(
                "EUR affected", format="€ %.0f"
            ),
        },
    )

with runs_tab:
    section(
        "Run history",
        "Run IDs, timestamps, duration, row counts and schema results provide an audit trail.",
    )
    st.dataframe(
        run_history,
        width="stretch",
        hide_index=True,
        column_config={
            "run_id": "Run ID",
            "started_at": st.column_config.DatetimeColumn("Started", format="YYYY-MM-DD HH:mm:ss"),
            "completed_at": st.column_config.DatetimeColumn("Completed", format="YYYY-MM-DD HH:mm:ss"),
            "duration_ms": st.column_config.NumberColumn("Duration", format="%.0f ms"),
            "datasets": "Datasets",
            "input_rows": "Input rows",
            "schema_passed": "Schema valid",
            "quality_score": st.column_config.NumberColumn("Quality score", format="%.1f"),
            "status": "Status",
        },
    )

    section(
        "Quality trend",
        "Scores are recorded per run so regressions are visible rather than overwritten.",
    )
    trend = run_history.sort_values("completed_at").tail(20)
    st.altair_chart(quality_trend(trend), width="stretch")

    section(
        "Latest source snapshot",
        "Source-level metadata captured before transformation.",
    )
    latest_details = data.runs[data.runs["run_id"] == latest_run["run_id"]]
    st.dataframe(
        latest_details[["dataset", "source_file", "row_count", "schema_valid", "schema_errors"]],
        width="stretch",
        hide_index=True,
        column_config={
            "dataset": "Dataset",
            "source_file": "Source",
            "row_count": "Rows",
            "schema_valid": "Schema valid",
            "schema_errors": "Schema errors",
        },
    )

with impact_tab:
    impact = kpis.get("data_quality_impact_eur", 0.0)
    volume = kpis.get("total_transaction_volume_eur", 0.0)
    impact_metrics = st.columns(4)
    impact_metrics[0].metric("Affected value", format_eur(impact), f"{impact / volume:.2%} of volume" if volume else None)
    impact_metrics[1].metric("Revenue at risk", format_eur(kpis.get("revenue_at_risk_eur", 0)))
    impact_metrics[2].metric("Receivables at risk", format_eur(kpis.get("ar_at_risk_eur", 0)))
    impact_metrics[3].metric("Anomaly records", f"{kpis.get('anomaly_count', 0):,.0f}")

    material = open_issues.sort_values("affected_amount_eur", ascending=False)
    if not material.empty:
        top_issue = material.iloc[0]
        priority_note(
            top_issue["check_name"],
            top_issue["affected_amount_eur"],
            top_issue["owner"],
        )

    section(
        "Material control failures",
        "Technical failures are ranked by financial consequence, not only record count.",
    )
    left, right = st.columns([1.35, 1])
    with left:
        issue_amounts = material.head(8)[["check_name", "affected_amount_eur"]]
        st.altair_chart(
            horizontal_bar(
                issue_amounts,
                "check_name",
                "affected_amount_eur",
                color=RED,
                height=320,
            ),
            width="stretch",
        )
    with right:
        impact_by_area = (
            data.quality_impact.groupby("business_impact", as_index=False)
            .agg(affected_amount_eur=("affected_amount_eur", "sum"))
            .sort_values("affected_amount_eur", ascending=False)
        )
        st.altair_chart(
            horizontal_bar(
                impact_by_area,
                "business_impact",
                "affected_amount_eur",
                color=AMBER,
                height=320,
            ),
            width="stretch",
        )

    section(
        "Records requiring investigation",
        "The dashboard keeps row-level evidence available for operational follow-up.",
    )
    anomalies = data.transactions[data.transactions["anomaly_flag"]].sort_values(
        "amount_eur", ascending=False
    )
    st.dataframe(
        anomalies[
            ["transaction_id", "customer_name", "currency", "amount_eur", "status"]
        ],
        width="stretch",
        hide_index=True,
        column_config={
            "transaction_id": "Transaction",
            "customer_name": "Customer",
            "currency": "Currency",
            "amount_eur": st.column_config.NumberColumn("Amount", format="€ %.0f"),
            "status": "Status",
        },
    )
    with st.expander("Collection priority derived from trusted invoice data"):
        st.dataframe(data.collection.head(25), width="stretch", hide_index=True)

footer()
