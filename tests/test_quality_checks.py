import pandas as pd

from src.quality_checks import quality_score, run_quality_checks
from src.transform import transform_all


def test_quality_checks_detect_common_finance_data_issues():
    raw = {
        "customers": pd.DataFrame(
            {
                "customer_id": ["C001", "C001"],
                "customer_name": ["Acme", None],
                "country": ["DE", "DE"],
                "segment": ["Corporate", "Corporate"],
                "risk_level": ["Low", "Low"],
                "created_at": pd.to_datetime(["2023-01-01", "2023-01-01"]),
                "status": ["active", "active"],
            }
        ),
        "transactions": pd.DataFrame(
            {
                "transaction_id": ["T001", "T001", "T002"],
                "customer_id": ["C001", "C001", "C999"],
                "transaction_date": pd.to_datetime(["2024-01-01"] * 3),
                "amount": [100, 100, -10],
                "currency": ["EUR", "EUR", "EUR"],
                "transaction_type": ["Payment", "Payment", "Refund"],
                "channel": ["Web", "Web", "API"],
                "status": ["Completed", "Completed", "Completed"],
            }
        ),
        "invoices": pd.DataFrame(
            {
                "invoice_id": ["I001"],
                "customer_id": ["C999"],
                "issue_date": pd.to_datetime(["2023-12-01"]),
                "due_date": pd.to_datetime(["2023-12-31"]),
                "paid_date": pd.to_datetime([None]),
                "amount": [100],
                "status": ["Open"],
            }
        ),
        "fx_rates": pd.DataFrame(
            {
                "currency": ["EUR"],
                "rate_to_eur": [1.1],
                "rate_date": pd.to_datetime(["2024-01-01"]),
            }
        ),
    }

    transformed = transform_all(raw, as_of_date="2024-02-29")
    issues = run_quality_checks(raw, transformed, run_id="test-run")
    issue_counts = issues.set_index("check_name")["failed_rows"].to_dict()

    assert issue_counts["uniqueness.customer_id_unique"] == 2
    assert issue_counts["uniqueness.transaction_id_unique"] == 2
    assert issue_counts["validity.transaction_amount_positive"] == 1
    assert issue_counts["consistency.transaction_customer_exists"] >= 1
    assert set(issues["status"]).issubset({"PASS", "WARNING", "FAIL"})
    assert quality_score(issues) < 100
