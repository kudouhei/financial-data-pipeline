from __future__ import annotations

import pandas as pd

from src.quality_checks import quality_score


def build_kpis(transformed: dict[str, pd.DataFrame], quality_issues: pd.DataFrame) -> pd.DataFrame:
    transactions = transformed["transactions"]
    invoices = transformed["invoices"]
    customers = transformed["customers"]

    transactions_with_amount = transactions[transactions["amount_eur"].notna()]
    valid_completed = transactions[
        (transactions["status"] == "completed")
        & (~transactions["is_duplicate"])
        & (transactions["amount"] > 0)
        & (transactions["has_valid_customer"])
    ]
    open_invoices = invoices[invoices["paid_date"].isna()]
    overdue_invoices = invoices[invoices["is_overdue"]]
    high_risk_transactions = transactions[
        (transactions["risk_level"] == "high")
        & (transactions["amount_eur"] > 50_000)
    ]
    invoices_with_risk = invoices.merge(
        customers[["customer_id", "risk_level"]],
        on="customer_id",
        how="left",
    )
    high_risk_overdue_invoices = invoices_with_risk[
        (invoices_with_risk["risk_level"] == "high")
        & (invoices_with_risk["is_overdue"])
    ]
    non_eur_transactions = transactions_with_amount[transactions_with_amount["currency"] != "EUR"]
    revenue_at_risk = quality_issues.loc[
        quality_issues["business_impact"] == "Revenue",
        "affected_amount_eur",
    ].sum()
    data_quality_impact = quality_issues["affected_amount_eur"].sum()
    total_volume = transactions_with_amount["amount_eur"].sum()

    kpis = {
        "total_transaction_volume_eur": total_volume,
        "transaction_count": len(transactions),
        "failed_transaction_rate": (transactions["status"] == "failed").mean(),
        "overdue_invoice_amount_eur": overdue_invoices["amount_eur"].sum(),
        "overdue_invoice_rate": invoices["is_overdue"].mean(),
        "high_risk_transaction_count": len(high_risk_transactions),
        "anomaly_count": transactions["anomaly_flag"].sum(),
        "revenue_at_risk_eur": revenue_at_risk,
        "ar_at_risk_eur": high_risk_overdue_invoices["amount_eur"].sum(),
        "fx_exposure_eur": non_eur_transactions["amount_eur"].sum(),
        "fx_exposure_rate": non_eur_transactions["amount_eur"].sum() / total_volume
        if total_volume
        else 0.0,
        "data_quality_impact_eur": data_quality_impact,
        "active_customers": (customers["status"] == "active").sum(),
        "completed_transaction_count": len(valid_completed),
        "completed_transaction_amount_eur": valid_completed["amount_eur"].sum(),
        "open_invoice_amount_eur": open_invoices["amount_eur"].sum(),
        "overdue_invoice_count": invoices["is_overdue"].sum(),
        "average_days_to_pay": invoices.loc[invoices["paid_date"].notna(), "days_to_pay"].mean(),
        "transaction_anomaly_count": transactions["anomaly_flag"].sum(),
        "invoice_anomaly_count": invoices["anomaly_flag"].sum(),
        "data_quality_score": quality_score(quality_issues),
        "high_severity_issue_count": quality_issues.loc[
            quality_issues["severity"] == "high", "failed_rows"
        ].sum(),
    }

    return pd.DataFrame(
        [{"metric": metric, "value": round(float(value), 2)} for metric, value in kpis.items()]
    )


def revenue_by_customer(transformed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    transactions = transformed["transactions"]
    customers = transformed["customers"][["customer_id", "customer_name", "segment"]]
    valid = transactions[
        (transactions["status"] == "completed")
        & (~transactions["is_duplicate"])
        & (transactions["amount"] > 0)
        & (transactions["has_valid_customer"])
    ]

    return (
        valid.groupby("customer_id", as_index=False)["amount_eur"]
        .sum()
        .merge(customers, on="customer_id", how="left")
        .sort_values("amount_eur", ascending=False)
    )


def aging_buckets(transformed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    invoices = transformed["invoices"].copy()
    open_invoices = invoices[invoices["paid_date"].isna()].copy()
    open_invoices["aging_bucket"] = pd.cut(
        open_invoices["overdue_days"],
        bins=[-1, 0, 30, 60, 10_000],
        labels=["current", "1-30 days", "31-60 days", "60+ days"],
    )

    return (
        open_invoices.groupby("aging_bucket", observed=False, as_index=False)["amount_eur"]
        .sum()
        .sort_values("aging_bucket")
    )


def dso_by_segment(transformed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    invoices = transformed["invoices"]
    customers = transformed["customers"][["customer_id", "segment", "country"]]
    paid = invoices[invoices["paid_date"].notna()].merge(customers, on="customer_id", how="left")
    return (
        paid.groupby("segment", dropna=False, as_index=False)
        .agg(
            average_days_to_pay=("days_to_pay", "mean"),
            invoice_amount_eur=("amount_eur", "sum"),
            invoice_count=("invoice_id", "count"),
        )
        .round({"average_days_to_pay": 2, "invoice_amount_eur": 2})
    )


def dso_by_country(transformed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    invoices = transformed["invoices"]
    customers = transformed["customers"][["customer_id", "country"]]
    paid = invoices[invoices["paid_date"].notna()].merge(customers, on="customer_id", how="left")
    return (
        paid.groupby("country", dropna=False, as_index=False)
        .agg(
            average_days_to_pay=("days_to_pay", "mean"),
            invoice_amount_eur=("amount_eur", "sum"),
            invoice_count=("invoice_id", "count"),
        )
        .round({"average_days_to_pay": 2, "invoice_amount_eur": 2})
    )


def collection_priority(transformed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    invoices = transformed["invoices"]
    customers = transformed["customers"][
        ["customer_id", "customer_name", "segment", "risk_level"]
    ]
    open_invoices = invoices[invoices["paid_date"].isna()].merge(
        customers,
        on="customer_id",
        how="left",
    )
    risk_weight = open_invoices["risk_level"].map({"high": 3, "medium": 2, "low": 1}).fillna(1)
    open_invoices["collection_priority_score"] = (
        open_invoices["overdue_days"].fillna(0) * 2
        + open_invoices["amount_eur"].fillna(0) / 1_000
        + risk_weight * 25
    ).round(2)
    return open_invoices.sort_values("collection_priority_score", ascending=False)[
        [
            "invoice_id",
            "customer_id",
            "customer_name",
            "segment",
            "risk_level",
            "due_date",
            "amount_eur",
            "overdue_days",
            "collection_priority_score",
        ]
    ]


def fx_exposure(transformed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    transactions = transformed["transactions"]
    exposure = (
        transactions.groupby("currency", dropna=False, as_index=False)
        .agg(
            transaction_count=("transaction_id", "count"),
            amount_eur=("amount_eur", "sum"),
            missing_fx_count=("rate_to_eur", lambda series: series.isna().sum()),
        )
        .sort_values("amount_eur", ascending=False)
    )
    total_amount = exposure["amount_eur"].sum()
    exposure["exposure_rate"] = (
        exposure["amount_eur"] / total_amount if total_amount else 0.0
    )
    return exposure.round({"amount_eur": 2, "exposure_rate": 4})


def build_metric_outputs(
    transformed: dict[str, pd.DataFrame],
    quality_issues: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    return {
        "kpis": build_kpis(transformed, quality_issues),
        "revenue_by_customer": revenue_by_customer(transformed),
        "aging_buckets": aging_buckets(transformed),
        "dso_by_segment": dso_by_segment(transformed),
        "dso_by_country": dso_by_country(transformed),
        "collection_priority": collection_priority(transformed),
        "fx_exposure": fx_exposure(transformed),
        "quality_by_dataset": quality_issues.groupby("table_name", as_index=False).agg(
            failed_rows=("failed_rows", "sum"),
            affected_amount_eur=("affected_amount_eur", "sum"),
        ),
        "quality_impact": quality_issues.groupby(
            ["business_impact", "owner", "status"],
            as_index=False,
        ).agg(
            failed_rows=("failed_rows", "sum"),
            affected_amount_eur=("affected_amount_eur", "sum"),
        ),
    }


def render_kpi_markdown(metrics: dict[str, pd.DataFrame]) -> str:
    kpis = metrics["kpis"].set_index("metric")["value"].to_dict()
    revenue = metrics["revenue_by_customer"].head(5)
    aging = metrics["aging_buckets"]

    revenue_lines = [
        f"- {row.customer_name}: EUR {row.amount_eur:,.2f}"
        for row in revenue.itertuples(index=False)
    ]
    aging_lines = [
        f"- {row.aging_bucket}: EUR {row.amount_eur:,.2f}"
        for row in aging.itertuples(index=False)
    ]

    return "\n".join(
        [
            "# Sample KPI Report",
            "",
            f"- Total transaction volume: EUR {kpis['total_transaction_volume_eur']:,.2f}",
            f"- Transaction count: {int(kpis['transaction_count'])}",
            f"- Failed transaction rate: {kpis['failed_transaction_rate']:.2%}",
            f"- Overdue invoice amount: EUR {kpis['overdue_invoice_amount_eur']:,.2f}",
            f"- Overdue invoice rate: {kpis['overdue_invoice_rate']:.2%}",
            f"- High-risk transaction count: {int(kpis['high_risk_transaction_count'])}",
            f"- Anomaly count: {int(kpis['anomaly_count'])}",
            f"- Data quality score: {kpis['data_quality_score']}",
            "",
            "## Revenue by Customer",
            *revenue_lines,
            "",
            "## Accounts Receivable Aging",
            *aging_lines,
            "",
        ]
    )
