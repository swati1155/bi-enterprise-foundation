-- ============================================================
-- EXECUTIVE TAB
-- ============================================================

-- ----------------------------------------------------------
-- TOP WIDGETS
-- ----------------------------------------------------------

-- Widget: Total Customers
-- Tooltip: Total number of customers acquired by the bank.
SELECT COUNT(*) AS total_customers
FROM customers
WHERE created_at <= '2026-07-31'
  [[AND created_at >= {{start_date}}]]
  [[AND created_at <= {{end_date}}]]
;

-- Widget: Active Customers (CERTIFIED definition)
-- Tooltip: Customers with an open account and at least one transaction (including loan repayments) in the trailing 90 days.
WITH open_account_customers AS (
    SELECT DISTINCT customer_id FROM accounts WHERE status != 'closed'
),
tx_active_customers AS (
    SELECT DISTINCT a.customer_id
    FROM accounts a
    JOIN transactions t ON t.account_id = a.account_id
    WHERE t.transaction_date <= {{end_date}}
      AND t.transaction_date >= {{end_date}}::date - INTERVAL '90 days'
),
repayment_active_customers AS (
    SELECT DISTINCT l.customer_id
    FROM loans l
    JOIN loan_repayments lr ON lr.loan_id = l.loan_id
    WHERE lr.paid_date <= {{end_date}}
      AND lr.paid_date >= {{end_date}}::date - INTERVAL '90 days'
),
active_customers AS (
    SELECT customer_id FROM tx_active_customers
    UNION
    SELECT customer_id FROM repayment_active_customers
)
SELECT COUNT(DISTINCT oac.customer_id) AS total_active_customers
FROM open_account_customers oac
JOIN active_customers ac ON ac.customer_id = oac.customer_id;

-- Widget: Total Revenue
-- Tooltip: Interest income from loan repayments (no fee income data yet).
SELECT ROUND(SUM(
    lr.paid_amount * ((l.interest_rate / 100) / (1 + (l.interest_rate / 100)))
)) AS total_revenue_interest_income
FROM loan_repayments lr
JOIN loans l ON l.loan_id = lr.loan_id
WHERE lr.paid_amount IS NOT NULL
  AND lr.paid_date <= '2026-07-31'
  [[AND lr.paid_date >= {{start_date}}]]
  [[AND lr.paid_date <= {{end_date}}]]
;

-- Widget: NPL Ratio
-- Tooltip: Share of the outstanding loan portfolio that has defaulted.
SELECT ROUND(
    100.0 * SUM(CASE WHEN loan_status = 'defaulted' THEN loan_amount ELSE 0 END)
    / NULLIF(SUM(CASE WHEN loan_status != 'fully_paid' THEN loan_amount ELSE 0 END), 0)
, 2) AS npl_ratio_pct
FROM loans
WHERE start_date <= '2026-07-31'
  [[AND start_date >= {{start_date}}]]
  [[AND start_date <= {{end_date}}]]
;

-- Widget: Total Origination Volume
-- Tooltip: Total amount of loans originated (funded) by the bank.
SELECT ROUND(SUM(loan_amount)) AS total_origination_volume
FROM loans
WHERE start_date <= '2026-07-31'
  [[AND start_date >= {{start_date}}]]
  [[AND start_date <= {{end_date}}]]
;

-- Widget: Active Origination Volume
-- Tooltip: Total amount of loans currently in active repayment status.
SELECT ROUND(SUM(loan_amount)) AS active_origination_volume
FROM loans
WHERE loan_status = 'active'
  AND start_date <= '2026-07-31'
  [[AND start_date >= {{start_date}}]]
  [[AND start_date <= {{end_date}}]]
;

-- Widget: Total Savings Balance
-- Tooltip: Total balance held in active savings accounts.
SELECT ROUND(SUM(balance)) AS total_savings_balance
FROM accounts
WHERE account_type = 'Savings' AND status = 'active'
  AND open_date <= '2026-07-31'
  [[AND open_date >= {{start_date}}]]
  [[AND open_date <= {{end_date}}]]
;

-- ----------------------------------------------------------
-- CHARTS — Section: Customer Metrics
-- ----------------------------------------------------------

-- Chart: New Customer Acquisition
-- Tooltip: Number of new customers signed up each month.
WITH months AS (
    SELECT date_trunc('month', gs)::date AS month_date
    FROM generate_series(
        date_trunc('month', {{start_date}})::date,
        date_trunc('month', {{end_date}})::date,
        INTERVAL '1 month'
    ) AS gs
)
SELECT to_char(m.month_date, 'Mon YYYY') AS month,
       COUNT(c.customer_id) AS new_customers
FROM months m
LEFT JOIN customers c
  ON date_trunc('month', c.created_at::date) = m.month_date
 AND c.created_at::date <= '2026-07-31'
GROUP BY m.month_date
ORDER BY m.month_date;

-- Chart: Customers by Channel
-- Tooltip: Breakdown of customers by acquisition channel.
SELECT acquisition_channel, COUNT(*) AS customer_count
FROM customers
WHERE created_at <= '2026-07-31'
  [[AND created_at >= {{start_date}}]]
  [[AND created_at <= {{end_date}}]]
GROUP BY acquisition_channel
ORDER BY customer_count DESC;

-- Chart: Customer Churn Rate
-- Tooltip: Monthly rate of account closures relative to active accounts.
WITH months AS (
    SELECT date_trunc('month', gs)::date AS month_start
    FROM generate_series(
        date_trunc('month', {{start_date}})::date,
        date_trunc('month', {{end_date}})::date,
        INTERVAL '1 month'
    ) AS gs
),
closed_in_month AS (
    SELECT m.month_start, COUNT(*) AS closed_count
    FROM months m
    JOIN accounts a
      ON date_trunc('month', a.closed_date) = m.month_start
     AND a.closed_date <= '2026-07-31'
    GROUP BY m.month_start
),
active_at_start AS (
    SELECT m.month_start, COUNT(*) AS active_count
    FROM months m
    JOIN accounts a
      ON a.open_date < m.month_start
     AND a.open_date <= '2026-07-31'
     AND (a.closed_date IS NULL OR a.closed_date >= m.month_start)
    GROUP BY m.month_start
)
SELECT to_char(m.month_start, 'Mon YYYY') AS month,
       ROUND(100.0 * COALESCE(cim.closed_count, 0) / NULLIF(aas.active_count, 0), 2) AS churn_rate_pct
FROM months m
LEFT JOIN closed_in_month cim ON cim.month_start = m.month_start
LEFT JOIN active_at_start aas ON aas.month_start = m.month_start
ORDER BY m.month_start;

-- Chart: Account Growth by Type
-- Tooltip: Monthly new account openings by account type.
WITH months AS (
    SELECT date_trunc('month', gs)::date AS month_date
    FROM generate_series(
        date_trunc('month', {{start_date}})::date,
        date_trunc('month', {{end_date}})::date,
        INTERVAL '1 month'
    ) AS gs
),
account_types AS (
    SELECT DISTINCT account_type FROM accounts
)
SELECT to_char(m.month_date, 'Mon YYYY') AS month,
       at.account_type,
       COUNT(a.account_id) AS account_count
FROM months m
CROSS JOIN account_types at
LEFT JOIN accounts a
  ON date_trunc('month', a.open_date) = m.month_date
 AND a.open_date <= '2026-07-31'
 AND a.account_type = at.account_type
GROUP BY m.month_date, at.account_type
ORDER BY m.month_date, at.account_type;

-- ----------------------------------------------------------
-- CHARTS — Section: Lending & Credit
-- ----------------------------------------------------------

-- Chart: Loan Origination (combo: bar = amount, line = count)
-- Tooltip: Monthly loan origination volume and count.
WITH months AS (
    SELECT date_trunc('month', gs)::date AS month_date
    FROM generate_series(
        date_trunc('month', {{start_date}})::date,
        date_trunc('month', {{end_date}})::date,
        INTERVAL '1 month'
    ) AS gs
)
SELECT to_char(m.month_date, 'Mon YYYY') AS month,
       ROUND(COALESCE(SUM(l.loan_amount), 0)) AS funded_amount,
       COUNT(l.loan_id) AS funded_count
FROM months m
LEFT JOIN loans l
  ON date_trunc('month', l.start_date) = m.month_date
 AND l.start_date <= '2026-07-31'
GROUP BY m.month_date
ORDER BY m.month_date;

-- Chart: New Loan Applications
-- Tooltip: Monthly loan application volume by stage.
WITH months AS (
    SELECT date_trunc('month', gs)::date AS month_date
    FROM generate_series(
        date_trunc('month', {{start_date}})::date,
        date_trunc('month', {{end_date}})::date,
        INTERVAL '1 month'
    ) AS gs
),
stages AS (
    SELECT stage,
           CASE stage
               WHEN 'applied' THEN '1 Applied'
               WHEN 'qualified' THEN '2 Qualified'
               WHEN 'approved' THEN '3 Approved'
               WHEN 'rejected' THEN '4 Rejected'
               WHEN 'funded' THEN '5 Funded'
           END AS stage_label
    FROM (SELECT DISTINCT stage FROM loan_applications) s
)
SELECT to_char(m.month_date, 'Mon YYYY') AS month,
       s.stage_label,
       COUNT(la.application_id) AS application_count
FROM months m
CROSS JOIN stages s
LEFT JOIN loan_applications la
  ON date_trunc('month', la.applied_date) = m.month_date
 AND la.applied_date <= '2026-07-31'
 AND la.stage = s.stage
GROUP BY m.month_date, s.stage_label
ORDER BY m.month_date, s.stage_label;

-- Chart: Loan Status
-- Tooltip: Distribution of loan amount by current loan status.
SELECT loan_status,
       ROUND(SUM(loan_amount)) AS loan_amount_sum
FROM loans
WHERE start_date <= '2026-07-31'
  [[AND start_date >= {{start_date}}]]
  [[AND start_date <= {{end_date}}]]
GROUP BY loan_status
ORDER BY loan_amount_sum DESC;

-- ----------------------------------------------------------
-- CHARTS — Section: Financial Performance
-- ----------------------------------------------------------

-- Chart: Transaction Amount
-- Tooltip: Monthly transaction value, split by credit and debit flow.
WITH months AS (
    SELECT date_trunc('month', gs)::date AS month_date
    FROM generate_series(
        date_trunc('month', {{start_date}})::date,
        date_trunc('month', {{end_date}})::date,
        INTERVAL '1 month'
    ) AS gs
),
tx_grouped AS (
    SELECT date_trunc('month', transaction_date)::date AS month_date,
           CASE WHEN type = 'deposit' THEN 'Credit' ELSE 'Debit' END AS flow_type,
           amount
    FROM transactions
    WHERE transaction_date <= '2026-07-31'
)
SELECT to_char(m.month_date, 'Mon YYYY') AS month,
       t.flow_type,
       ROUND(COALESCE(SUM(t.amount), 0)) AS transaction_value
FROM months m
LEFT JOIN tx_grouped t ON t.month_date = m.month_date
GROUP BY m.month_date, t.flow_type
ORDER BY m.month_date, t.flow_type;
