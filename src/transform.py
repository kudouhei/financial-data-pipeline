from __future__ import annotations

import pandas as pd


VALID_SEGMENTS = {"retail", "sme", "corporate"}
VALID_RISK_LEVELS = {"low", "medium", "high"}
VALID_CUSTOMER_STATUSES = {"active", "inactive", "unknown"}
VALID_CURRENCIES = {"EUR", "USD", "GBP"}
VALID_TRANSACTION_TYPES = {"payment", "refund", "transfer"}
VALID_CHANNELS = {"web", "branch", "api"}
VALID_TRANSACTION_STATUSES = {"completed", "failed", "pending"}
VALID_INVOICE_STATUSES = {"paid", "overdue", "open"}
LARGE_TRANSACTION_THRESHOLD = 50_000


def _normalize_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    for column in cleaned.select_dtypes(include="object").columns:
        cleaned[column] = cleaned[column].astype("string").str.strip()
    return cleaned


def _upper(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.upper()


def _lower(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def _join_reasons(flags: dict[str, pd.Series]) -> pd.Series:
    reasons = pd.Series("", index=next(iter(flags.values())).index, dtype="string")
    for reason, mask in flags.items():
        reasons = reasons.mask(mask, reasons + reason + "|")
    return reasons.str.rstrip("|")


def transform_customers(customers: pd.DataFrame) -> pd.DataFrame:
    cleaned = _normalize_string_columns(customers)
    cleaned["customer_id"] = _upper(cleaned["customer_id"])
    cleaned["country"] = _upper(cleaned["country"])
    cleaned["status"] = _lower(cleaned["status"]).fillna("unknown")
    cleaned["segment"] = _lower(cleaned["segment"])
    cleaned["risk_level"] = _lower(cleaned["risk_level"])
    cleaned["created_at"] = pd.to_datetime(cleaned["created_at"], errors="coerce")
    cleaned["is_duplicate"] = cleaned.duplicated(subset=["customer_id"], keep="first")
    cleaned = cleaned.drop_duplicates(subset=["customer_id"], keep="first")
    return cleaned


def transform_fx_rates(fx_rates: pd.DataFrame) -> pd.DataFrame:
    cleaned = _normalize_string_columns(fx_rates)
    cleaned["rate_date"] = pd.to_datetime(cleaned["rate_date"], errors="coerce")
    cleaned["currency"] = _upper(cleaned["currency"])
    cleaned["rate_to_eur"] = pd.to_numeric(cleaned["rate_to_eur"], errors="coerce")
    return cleaned.drop_duplicates(subset=["rate_date", "currency"], keep="last")


def transform_transactions(
    transactions: pd.DataFrame,
    customers: pd.DataFrame,
    fx_rates: pd.DataFrame,
) -> pd.DataFrame:
    cleaned = _normalize_string_columns(transactions)
    cleaned["transaction_date"] = pd.to_datetime(cleaned["transaction_date"], errors="coerce")
    cleaned["customer_id"] = _upper(cleaned["customer_id"])
    cleaned["currency"] = _upper(cleaned["currency"])
    cleaned["status"] = _lower(cleaned["status"])
    cleaned["transaction_type"] = _lower(cleaned["transaction_type"])
    cleaned["channel"] = _lower(cleaned["channel"])
    cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce")
    cleaned["is_duplicate"] = cleaned.duplicated(subset=["transaction_id"], keep="first")
    cleaned["has_valid_customer"] = cleaned["customer_id"].isin(customers["customer_id"])

    customer_risk = customers[["customer_id", "risk_level"]].drop_duplicates("customer_id")
    cleaned = cleaned.merge(customer_risk, on="customer_id", how="left")
    fx_lookup = fx_rates.rename(columns={"rate_date": "transaction_date"})
    cleaned = cleaned.merge(
        fx_lookup[["transaction_date", "currency", "rate_to_eur"]],
        on=["transaction_date", "currency"],
        how="left",
    )
    cleaned["amount_eur"] = cleaned["amount"] * cleaned["rate_to_eur"]
    flags = {
        "duplicate_transaction_id": cleaned["is_duplicate"],
        "missing_customer_id": cleaned["customer_id"].isna() | (cleaned["customer_id"] == ""),
        "unknown_customer": ~cleaned["has_valid_customer"],
        "non_positive_amount": cleaned["amount"].isna() | (cleaned["amount"] <= 0),
        "invalid_currency": ~cleaned["currency"].isin(VALID_CURRENCIES),
        "missing_fx_rate": cleaned["rate_to_eur"].isna(),
        "invalid_status": ~cleaned["status"].isin(VALID_TRANSACTION_STATUSES),
        "large_transaction": cleaned["amount"] > LARGE_TRANSACTION_THRESHOLD,
        "high_risk_large_transaction": (cleaned["risk_level"] == "high")
        & (cleaned["amount"] > LARGE_TRANSACTION_THRESHOLD),
    }
    cleaned["anomaly_reasons"] = _join_reasons(flags)
    cleaned["anomaly_flag"] = cleaned["anomaly_reasons"].ne("")
    return cleaned


def transform_invoices(
    invoices: pd.DataFrame,
    customers: pd.DataFrame,
    fx_rates: pd.DataFrame,
    as_of_date: str,
) -> pd.DataFrame:
    cleaned = _normalize_string_columns(invoices)
    cleaned["customer_id"] = _upper(cleaned["customer_id"])
    cleaned["issue_date"] = pd.to_datetime(cleaned["issue_date"], errors="coerce")
    cleaned["due_date"] = pd.to_datetime(cleaned["due_date"], errors="coerce")
    cleaned["paid_date"] = pd.to_datetime(cleaned["paid_date"], errors="coerce")
    cleaned["status"] = _lower(cleaned["status"])
    cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce")
    cleaned["has_valid_customer"] = cleaned["customer_id"].isin(customers["customer_id"])

    as_of = pd.Timestamp(as_of_date)
    paid_or_as_of = cleaned["paid_date"].fillna(as_of)
    cleaned["days_to_pay"] = (paid_or_as_of - cleaned["issue_date"]).dt.days
    cleaned["overdue_days"] = (paid_or_as_of - cleaned["due_date"]).dt.days.clip(lower=0)
    cleaned["is_overdue"] = cleaned["paid_date"].isna() & (cleaned["due_date"] < as_of)
    cleaned["amount_eur"] = cleaned["amount"]
    flags = {
        "unknown_customer": ~cleaned["has_valid_customer"],
        "missing_amount": cleaned["amount"].isna(),
        "non_positive_amount": cleaned["amount"] <= 0,
        "invalid_status": ~cleaned["status"].isin(VALID_INVOICE_STATUSES),
        "due_before_issue": cleaned["due_date"] < cleaned["issue_date"],
        "paid_after_due": cleaned["paid_date"].notna() & (cleaned["paid_date"] > cleaned["due_date"]),
        "overdue_invoice": cleaned["is_overdue"],
    }
    cleaned["anomaly_reasons"] = _join_reasons(flags)
    cleaned["anomaly_flag"] = cleaned["anomaly_reasons"].ne("")
    return cleaned


def transform_all(raw: dict[str, pd.DataFrame], as_of_date: str) -> dict[str, pd.DataFrame]:
    fx_rates = transform_fx_rates(raw["fx_rates"])
    customers = transform_customers(raw["customers"])
    transactions = transform_transactions(raw["transactions"], customers, fx_rates)
    invoices = transform_invoices(raw["invoices"], customers, fx_rates, as_of_date)

    return {
        "customers": customers,
        "transactions": transactions,
        "invoices": invoices,
        "fx_rates": fx_rates,
    }
