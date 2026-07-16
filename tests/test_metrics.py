import pandas as pd

from src.metrics import build_metric_outputs, render_kpi_markdown
from src.quality_checks import run_quality_checks
from src.transform import transform_all


def test_metrics_build_operational_kpis():
    raw = {
        "customers": pd.DataFrame(
            {
                "customer_id": ["C001", "C002"],
                "customer_name": ["Acme", "Blue River"],
                "country": ["DE", "FR"],
                "segment": ["Corporate", "SME"],
                "risk_level": ["Low", "Medium"],
                "created_at": pd.to_datetime(["2023-01-01", "2023-02-01"]),
                "status": ["active", "active"],
            }
        ),
        "transactions": pd.DataFrame(
            {
                "transaction_id": ["T001", "T002"],
                "customer_id": ["C001", "C002"],
                "transaction_date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                "amount": [100, 200],
                "currency": ["EUR", "GBP"],
                "transaction_type": ["Payment", "Transfer"],
                "channel": ["Web", "API"],
                "status": ["Completed", "Completed"],
            }
        ),
        "invoices": pd.DataFrame(
            {
                "invoice_id": ["I001", "I002"],
                "customer_id": ["C001", "C002"],
                "issue_date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
                "due_date": pd.to_datetime(["2024-01-31", "2024-01-31"]),
                "paid_date": pd.to_datetime(["2024-01-20", None]),
                "amount": [100, 200],
                "status": ["Paid", "Open"],
            }
        ),
        "fx_rates": pd.DataFrame(
            {
                "currency": ["EUR", "GBP"],
                "rate_to_eur": [1.0, 1.2],
                "rate_date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            }
        ),
    }

    transformed = transform_all(raw, as_of_date="2024-02-29")
    quality_issues = run_quality_checks(raw, transformed, run_id="test-run")
    metrics = build_metric_outputs(transformed, quality_issues)
    kpis = metrics["kpis"].set_index("metric")["value"].to_dict()

    assert kpis["active_customers"] == 2
    assert kpis["transaction_count"] == 2
    assert kpis["total_transaction_volume_eur"] == 340
    assert kpis["failed_transaction_rate"] == 0
    assert kpis["overdue_invoice_amount_eur"] == 200
    assert kpis["overdue_invoice_rate"] == 0.5
    assert kpis["fx_exposure_eur"] == 240
    assert kpis["fx_exposure_rate"] == 0.71
    assert kpis["completed_transaction_amount_eur"] == 340
    assert kpis["open_invoice_amount_eur"] == 200
    assert kpis["anomaly_count"] == 0
    assert "collection_priority" in metrics
    assert "fx_exposure" in metrics
    assert "Sample KPI Report" in render_kpi_markdown(metrics)
