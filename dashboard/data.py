from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st


OUTPUT_NAMES = (
    "mart_kpis",
    "data_quality_results",
    "mart_revenue_by_customer",
    "mart_aging_buckets",
    "pipeline_runs",
    "fact_transactions",
    "fact_invoices",
    "dim_customers",
    "mart_quality_impact",
    "mart_dso_by_segment",
    "mart_dso_by_country",
    "mart_collection_priority",
    "mart_fx_exposure",
)


@dataclass(frozen=True)
class DashboardData:
    kpis: dict[str, float]
    quality: pd.DataFrame
    revenue: pd.DataFrame
    aging: pd.DataFrame
    runs: pd.DataFrame
    transactions: pd.DataFrame
    invoices: pd.DataFrame
    quality_impact: pd.DataFrame
    dso_segment: pd.DataFrame
    dso_country: pd.DataFrame
    collection: pd.DataFrame
    fx: pd.DataFrame


def missing_outputs(processed_dir: Path) -> list[str]:
    return [
        f"{name}.csv"
        for name in OUTPUT_NAMES
        if not (processed_dir / f"{name}.csv").exists()
    ]


@st.cache_data
def _read_csv(path: str, modified_at: float) -> pd.DataFrame:
    """Cache by path and modification time so pipeline reruns invalidate data."""
    del modified_at
    return pd.read_csv(path)


def _read(processed_dir: Path, name: str) -> pd.DataFrame:
    path = processed_dir / f"{name}.csv"
    return _read_csv(str(path), path.stat().st_mtime)


def load_dashboard_data(processed_dir: Path) -> DashboardData:
    customers = _read(processed_dir, "dim_customers")
    transactions = _read(processed_dir, "fact_transactions").merge(
        customers[["customer_id", "country", "segment", "customer_name"]],
        on="customer_id",
        how="left",
    )
    invoices = _read(processed_dir, "fact_invoices").merge(
        customers[
            ["customer_id", "country", "segment", "customer_name", "risk_level"]
        ],
        on="customer_id",
        how="left",
        suffixes=("", "_customer"),
    )
    kpis = (
        _read(processed_dir, "mart_kpis")
        .set_index("metric")["value"]
        .astype(float)
        .to_dict()
    )

    return DashboardData(
        kpis=kpis,
        quality=_read(processed_dir, "data_quality_results"),
        revenue=_read(processed_dir, "mart_revenue_by_customer"),
        aging=_read(processed_dir, "mart_aging_buckets"),
        runs=_read(processed_dir, "pipeline_runs"),
        transactions=transactions,
        invoices=invoices,
        quality_impact=_read(processed_dir, "mart_quality_impact"),
        dso_segment=_read(processed_dir, "mart_dso_by_segment"),
        dso_country=_read(processed_dir, "mart_dso_by_country"),
        collection=_read(processed_dir, "mart_collection_priority"),
        fx=_read(processed_dir, "mart_fx_exposure"),
    )
