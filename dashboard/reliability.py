from __future__ import annotations

import pandas as pd


DIMENSION_LABELS = {
    "completeness": "Completeness",
    "uniqueness": "Uniqueness",
    "validity": "Validity",
    "consistency": "Consistency",
}


def add_quality_dimensions(quality: pd.DataFrame) -> pd.DataFrame:
    result = quality.copy()
    result["dimension"] = (
        result["check_name"].str.split(".", n=1).str[0].map(DIMENSION_LABELS)
    )
    return result


def reliability_by_dimension(quality: pd.DataFrame) -> pd.DataFrame:
    controls = add_quality_dimensions(quality)
    summary = controls.groupby("dimension", as_index=False).agg(
        controls=("check_id", "count"),
        passing=("status", lambda values: (values == "PASS").sum()),
        failed_rows=("failed_rows", "sum"),
        affected_amount_eur=("affected_amount_eur", "sum"),
    )
    summary["pass_rate"] = summary["passing"] / summary["controls"]
    return summary.sort_values("pass_rate")


def reliability_by_dataset(quality: pd.DataFrame) -> pd.DataFrame:
    summary = quality.groupby("table_name", as_index=False).agg(
        controls=("check_id", "count"),
        failed_controls=("status", lambda values: (values != "PASS").sum()),
        failed_rows=("failed_rows", "sum"),
        affected_amount_eur=("affected_amount_eur", "sum"),
    )
    summary["status"] = summary["failed_controls"].map(
        lambda count: "Healthy" if count == 0 else "Attention"
    )
    return summary.sort_values(
        ["failed_controls", "affected_amount_eur"], ascending=False
    )


def pipeline_run_summary(runs: pd.DataFrame) -> pd.DataFrame:
    frame = runs.copy()
    frame["started_at"] = pd.to_datetime(frame["started_at"], utc=True)
    frame["completed_at"] = pd.to_datetime(frame["completed_at"], utc=True)
    frame["duration_ms"] = (
        (frame["completed_at"] - frame["started_at"]).dt.total_seconds() * 1_000
    )
    summary = frame.groupby("run_id", as_index=False).agg(
        started_at=("started_at", "first"),
        completed_at=("completed_at", "first"),
        duration_ms=("duration_ms", "first"),
        datasets=("dataset", "nunique"),
        input_rows=("row_count", "sum"),
        schema_passed=("schema_valid", "all"),
        quality_score=("quality_score", "first"),
    )
    summary["status"] = summary["schema_passed"].map(
        {True: "Completed", False: "Schema failure"}
    )
    return summary.sort_values("completed_at", ascending=False)
