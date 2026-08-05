# Metric Conflict Resolution Tab

**Top text card:**
> Three teams at the bank each reported a different number under the name "Active Customers," measuring completely different things: Finance looked at account balances, Product looked at transaction activity, and Credit looked at open loans. This tab reconciles that conflict. Each team's original metric has been renamed to reflect what it actually measures, and the canonical name "Active Customers" is now reserved for the single certified definition used company wide.

---

### Widget: Balance Holders

**Tooltip:** Finance: counts customers with a positive balance in any account.

```sql
SELECT COUNT(DISTINCT customer_id) AS finance_active_customers
FROM accounts
WHERE balance > 0;
```

---

### Widget: Active Transactors

**Tooltip:** Product: counts customers with a transaction in the last 30 days.

```sql
SELECT COUNT(DISTINCT a.customer_id) AS product_active_customers
FROM accounts a
JOIN transactions t ON t.account_id = a.account_id
WHERE t.transaction_date <= '2026-07-31'
  AND t.transaction_date >= '2026-07-31'::date - INTERVAL '30 days';
```

---

### Widget: Current Borrowers

**Tooltip:** Credit: counts customers with an open loan.

```sql
SELECT COUNT(DISTINCT customer_id) AS credit_active_customers
FROM loans
WHERE loan_status IN ('active','delinquent')
  AND start_date <= '2026-07-31';
```

---

### Widget: Active Customers (CERTIFIED)

**Tooltip:** Certified: open account plus any activity (deposits, withdrawals, or loan repayments) in the last 90 days.

```sql
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
```
