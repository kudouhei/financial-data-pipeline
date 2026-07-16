CREATE TABLE IF NOT EXISTS finance_raw.raw_customers (
    customer_id TEXT,
    customer_name TEXT,
    country TEXT,
    segment TEXT,
    risk_level TEXT,
    created_at DATE,
    status TEXT
);

CREATE TABLE IF NOT EXISTS finance_raw.raw_transactions (
    transaction_id TEXT,
    customer_id TEXT,
    transaction_date DATE,
    amount NUMERIC(18, 2),
    currency TEXT,
    transaction_type TEXT,
    channel TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS finance_raw.raw_invoices (
    invoice_id TEXT,
    customer_id TEXT,
    issue_date DATE,
    due_date DATE,
    paid_date DATE,
    amount NUMERIC(18, 2),
    status TEXT
);

CREATE TABLE IF NOT EXISTS finance_raw.raw_fx_rates (
    rate_date DATE,
    currency TEXT,
    rate_to_eur NUMERIC(18, 6)
);

CREATE TABLE IF NOT EXISTS finance_staging.stg_customers (
    customer_id TEXT,
    customer_name TEXT,
    country TEXT,
    segment TEXT,
    risk_level TEXT,
    created_at DATE,
    status TEXT,
    is_duplicate BOOLEAN
);

CREATE TABLE IF NOT EXISTS finance_staging.stg_transactions (
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

CREATE TABLE IF NOT EXISTS finance_staging.stg_invoices (
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
