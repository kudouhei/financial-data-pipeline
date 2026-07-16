import pandas as pd
import pytest

from src.transform import transform_all


def test_transform_all_normalizes_and_enriches_amounts():
    raw = {
        "customers": pd.DataFrame(
            {
                "customer_id": [" c001 ", "C001"],
                "customer_name": ["Acme", "Duplicate"],
                "country": ["DE", "DE"],
                "segment": ["Corporate", "Corporate"],
                "risk_level": ["Low", "Low"],
                "created_at": pd.to_datetime(["2023-01-01", "2023-01-01"]),
                "status": ["Active", "Active"],
            }
        ),
        "transactions": pd.DataFrame(
            {
                "transaction_id": ["T001"],
                "customer_id": ["c001"],
                "transaction_date": pd.to_datetime(["2024-01-01"]),
                "amount": ["100"],
                "currency": ["eur"],
                "transaction_type": ["Payment"],
                "channel": ["Web"],
                "status": ["Completed"],
            }
        ),
        "invoices": pd.DataFrame(
            {
                "invoice_id": ["I001"],
                "customer_id": ["c001"],
                "issue_date": pd.to_datetime(["2024-01-01"]),
                "due_date": pd.to_datetime(["2024-01-31"]),
                "paid_date": pd.to_datetime(["2024-02-05"]),
                "amount": ["100"],
                "status": ["Paid"],
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

    assert len(transformed["customers"]) == 1
    assert transformed["transactions"].loc[0, "amount_eur"] == pytest.approx(110)
    assert transformed["transactions"].loc[0, "has_valid_customer"]
    assert transformed["invoices"].loc[0, "overdue_days"] == 5
