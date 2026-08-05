# KPI Dictionary — Business Insights Dashboard

**Assumption:** Refresh Cadence is listed as "Daily" for all metrics since the underlying data is loaded via a static script, not a live pipeline. Update this column once real pipeline scheduling exists.

| Metric Name | Domain Owner | Business Definition | Formula | Data Source | Refresh Cadence | Status |
|---|---|---|---|---|---|---|
| Total Customers | Product | Total number of customers acquired by the bank | `COUNT(*)` | customers | Daily | Certified |
| Active Customers | Enterprise BI | Customers with an open account and any activity (transaction or loan repayment) in the trailing 90 days | Open account AND activity within trailing 90 days of the reporting date | customers, accounts, transactions, loans, loan_repayments | Daily | Certified |
| Total Revenue | Finance | Interest income earned from loan repayments (no fee income in current data) | `SUM(paid_amount * (rate/(1+rate)))`, where `rate = interest_rate/100` | loan_repayments, loans | Daily | Certified |
| NPL Ratio | Credit | Share of the outstanding loan portfolio that has defaulted | `SUM(loan_amount WHERE loan_status='defaulted') / SUM(loan_amount WHERE loan_status != 'fully_paid') * 100` | loans | Daily | Certified |
| Total Origination Volume | Credit | Total amount of loans ever originated (funded), all statuses | `SUM(loan_amount)` | loans | Daily | Certified |
| Active Origination Volume | Credit | Total amount of loans currently in active repayment (excludes delinquent/defaulted) | `SUM(loan_amount WHERE loan_status='active')` | loans | Daily | Certified |
| Total Savings Balance | Finance | Total balance held in active savings accounts | `SUM(balance WHERE account_type='Savings' AND status='active')` | accounts | Daily | Certified |
| New Customer Acquisition | Product | Number of new customers signed up per month | `COUNT(customer_id)` grouped by month | customers | Daily | Certified |
| Customers by Channel | Product | Breakdown of customers by acquisition channel | `COUNT(*)` grouped by `acquisition_channel` | customers | Daily | Certified |
| Customer Churn Rate | Product | Monthly rate of account closures relative to active accounts at start of month | `COUNT(closed in month) / COUNT(active at month start) * 100` | accounts | Daily | Certified |
| Account Growth by Type | Finance | Monthly new account openings by account type | `COUNT(account_id)` grouped by month, `account_type` | accounts | Daily | Certified |
| Loan Origination (Amount & Count) | Credit | Monthly loan origination volume and count | `SUM(loan_amount)`, `COUNT(loan_id)` grouped by month | loans | Daily | Certified |
| New Loan Applications | Credit | Monthly application volume by pipeline stage | `COUNT(application_id)` grouped by month, `stage` | loan_applications | Daily | Certified |
| Loan Status Mix | Credit | Distribution of loan amount by current status | `SUM(loan_amount)` grouped by `loan_status` | loans | Daily | Certified |
| Transaction Amount (Credit/Debit) | Finance | Monthly transaction value split by credit and debit flow | `SUM(amount)` grouped by month, flow_type (`deposit`=Credit, else Debit) | transactions | Daily | Certified |
| Approval Rate | Credit | Share of applications that reach approved or funded stage | `COUNT(stage IN ('approved','funded')) / COUNT(*) * 100` | loan_applications | Daily | Certified |
| Disbursement Rate | Credit | Share of all applications that ultimately get funded | `COUNT(stage='funded') / COUNT(*) * 100` | loan_applications | Daily | Certified |
| On-Time Repayment Rate | Credit | Share of due installments paid on or before their due date | `COUNT(paid_date NOT NULL AND days_late<=0) / COUNT(due_date<=today) * 100` | loan_repayments | Daily | Certified |
| Total Overdue Amount | Credit | Amount still owed on installments past their due date | `SUM(due_amount - COALESCE(paid_amount,0))` where unpaid/late and past due | loan_repayments | Daily | Certified |
| Credit Funnel | Credit | Applications reaching each stage of the credit pipeline (cumulative) | `COUNT(*)` filtered by stage reached | loan_applications | Daily | Certified |
| Rejection Reasons | Credit | Breakdown of why rejected applications were declined | `COUNT(*)` grouped by `rejection_reason` where `outcome='rejected'` | loan_applications | Daily | Certified |
| Time-to-Decision (Funded vs Rejected) | Credit | Average days from application to final funded or rejected decision, by month applied | `AVG(last_status_updated_date - applied_date)`, split by outcome | loan_applications | Daily | Certified |
| DPD Bucket Distribution | Credit | Currently unpaid installments grouped by days past due (0-30 / 31-90 / 91+) | `COUNT(DISTINCT loan_id)`, `SUM(due_amount-paid_amount)` grouped by days_late bucket, where `paid_date IS NULL` | loan_repayments | Daily | Certified |
| Balance Holders (Finance's "Active Customers") | Finance | Customers with a positive balance in any account | `COUNT(DISTINCT customer_id) WHERE balance > 0` | accounts | Daily | Domain-specific |
| Active Transactors (Product's "Active Customers") | Product | Customers with a transaction in the last 30 days | `COUNT(DISTINCT customer_id)` with `transaction_date` within trailing 30 days | accounts, transactions | Daily | Domain-specific |
| Current Borrowers (Credit's "Active Customers") | Credit | Customers with an open loan (active or delinquent) | `COUNT(DISTINCT customer_id) WHERE loan_status IN ('active','delinquent')` | loans | Daily | Domain-specific |
