-- ============================================================
-- CREDIT & LENDING TAB
-- ============================================================

-- ----------------------------------------------------------
-- TOP WIDGETS
-- ----------------------------------------------------------

-- Widget: Approval Rate
-- Tooltip: Share of applications that get approved.
SELECT ROUND(
    100.0 * COUNT(*) FILTER (WHERE stage IN ('approved','funded'))
    / NULLIF(COUNT(*), 0)
, 2) AS approval_rate_pct
FROM loan_applications
WHERE applied_date <= '2026-07-31'
  [[AND applied_date >= {{start_date}}]]
  [[AND applied_date <= {{end_date}}]]
;

-- Widget: Disbursement Rate
-- Tooltip: Share of applications that ultimately get funded.
SELECT ROUND(
    100.0 * COUNT(*) FILTER (WHERE stage = 'funded')
    / NULLIF(COUNT(*), 0)
, 2) AS disbursement_rate_pct
FROM loan_applications
WHERE applied_date <= '2026-07-31'
  [[AND applied_date >= {{start_date}}]]
  [[AND applied_date <= {{end_date}}]]
;

-- Widget: NPL Ratio (same certified metric as Executive tab, reused)
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

-- Widget: On-Time Repayment Rate ("On-Time Rate")
-- Tooltip: Share of due installments paid on or before their due date.
SELECT ROUND(
    100.0 * COUNT(*) FILTER (WHERE paid_date IS NOT NULL AND days_late <= 0)
    / NULLIF(COUNT(*) FILTER (WHERE due_date <= '2026-07-31'), 0)
, 2) AS on_time_repayment_rate_pct
FROM loan_repayments
WHERE due_date <= '2026-07-31'
  [[AND due_date >= {{start_date}}]]
  [[AND due_date <= {{end_date}}]]
;

-- Widget: Total Overdue Amount
-- Tooltip: Amount still owed on installments past their due date.
SELECT ROUND(SUM(due_amount - COALESCE(paid_amount, 0))) AS total_overdue_amount
FROM loan_repayments
WHERE due_date < '2026-07-31'
  AND (paid_date IS NULL OR days_late > 0)
  [[AND due_date >= {{start_date}}]]
  [[AND due_date <= {{end_date}}]]
;

-- ----------------------------------------------------------
-- CHARTS — Section: Application Pipeline
-- ----------------------------------------------------------

-- Chart: Credit Funnel
-- Tooltip: Number of applications progressing through each stage of the credit approval pipeline.
SELECT 'Applied' AS stage, COUNT(*) AS application_count, 1 AS sort_order
FROM loan_applications
WHERE applied_date <= '2026-07-31'
  [[AND applied_date >= {{start_date}}]]
  [[AND applied_date <= {{end_date}}]]
UNION ALL
SELECT 'Qualified', COUNT(*) FILTER (WHERE stage IN ('qualified','approved','funded')), 2
FROM loan_applications
WHERE applied_date <= '2026-07-31'
  [[AND applied_date >= {{start_date}}]]
  [[AND applied_date <= {{end_date}}]]
UNION ALL
SELECT 'Approved', COUNT(*) FILTER (WHERE stage IN ('approved','funded')), 3
FROM loan_applications
WHERE applied_date <= '2026-07-31'
  [[AND applied_date >= {{start_date}}]]
  [[AND applied_date <= {{end_date}}]]
UNION ALL
SELECT 'Funded', COUNT(*) FILTER (WHERE stage = 'funded'), 4
FROM loan_applications
WHERE applied_date <= '2026-07-31'
  [[AND applied_date >= {{start_date}}]]
  [[AND applied_date <= {{end_date}}]]
ORDER BY sort_order;

-- Chart: Rejection Reasons
-- Tooltip: Breakdown of why rejected applications were declined.
SELECT rejection_reason, COUNT(*) AS rejection_count
FROM loan_applications
WHERE outcome = 'rejected'
  AND applied_date <= '2026-07-31'
  [[AND applied_date >= {{start_date}}]]
  [[AND applied_date <= {{end_date}}]]
GROUP BY rejection_reason
ORDER BY rejection_count DESC;

-- Chart: Time-to-Decision (Funded vs Rejected)
-- Tooltip: Average time from application to a final funded or rejected decision, grouped by the month the application was submitted.
WITH months AS (
    SELECT date_trunc('month', gs)::date AS month_date
    FROM generate_series(
        date_trunc('month', {{start_date}})::date,
        date_trunc('month', {{end_date}})::date,
        INTERVAL '1 month'
    ) AS gs
)
SELECT to_char(m.month_date, 'Mon YYYY') AS application_month,
       ROUND(AVG(la.last_status_updated_date - la.applied_date) FILTER (WHERE la.outcome = 'funded'), 2) AS avg_days_to_fund,
       ROUND(AVG(la.last_status_updated_date - la.applied_date) FILTER (WHERE la.outcome = 'rejected'), 2) AS avg_days_to_reject
FROM months m
LEFT JOIN loan_applications la
  ON date_trunc('month', la.applied_date) = m.month_date
 AND la.applied_date <= '2026-07-31'
GROUP BY m.month_date
ORDER BY m.month_date;

-- ----------------------------------------------------------
-- CHARTS — Section: Portfolio Risk
-- ----------------------------------------------------------

-- Chart: DPD Bucket Distribution
-- Tooltip: Currently unpaid installments past due date, grouped by how many days late.
SELECT
    CASE
        WHEN days_late BETWEEN 1 AND 30 THEN '0-30'
        WHEN days_late BETWEEN 31 AND 90 THEN '31-90'
        ELSE '91+'
    END AS dpd_bucket,
    CASE
        WHEN days_late BETWEEN 1 AND 30 THEN 1
        WHEN days_late BETWEEN 31 AND 90 THEN 2
        ELSE 3
    END AS sort_order,
    COUNT(DISTINCT loan_id) AS loan_count,
    ROUND(SUM(due_amount - COALESCE(paid_amount, 0))) AS overdue_amount
FROM loan_repayments
WHERE due_date <= '2026-07-31'
  AND paid_date IS NULL
  [[AND due_date >= {{start_date}}]]
  [[AND due_date <= {{end_date}}]]
GROUP BY dpd_bucket, sort_order
ORDER BY sort_order;

-- Chart: Loan Status (same certified metric as Executive tab, reused)
-- Tooltip: Distribution of loan amount by current loan status.
SELECT loan_status,
       ROUND(SUM(loan_amount)) AS loan_amount_sum
FROM loans
WHERE start_date <= '2026-07-31'
  [[AND start_date >= {{start_date}}]]
  [[AND start_date <= {{end_date}}]]
GROUP BY loan_status
ORDER BY loan_amount_sum DESC;
