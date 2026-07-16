CREATE OR REPLACE VIEW finance_mart.v_dashboard_summary AS
SELECT
    metric,
    value
FROM finance_mart.mart_kpis;

CREATE OR REPLACE VIEW finance_mart.v_quality_issues_by_dataset AS
SELECT
    table_name,
    severity,
    SUM(failed_rows) AS failed_rows,
    SUM(affected_amount_eur) AS affected_amount_eur
FROM finance_quality.data_quality_results
GROUP BY table_name, severity;

CREATE OR REPLACE VIEW finance_mart.v_customer_revenue_rank AS
SELECT
    customer_id,
    customer_name,
    segment,
    amount_eur,
    RANK() OVER (ORDER BY amount_eur DESC) AS revenue_rank
FROM finance_mart.mart_revenue_by_customer;
