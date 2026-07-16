# Financial Data Reliability Pipeline

This project applies software reliability practices to financial data processing. It treats schemas, quality rules, run metadata, traceable failures, tests, and operational ownership as reliability controls around a daily ETL pipeline.

## Executive Summary

Reliable applications still produce unreliable outcomes when their input data is incomplete, duplicated, invalid, or inconsistent. This project extends system-quality thinking into the data layer: validate contracts at ingestion, test business invariants, preserve run evidence, identify the affected dataset and owner, and quantify downstream impact.

The core question is: can a pipeline run be trusted, and can every failure be traced to a dataset, control, owner, and business consequence?

For interview context, see:

- `docs/business_case.md`
- `docs/interview_walkthrough.md`

## What It Demonstrates

- Python ETL using `pandas`
- Data quality checks for duplicate IDs, missing values, invalid customers, abnormal amounts, missing FX rates, overdue invoices, and delayed payments
- PostgreSQL schema, staging tables, marts, and dashboard views
- Processed CSV outputs for lightweight local development
- Streamlit reliability console for run audit, control triage, and impact analysis
- Synthetic data generation with intentional quality issues
- Docker Compose setup with PostgreSQL
- CI pipeline running automated tests

## Tech Stack

| Area | Technology |
| --- | --- |
| ETL | Python + Pandas |
| Database | PostgreSQL |
| SQL | Schema, views, and aggregations |
| Dashboard | Streamlit |

## Data Objects

The pipeline uses four simple business data objects.

### Customers

| Field | Meaning |
| --- | --- |
| `customer_id` | Customer ID |
| `customer_name` | Customer name |
| `country` | Country |
| `segment` | Retail / SME / Corporate |
| `risk_level` | Low / Medium / High |
| `created_at` | Customer creation date |
| `status` | Active / Inactive |

### Transactions

| Field | Meaning |
| --- | --- |
| `transaction_id` | Transaction ID |
| `customer_id` | Customer ID |
| `transaction_date` | Transaction date |
| `amount` | Amount |
| `currency` | EUR / USD / GBP |
| `transaction_type` | Payment / Refund / Transfer |
| `channel` | Web / Branch / API |
| `status` | Completed / Failed / Pending |

### Invoices

| Field | Meaning |
| --- | --- |
| `invoice_id` | Invoice ID |
| `customer_id` | Customer ID |
| `issue_date` | Invoice issue date |
| `due_date` | Due date |
| `paid_date` | Payment date |
| `amount` | Amount in EUR |
| `status` | Paid / Overdue / Open |

### FX Rates

| Field | Meaning |
| --- | --- |
| `rate_date` | Rate date |
| `currency` | Currency |
| `rate_to_eur` | Exchange rate to EUR |

## Project Structure

```text
financial-data-pipeline/
├── data/
│   ├── raw/                 # Source CSV files
│   └── processed/           # Generated pipeline outputs
├── docs/                    # Business case and interview walkthrough
├── src/                     # ETL, checks, metrics, loading, orchestration
├── sql/                     # PostgreSQL schema and reporting views
├── dashboard/               # Streamlit dashboard
├── tests/                   # Unit tests
├── reports/                 # Generated HTML and markdown reports
├── docker-compose.yml
├── Dockerfile
└── .github/workflows/ci.yml
```

## Quick Start

Create an environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Generate simulated source data:

```bash
python generate_data.py --customers 800 --transactions 6000 --invoices 3000
```

Run the pipeline:

```bash
python -m src.pipeline
```

Run tests:

```bash
pytest -q
```

Open the dashboard after the pipeline has generated processed data:

```bash
streamlit run dashboard/app.py
```

## Docker

Run PostgreSQL, execute the pipeline, and open the dashboard:

```bash
docker compose up --build
```

The dashboard is served at `http://localhost:8501`.

## Outputs

Running `python -m src.pipeline` writes:

- Raw layer: `raw_customers.csv`, `raw_transactions.csv`, `raw_invoices.csv`, `raw_fx_rates.csv`
- Staging layer: `stg_customers.csv`, `stg_transactions.csv`, `stg_invoices.csv`
- Mart layer: `dim_customers.csv`, `fact_transactions.csv`, `fact_invoices.csv`, `mart_kpis.csv`, `mart_revenue_by_customer.csv`, `mart_aging_buckets.csv`, `mart_dso_by_segment.csv`, `mart_dso_by_country.csv`, `mart_collection_priority.csv`, `mart_fx_exposure.csv`, `mart_quality_by_dataset.csv`, `mart_quality_impact.csv`
- Quality layer: `data_quality_results.csv`, `pipeline_runs.csv`
- `reports/data_quality_report.html`
- `reports/sample_kpi_report.md`

Generated CSV and report files are intentionally ignored by git. The repository keeps
`data/raw`, `data/processed`, and `reports` as clean output directories with `.gitkeep`
files; regenerate their contents with `python generate_data.py` and `python -m src.pipeline`.

## Intentional Data Issues

`generate_data.py` injects repeatable quality issues:

- Duplicate `transaction_id`
- Missing `customer_id`
- Negative or zero transaction amounts
- Invalid currency values such as `ABC`
- Missing FX rates for unsupported currencies
- Transaction customer IDs that do not exist in customers
- Invalid transaction or invoice status
- Invoice `due_date` earlier than `issue_date`
- `paid_date` later than `due_date`
- Outlier transactions above EUR 50,000
- High-risk customers with large transactions

## Data Quality Checks

The project groups checks into four categories.

### A. Completeness

- `customer_id` is not null
- `transaction_id` is not null
- `amount` is not null
- `invoice_id` is not null
- `due_date` is not null

### B. Uniqueness

- `customer_id` is unique
- `transaction_id` is unique
- `invoice_id` is unique

### C. Validity

- `amount > 0`
- `currency in EUR / USD / GBP`
- `status` is in allowed values
- `risk_level in Low / Medium / High`
- `transaction_date` is not in the future

### D. Consistency

- `transaction.customer_id` exists in customers
- `invoice.customer_id` exists in customers
- `due_date >= issue_date`
- `paid_date >= issue_date`
- FX rate exists for each transaction currency/date

Quality results are written to `finance_quality.data_quality_results` and `data/processed/data_quality_results.csv`:

```sql
CREATE TABLE data_quality_results (
    check_id SERIAL PRIMARY KEY,
    run_id TEXT,
    check_name TEXT,
    table_name TEXT,
    severity TEXT,
    total_rows INT,
    failed_rows INT,
    failed_rate NUMERIC,
    status TEXT,
    business_impact TEXT,
    owner TEXT,
    affected_amount_eur NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

`status` is one of `PASS`, `WARNING`, or `FAIL`, which feeds the dashboard quality score.

## KPI and Reporting Design

Core KPI outputs are written to `data/processed/mart_kpis.csv` and `finance_mart.mart_kpis`:

- Total transaction volume
- Transaction count
- Failed transaction rate
- Overdue invoice amount
- Overdue invoice rate
- High-risk transaction count
- Revenue at risk
- AR at risk
- FX exposure
- Data quality impact EUR
- Data quality score
- Anomaly count

The Streamlit console is organized around reliability evidence:

- `Reliability overview`: control coverage, reliability dimensions, dataset health, and the source-to-mart processing path.
- `Quality controls`: filterable completeness, uniqueness, validity, and consistency results with severity and ownership.
- `Pipeline runs`: run IDs, timestamps, duration, row counts, schema validation, source metadata, and historical quality scores.
- `Business impact`: financial materiality, row-level exceptions, and downstream collection priorities retained as evidence of why data reliability matters.

## Example Business Rules

- Customer IDs should be unique.
- Transaction and invoice records must map to known customers.
- Completed transaction revenue excludes duplicates, negative amounts, failed payments, and unknown customers.
- Invoice lateness is calculated against an `AS_OF_DATE`, defaulting to `2024-02-29`.
- All reporting amounts are normalized to EUR using `data/raw/fx_rates.csv`.

## Optional Database Load

Start PostgreSQL with Docker Compose and load outputs into database tables:

```bash
docker compose up postgres
python -m src.pipeline --load-database
```

Override the database connection with:

```bash
export DATABASE_URL=postgresql+psycopg2://pipeline:pipeline@localhost:5433/financial_data
```

## PostgreSQL Layers

The PostgreSQL load creates four schemas:

- `finance_raw`: `raw_customers`, `raw_transactions`, `raw_invoices`, `raw_fx_rates`
- `finance_staging`: `stg_customers`, `stg_transactions`, `stg_invoices`
- `finance_mart`: `dim_customers`, `fact_transactions`, `fact_invoices`, `mart_kpis`, `mart_revenue_by_customer`, `mart_aging_buckets`, `mart_dso_by_segment`, `mart_dso_by_country`, `mart_collection_priority`, `mart_fx_exposure`, `mart_quality_impact`
- `finance_quality`: `data_quality_results`, `pipeline_runs`
