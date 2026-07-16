CREATE TABLE IF NOT EXISTS finance_mart.dim_customers (
    customer_id TEXT,
    customer_name TEXT,
    country TEXT,
    segment TEXT,
    risk_level TEXT,
    created_at DATE,
    status TEXT,
    is_duplicate BOOLEAN
);

CREATE TABLE IF NOT EXISTS finance_mart.fact_transactions (
    transaction_id TEXT,
    customer_id TEXT,
    transaction_date DATE,
    amount NUMERIC(18, 2),
    currency TEXT,
    transaction_type TEXT,
    channel TEXT,
    status TEXT,
    is_duplicate BOOLEAN,
    has_valid_customer BOOLEAN,
    risk_level TEXT,
    rate_to_eur NUMERIC(18, 6),
    amount_eur NUMERIC(18, 2),
    anomaly_reasons TEXT,
    anomaly_flag BOOLEAN
);

CREATE TABLE IF NOT EXISTS finance_mart.fact_invoices (
    invoice_id TEXT,
    customer_id TEXT,
    issue_date DATE,
    due_date DATE,
    paid_date DATE,
    amount NUMERIC(18, 2),
    status TEXT,
    has_valid_customer BOOLEAN,
    days_to_pay INTEGER,
    overdue_days INTEGER,
    is_overdue BOOLEAN,
    amount_eur NUMERIC(18, 2),
    anomaly_reasons TEXT,
    anomaly_flag BOOLEAN
);

CREATE TABLE IF NOT EXISTS finance_quality.data_quality_results (
    check_id SERIAL PRIMARY KEY,
    run_id TEXT,
    check_name TEXT,
    table_name TEXT,
    severity TEXT,
    total_rows INTEGER,
    failed_rows INTEGER,
    failed_rate NUMERIC,
    status TEXT,
    business_impact TEXT,
    owner TEXT,
    affected_amount_eur NUMERIC(18, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS finance_quality.pipeline_runs (
    dataset TEXT,
    source_file TEXT,
    row_count INTEGER,
    schema_valid BOOLEAN,
    schema_errors TEXT,
    run_id TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    quality_score NUMERIC(18, 2)
);

CREATE TABLE IF NOT EXISTS finance_mart.mart_kpis (
    metric TEXT PRIMARY KEY,
    value NUMERIC(18, 2)
);

CREATE TABLE IF NOT EXISTS finance_mart.mart_revenue_by_customer (
    customer_id TEXT,
    amount_eur NUMERIC(18, 2),
    customer_name TEXT,
    segment TEXT
);

CREATE TABLE IF NOT EXISTS finance_mart.mart_aging_buckets (
    aging_bucket TEXT,
    amount_eur NUMERIC(18, 2)
);

CREATE TABLE IF NOT EXISTS finance_mart.mart_dso_by_segment (
    segment TEXT,
    average_days_to_pay NUMERIC(18, 2),
    invoice_amount_eur NUMERIC(18, 2),
    invoice_count INTEGER
);

CREATE TABLE IF NOT EXISTS finance_mart.mart_dso_by_country (
    country TEXT,
    average_days_to_pay NUMERIC(18, 2),
    invoice_amount_eur NUMERIC(18, 2),
    invoice_count INTEGER
);

CREATE TABLE IF NOT EXISTS finance_mart.mart_collection_priority (
    invoice_id TEXT,
    customer_id TEXT,
    customer_name TEXT,
    segment TEXT,
    risk_level TEXT,
    due_date DATE,
    amount_eur NUMERIC(18, 2),
    overdue_days INTEGER,
    collection_priority_score NUMERIC(18, 2)
);

CREATE TABLE IF NOT EXISTS finance_mart.mart_fx_exposure (
    currency TEXT,
    transaction_count INTEGER,
    amount_eur NUMERIC(18, 2),
    missing_fx_count INTEGER,
    exposure_rate NUMERIC
);

CREATE TABLE IF NOT EXISTS finance_mart.mart_quality_by_dataset (
    table_name TEXT,
    failed_rows INTEGER,
    affected_amount_eur NUMERIC(18, 2)
);

CREATE TABLE IF NOT EXISTS finance_mart.mart_quality_impact (
    business_impact TEXT,
    owner TEXT,
    status TEXT,
    failed_rows INTEGER,
    affected_amount_eur NUMERIC(18, 2)
);
