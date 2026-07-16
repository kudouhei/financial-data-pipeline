from __future__ import annotations

from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = {
    "customers": [
        "customer_id",
        "customer_name",
        "country",
        "segment",
        "risk_level",
        "created_at",
        "status",
    ],
    "transactions": [
        "transaction_id",
        "customer_id",
        "transaction_date",
        "amount",
        "currency",
        "transaction_type",
        "channel",
        "status",
    ],
    "invoices": [
        "invoice_id",
        "customer_id",
        "issue_date",
        "due_date",
        "paid_date",
        "amount",
        "status",
    ],
    "fx_rates": ["rate_date", "currency", "rate_to_eur"],
}

DATE_COLUMNS = {
    "customers": ["created_at"],
    "transactions": ["transaction_date"],
    "invoices": ["issue_date", "due_date", "paid_date"],
    "fx_rates": ["rate_date"],
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = df.copy()
    renamed.columns = [
        str(column).strip().lower().replace(" ", "_") for column in renamed.columns
    ]
    return renamed


def validate_schema(df: pd.DataFrame, dataset_name: str) -> list[str]:
    expected = EXPECTED_COLUMNS[dataset_name]
    missing = sorted(set(expected) - set(df.columns))
    extra = sorted(set(df.columns) - set(expected))
    errors = []
    if missing:
        errors.append(f"missing columns: {', '.join(missing)}")
    if extra:
        errors.append(f"unexpected columns: {', '.join(extra)}")
    return errors


def read_csv_dataset(raw_data_dir: Path, dataset_name: str) -> pd.DataFrame:
    """Read a raw CSV dataset with normalized columns and parsed dates."""

    file_path = raw_data_dir / f"{dataset_name}.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Missing raw dataset: {file_path}")

    df = _normalize_columns(pd.read_csv(file_path))
    for column in DATE_COLUMNS.get(dataset_name, []):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def build_extract_metadata(
    raw_data_dir: Path,
    datasets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows = []
    for name, frame in datasets.items():
        schema_errors = validate_schema(frame, name)
        rows.append(
            {
                "dataset": name,
                "source_file": str(raw_data_dir / f"{name}.csv"),
                "row_count": len(frame),
                "schema_valid": not schema_errors,
                "schema_errors": "; ".join(schema_errors),
            }
        )
    return pd.DataFrame(rows)


def extract_all(raw_data_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        "customers": read_csv_dataset(raw_data_dir, "customers"),
        "transactions": read_csv_dataset(raw_data_dir, "transactions"),
        "invoices": read_csv_dataset(raw_data_dir, "invoices"),
        "fx_rates": read_csv_dataset(raw_data_dir, "fx_rates"),
    }


def extract_with_metadata(raw_data_dir: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    datasets = extract_all(raw_data_dir)
    return datasets, build_extract_metadata(raw_data_dir, datasets)
