from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd


CHECK_CONTEXT = {
    "completeness": ("Reporting", "Data Engineering"),
    "uniqueness": ("Reporting", "Finance Ops"),
    "validity": ("Compliance", "Data Engineering"),
    "consistency": ("Revenue", "Finance Ops"),
}
CHECK_OVERRIDES = {
    "completeness.transaction_customer_id_not_null": ("Revenue", "Finance Ops"),
    "completeness.transaction_amount_not_null": ("Revenue", "Finance Ops"),
    "validity.transaction_amount_positive": ("Revenue", "Finance Ops"),
    "validity.currency_allowed": ("Reporting", "Data Engineering"),
    "validity.transaction_status_allowed": ("Compliance", "Finance Ops"),
    "validity.invoice_status_allowed": ("Cash Flow", "AR Team"),
    "consistency.transaction_customer_exists": ("Revenue", "Finance Ops"),
    "consistency.invoice_customer_exists": ("Cash Flow", "AR Team"),
    "consistency.invoice_due_date_after_issue_date": ("Cash Flow", "AR Team"),
    "consistency.invoice_paid_date_after_issue_date": ("Cash Flow", "AR Team"),
    "consistency.fx_rate_exists": ("Reporting", "Data Engineering"),
}


def _is_missing(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype("string").str.strip().isin(["", "<NA>", "nan"])


def _status(severity: str, failed_rows: int) -> str:
    if failed_rows == 0:
        return "PASS"
    if severity in {"critical", "high"}:
        return "FAIL"
    return "WARNING"


def _result(
    check_name: str,
    table_name: str,
    severity: str,
    total_rows: int,
    failed_rows: int,
    affected_amount_eur: float = 0.0,
) -> dict[str, object]:
    failed_rows = int(failed_rows)
    total_rows = int(total_rows)
    failed_rate = round(failed_rows / total_rows, 4) if total_rows else 0.0
    category = check_name.split(".", maxsplit=1)[0]
    business_impact, owner = CHECK_OVERRIDES.get(
        check_name,
        CHECK_CONTEXT.get(category, ("Reporting", "Data Engineering")),
    )
    return {
        "check_name": check_name,
        "table_name": table_name,
        "severity": severity,
        "total_rows": total_rows,
        "failed_rows": failed_rows,
        "failed_rate": failed_rate,
        "status": _status(severity, failed_rows),
        "business_impact": business_impact,
        "owner": owner,
        "affected_amount_eur": round(float(affected_amount_eur), 2),
    }


def _amount_at_risk(frame: pd.DataFrame, mask: pd.Series, amount_column: str = "amount_eur") -> float:
    if amount_column not in frame.columns:
        amount_column = "amount"
    return frame.loc[mask, amount_column].fillna(frame.loc[mask, "amount"]).abs().sum()


def check_completeness(
    raw: dict[str, pd.DataFrame],
    transformed: dict[str, pd.DataFrame],
) -> list[dict[str, object]]:
    customers = raw["customers"]
    transactions = raw["transactions"]
    invoices = raw["invoices"]
    missing_transaction_customer = _is_missing(transactions["customer_id"])
    missing_transaction_amount = _is_missing(transactions["amount"])
    missing_invoice_customer = _is_missing(invoices["customer_id"])
    missing_invoice_due_date = _is_missing(invoices["due_date"])

    return [
        _result(
            "completeness.customer_id_not_null",
            "raw_customers",
            "high",
            len(customers),
            _is_missing(customers["customer_id"]).sum(),
        ),
        _result(
            "completeness.transaction_customer_id_not_null",
            "raw_transactions",
            "high",
            len(transactions),
            missing_transaction_customer.sum(),
            _amount_at_risk(transactions, missing_transaction_customer, "amount"),
        ),
        _result(
            "completeness.transaction_id_not_null",
            "raw_transactions",
            "critical",
            len(transactions),
            _is_missing(transactions["transaction_id"]).sum(),
        ),
        _result(
            "completeness.transaction_amount_not_null",
            "raw_transactions",
            "high",
            len(transactions),
            missing_transaction_amount.sum(),
            0.0,
        ),
        _result(
            "completeness.invoice_id_not_null",
            "raw_invoices",
            "critical",
            len(invoices),
            _is_missing(invoices["invoice_id"]).sum(),
        ),
        _result(
            "completeness.invoice_customer_id_not_null",
            "raw_invoices",
            "high",
            len(invoices),
            missing_invoice_customer.sum(),
            _amount_at_risk(invoices, missing_invoice_customer, "amount"),
        ),
        _result(
            "completeness.invoice_due_date_not_null",
            "raw_invoices",
            "high",
            len(invoices),
            missing_invoice_due_date.sum(),
            _amount_at_risk(invoices, missing_invoice_due_date, "amount"),
        ),
    ]


def check_uniqueness(raw: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    customers = raw["customers"]
    transactions = raw["transactions"]
    invoices = raw["invoices"]
    duplicate_customers = customers.duplicated(subset=["customer_id"], keep=False)
    duplicate_transactions = transactions.duplicated(subset=["transaction_id"], keep=False)
    duplicate_invoices = invoices.duplicated(subset=["invoice_id"], keep=False)

    return [
        _result(
            "uniqueness.customer_id_unique",
            "raw_customers",
            "high",
            len(customers),
            duplicate_customers.sum(),
        ),
        _result(
            "uniqueness.transaction_id_unique",
            "raw_transactions",
            "high",
            len(transactions),
            duplicate_transactions.sum(),
            _amount_at_risk(transactions, duplicate_transactions, "amount"),
        ),
        _result(
            "uniqueness.invoice_id_unique",
            "raw_invoices",
            "high",
            len(invoices),
            duplicate_invoices.sum(),
            _amount_at_risk(invoices, duplicate_invoices, "amount"),
        ),
    ]


def check_validity(transformed: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    customers = transformed["customers"]
    transactions = transformed["transactions"]
    invoices = transformed["invoices"]
    now = pd.Timestamp.now(tz=None).normalize()
    invalid_transaction_amount = transactions["amount"].isna() | (transactions["amount"] <= 0)
    invalid_invoice_amount = invoices["amount"].isna() | (invoices["amount"] <= 0)
    invalid_currency = ~transactions["currency"].isin(["EUR", "USD", "GBP"])
    invalid_transaction_status = ~transactions["status"].isin(["completed", "failed", "pending"])
    invalid_invoice_status = ~invoices["status"].isin(["paid", "overdue", "open"])
    future_transaction_date = transactions["transaction_date"] > now

    return [
        _result(
            "validity.transaction_amount_positive",
            "stg_transactions",
            "high",
            len(transactions),
            invalid_transaction_amount.sum(),
            _amount_at_risk(transactions, invalid_transaction_amount),
        ),
        _result(
            "validity.invoice_amount_positive",
            "stg_invoices",
            "high",
            len(invoices),
            invalid_invoice_amount.sum(),
            _amount_at_risk(invoices, invalid_invoice_amount),
        ),
        _result(
            "validity.currency_allowed",
            "stg_transactions",
            "high",
            len(transactions),
            invalid_currency.sum(),
            _amount_at_risk(transactions, invalid_currency),
        ),
        _result(
            "validity.customer_status_allowed",
            "stg_customers",
            "medium",
            len(customers),
            (~customers["status"].isin(["active", "inactive", "unknown"])).sum(),
        ),
        _result(
            "validity.transaction_status_allowed",
            "stg_transactions",
            "medium",
            len(transactions),
            invalid_transaction_status.sum(),
            _amount_at_risk(transactions, invalid_transaction_status),
        ),
        _result(
            "validity.invoice_status_allowed",
            "stg_invoices",
            "medium",
            len(invoices),
            invalid_invoice_status.sum(),
            _amount_at_risk(invoices, invalid_invoice_status),
        ),
        _result(
            "validity.risk_level_allowed",
            "stg_customers",
            "medium",
            len(customers),
            (~customers["risk_level"].isin(["low", "medium", "high"])).sum(),
        ),
        _result(
            "validity.transaction_date_not_future",
            "stg_transactions",
            "medium",
            len(transactions),
            future_transaction_date.sum(),
            _amount_at_risk(transactions, future_transaction_date),
        ),
    ]


def check_consistency(transformed: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    transactions = transformed["transactions"]
    invoices = transformed["invoices"]
    unknown_transaction_customer = ~transactions["has_valid_customer"]
    unknown_invoice_customer = ~invoices["has_valid_customer"]
    due_before_issue = invoices["due_date"] < invoices["issue_date"]
    paid_before_issue = invoices["paid_date"].notna() & (invoices["paid_date"] < invoices["issue_date"])
    missing_fx_rate = transactions["rate_to_eur"].isna()

    return [
        _result(
            "consistency.transaction_customer_exists",
            "stg_transactions",
            "high",
            len(transactions),
            unknown_transaction_customer.sum(),
            _amount_at_risk(transactions, unknown_transaction_customer),
        ),
        _result(
            "consistency.invoice_customer_exists",
            "stg_invoices",
            "high",
            len(invoices),
            unknown_invoice_customer.sum(),
            _amount_at_risk(invoices, unknown_invoice_customer),
        ),
        _result(
            "consistency.invoice_due_date_after_issue_date",
            "stg_invoices",
            "high",
            len(invoices),
            due_before_issue.sum(),
            _amount_at_risk(invoices, due_before_issue),
        ),
        _result(
            "consistency.invoice_paid_date_after_issue_date",
            "stg_invoices",
            "medium",
            len(invoices),
            paid_before_issue.sum(),
            _amount_at_risk(invoices, paid_before_issue),
        ),
        _result(
            "consistency.fx_rate_exists",
            "stg_transactions",
            "high",
            len(transactions),
            missing_fx_rate.sum(),
            _amount_at_risk(transactions, missing_fx_rate),
        ),
    ]


def run_quality_checks(
    raw: dict[str, pd.DataFrame],
    transformed: dict[str, pd.DataFrame],
    run_id: str,
    extract_metadata: pd.DataFrame | None = None,
) -> pd.DataFrame:
    checks = [
        *check_completeness(raw, transformed),
        *check_uniqueness(raw),
        *check_validity(transformed),
        *check_consistency(transformed),
    ]
    if extract_metadata is not None and not extract_metadata.empty:
        checks.extend(
            _result(
                "validity.schema_matches_expected_columns",
                f"raw_{row.dataset}",
                "critical",
                row.row_count,
                0 if row.schema_valid else row.row_count,
            )
            for row in extract_metadata.itertuples(index=False)
        )

    created_at = datetime.now(UTC).isoformat()
    results = pd.DataFrame(checks)
    results.insert(0, "run_id", run_id)
    results.insert(0, "check_id", range(1, len(results) + 1))
    results["created_at"] = created_at
    return results


def quality_score(results: pd.DataFrame) -> float:
    if results.empty:
        return 100.0

    check_penalties = {"critical": 10.0, "high": 5.0, "medium": 2.0, "low": 1.0}
    rate_multipliers = {"critical": 25.0, "high": 15.0, "medium": 8.0, "low": 4.0}
    penalty = sum(
        (
            check_penalties.get(row.severity, 1.0)
            + rate_multipliers.get(row.severity, 4.0) * row.failed_rate
        )
        for row in results.itertuples(index=False)
        if row.failed_rows > 0
    )
    return max(0.0, round(100.0 - penalty, 2))
