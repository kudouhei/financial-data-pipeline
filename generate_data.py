from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

COUNTRIES = ["DE", "FR", "NL", "ES", "IT", "BE", "SE", "DK"]
SEGMENTS = ["Retail", "SME", "Corporate"]
RISK_LEVELS = ["Low", "Medium", "High"]
STATUSES = ["Active", "Inactive"]
TRANSACTION_TYPES = ["Payment", "Refund", "Transfer"]
CHANNELS = ["Web", "Branch", "API"]
TRANSACTION_STATUSES = ["Completed", "Failed", "Pending"]
INVOICE_STATUSES = ["Paid", "Open", "Overdue"]
VALID_CURRENCIES = ["EUR", "USD", "GBP"]
FX_RATES_TO_EUR = {"EUR": 1.0, "USD": 0.92, "GBP": 1.17}
SEGMENT_AMOUNT_PROFILE = {
    "Retail": (7.2, 0.65),
    "SME": (8.1, 0.75),
    "Corporate": (9.0, 0.85),
}
RISK_STATUS_WEIGHTS = {
    "Low": [0.88, 0.04, 0.08],
    "Medium": [0.82, 0.08, 0.10],
    "High": [0.70, 0.18, 0.12],
}


def _random_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def _business_activity_date(start: date, end: date) -> date:
    # Finance activity is often heavier around month start and month end.
    if random.random() < 0.35:
        month = random.choice([1, 2, 3])
        day = random.choice([1, 2, 3, 28, 29, 30])
        try:
            candidate = date(2024, month, day)
        except ValueError:
            candidate = date(2024, month, 28)
        return min(max(candidate, start), end)
    return _random_date(start, end)


def generate_customers(customer_count: int) -> pd.DataFrame:
    rows = []
    for idx in range(1, customer_count + 1):
        risk = random.choices(RISK_LEVELS, weights=[0.55, 0.30, 0.15], k=1)[0]
        rows.append(
            {
                "customer_id": f"C{idx:05d}",
                "customer_name": f"Customer {idx:05d}",
                "country": random.choice(COUNTRIES),
                "segment": random.choice(SEGMENTS),
                "risk_level": risk,
                "created_at": _random_date(date(2021, 1, 1), date(2024, 1, 31)),
                "status": random.choice(STATUSES),
            }
        )

    customers = pd.DataFrame(rows)
    duplicate_rows = customers.sample(n=max(3, customer_count // 100), random_state=7)
    return pd.concat([customers, duplicate_rows], ignore_index=True)


def generate_transactions(customers: pd.DataFrame, transaction_count: int) -> pd.DataFrame:
    customer_master = customers.drop_duplicates("customer_id").set_index("customer_id")
    customer_ids = customer_master.index.tolist()
    high_risk_ids = customers.loc[
        customers["risk_level"] == "High", "customer_id"
    ].drop_duplicates().tolist()

    rows = []
    for idx in range(1, transaction_count + 1):
        transaction_id = f"T{idx:07d}"
        customer_id = random.choice(customer_ids)
        customer = customer_master.loc[customer_id]
        segment = customer["segment"]
        risk_level = customer["risk_level"]
        mean, sigma = SEGMENT_AMOUNT_PROFILE[segment]
        amount = round(random.lognormvariate(mean, sigma), 2)
        currency = random.choice(VALID_CURRENCIES)
        channel = random.choices(CHANNELS, weights=[0.45, 0.20, 0.35], k=1)[0]
        status = random.choices(
            TRANSACTION_STATUSES,
            weights=RISK_STATUS_WEIGHTS[risk_level],
            k=1,
        )[0]

        if idx % 211 == 0:
            transaction_id = f"T{idx - 1:07d}"
        if idx % 257 == 0:
            customer_id = ""
        if idx % 313 == 0:
            amount = -abs(amount)
        if idx % 337 == 0:
            currency = "ABC"
        if idx % 389 == 0:
            customer_id = f"CX{idx:05d}"
        if idx % 431 == 0:
            status = "Reversed"
        if channel == "API" and idx % 149 == 0:
            status = "Reversed"
        if idx % 467 == 0:
            amount = round(random.uniform(50_001, 125_000), 2)
        if idx % 503 == 0 and high_risk_ids:
            customer_id = random.choice(high_risk_ids)
            amount = round(random.uniform(60_000, 180_000), 2)
        if idx % 547 == 0:
            currency = "JPY"

        rows.append(
            {
                "transaction_id": transaction_id,
                "customer_id": customer_id,
                "transaction_date": _business_activity_date(date(2024, 1, 1), date(2024, 3, 31)),
                "amount": amount,
                "currency": currency,
                "transaction_type": random.choice(TRANSACTION_TYPES),
                "channel": channel,
                "status": status,
            }
        )

    return pd.DataFrame(rows)


def generate_invoices(customers: pd.DataFrame, invoice_count: int) -> pd.DataFrame:
    customer_master = customers.drop_duplicates("customer_id").set_index("customer_id")
    customer_ids = customer_master.index.tolist()
    rows = []
    for idx in range(1, invoice_count + 1):
        customer_id = random.choice(customer_ids)
        customer = customer_master.loc[customer_id]
        risk_level = customer["risk_level"]
        segment = customer["segment"]
        mean, sigma = SEGMENT_AMOUNT_PROFILE[segment]
        issue_date = _business_activity_date(date(2024, 1, 1), date(2024, 3, 31))
        due_date = issue_date + timedelta(days=random.choice([14, 30, 45, 60]))
        paid_date = None
        status_weights = {
            "Low": [0.68, 0.24, 0.08],
            "Medium": [0.56, 0.29, 0.15],
            "High": [0.42, 0.33, 0.25],
        }[risk_level]
        status = random.choices(INVOICE_STATUSES, weights=status_weights, k=1)[0]
        if status == "Paid":
            delay_ceiling = 45 if risk_level == "Low" else 90
            paid_date = issue_date + timedelta(days=random.randint(3, delay_ceiling))

        if idx % 173 == 0:
            due_date = issue_date - timedelta(days=random.randint(1, 10))
        if idx % 197 == 0:
            paid_date = due_date + timedelta(days=random.randint(1, 45))
            status = "Paid"
        if idx % 229 == 0:
            status = "Cancelled"

        rows.append(
            {
                "invoice_id": f"I{idx:07d}",
                "customer_id": customer_id,
                "issue_date": issue_date,
                "due_date": due_date,
                "paid_date": paid_date,
                "amount": round(random.lognormvariate(mean, sigma), 2),
                "status": status,
            }
        )

    return pd.DataFrame(rows)


def generate_fx_rates() -> pd.DataFrame:
    start = date(2024, 1, 1)
    rows = []
    for offset in range(0, 91):
        rate_date = start + timedelta(days=offset)
        for currency, rate in FX_RATES_TO_EUR.items():
            # Simulate market-data feed gaps clustered around reporting dates.
            if currency == "GBP" and rate_date.day in {15, 30}:
                continue
            if currency == "USD" and rate_date.day == 31:
                continue
            rows.append(
                {
                    "rate_date": rate_date,
                    "currency": currency,
                    "rate_to_eur": round(rate * random.uniform(0.985, 1.015), 6),
                }
            )
    return pd.DataFrame(rows)


def generate_all(
    customer_count: int = 800,
    transaction_count: int = 6_000,
    invoice_count: int = 3_000,
    seed: int = 42,
) -> None:
    random.seed(seed)
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    customers = generate_customers(customer_count)
    transactions = generate_transactions(customers, transaction_count)
    invoices = generate_invoices(customers, invoice_count)
    fx_rates = generate_fx_rates()

    customers.to_csv(RAW_DATA_DIR / "customers.csv", index=False)
    transactions.to_csv(RAW_DATA_DIR / "transactions.csv", index=False)
    invoices.to_csv(RAW_DATA_DIR / "invoices.csv", index=False)
    fx_rates.to_csv(RAW_DATA_DIR / "fx_rates.csv", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate simulated financial source data.")
    parser.add_argument("--customers", type=int, default=800)
    parser.add_argument("--transactions", type=int, default=6_000)
    parser.add_argument("--invoices", type=int, default=3_000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_all(args.customers, args.transactions, args.invoices, args.seed)
