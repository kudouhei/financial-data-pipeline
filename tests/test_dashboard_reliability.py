import pandas as pd

from dashboard.reliability import pipeline_run_summary, reliability_by_dimension


def test_reliability_by_dimension_calculates_control_pass_rate() -> None:
    quality = pd.DataFrame(
        [
            {
                "check_id": 1,
                "check_name": "completeness.customer_id_not_null",
                "status": "PASS",
                "failed_rows": 0,
                "affected_amount_eur": 0,
            },
            {
                "check_id": 2,
                "check_name": "completeness.amount_not_null",
                "status": "FAIL",
                "failed_rows": 2,
                "affected_amount_eur": 150,
            },
        ]
    )

    result = reliability_by_dimension(quality).iloc[0]

    assert result["dimension"] == "Completeness"
    assert result["controls"] == 2
    assert result["pass_rate"] == 0.5


def test_pipeline_run_summary_aggregates_source_metadata() -> None:
    runs = pd.DataFrame(
        {
            "run_id": ["run-1", "run-1"],
            "dataset": ["customers", "transactions"],
            "row_count": [10, 20],
            "schema_valid": [True, True],
            "started_at": ["2026-01-01T00:00:00Z"] * 2,
            "completed_at": ["2026-01-01T00:00:01Z"] * 2,
            "quality_score": [95.0, 95.0],
        }
    )

    result = pipeline_run_summary(runs).iloc[0]

    assert result["datasets"] == 2
    assert result["input_rows"] == 30
    assert result["duration_ms"] == 1_000
    assert result["status"] == "Completed"
