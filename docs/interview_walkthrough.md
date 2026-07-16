# Interview Walkthrough

## 30-Second Pitch

This is a Financial Data Quality & Risk Control Tower. It simulates how a finance operations team ingests daily customer, transaction, invoice, and FX data, detects quality issues, quantifies financial impact, and produces a dashboard for revenue reporting, risk monitoring, and cash collection.

## 3-5 Minute Demo Flow

1. Start with the business problem.
   - Finance needs reliable daily reporting.
   - Bad data can overstate revenue, hide overdue receivables, or miss high-risk exposure.

2. Show the generated source data.
   - `generate_data.py` creates realistic customers, transactions, invoices, and FX rates.
   - The data intentionally includes duplicates, missing IDs, invalid currency, missing FX, overdue invoices, and high-risk large transactions.

3. Explain the pipeline layers.
   - Raw: source backup.
   - Staging: standardized and enriched data.
   - Mart: finance-ready facts, dimensions, KPIs, and risk views.
   - Quality: check-level results with severity, owner, business impact, and affected EUR.

4. Open the dashboard.
   - Overview: CFO-level KPIs such as Revenue at Risk, AR at Risk, Data Quality Score, and FX Exposure.
   - Data Quality: PASS/WARNING/FAIL checks with owners and financial impact.
   - Transactions: high-value and anomalous transactions by segment, country, and channel.
   - Invoices: overdue invoices, collection priority, DSO, and outstanding amount by segment.

5. Highlight the engineering decisions.
   - Reproducible synthetic data.
   - Python + pandas ETL.
   - PostgreSQL layered schemas.
   - Streamlit business dashboard.
   - CI tests.
   - Generated outputs ignored by git for a clean project structure.

## Strong Interview Talking Points

- I designed the project around business materiality, not just row counts.
- Data quality checks include affected amount and owner, so failures are actionable.
- The dashboard separates executive summary from analyst triage.
- Synthetic data follows business assumptions: corporate customers transact more, high-risk customers have more collection and transaction risk, and FX gaps simulate upstream market data delays.
- The project is reproducible locally and can load the same layers into PostgreSQL.

## Concise Closing

The main value is that the pipeline translates raw operational data quality into financial risk and reporting confidence. That is the difference between a technical ETL project and a finance analytics control framework.
