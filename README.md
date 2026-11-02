# Enterprise BI Foundation for a Digital Bank

Built as part of the **BI Lead case study**

A working prototype of an enterprise BI foundation covering an Executive Dashboard, a Credit & Lending domain dashboard, a Metric Conflict Resolution view, a KPI Dictionary, and a Self-Service Analytics section, all delivered within a single live Metabase dashboard.

**Live dashboard (no login required):** http://metabase-v0-56-4.onrender.com/public/dashboard/393fc0a3-07f3-4ca2-9a18-d2434327fdf1

All data is fully synthetic. No real bank or personal data is used anywhere in this repository.

---

## Dashboard Tour

The dashboard consists of five sections:

1. **Executive Dashboard**: 12+ certified enterprise KPIs, well above the required minimum of 8. This includes 7 headline metrics (Total Customers, Active Customers, Total Loan Portfolio Value, Total Origination Volume, Total Revenue, Total Savings Balance, NPL Ratio) plus additional KPIs surfaced through supporting charts (New Customer Acquisition, Customer Churn Rate, Loan Status Mix, Time-to-Decision, Transaction Volume, Account Growth by Type, and more), spanning Credit, Finance, and Product.
2. **Credit & Lending**: Credit approval funnel (Applied → Qualified → Approved → Funded), portfolio quality, loan status distribution, and risk indicators including NPL Ratio, DPD buckets, and overdue exposure.
3. **Metric Conflict Resolution**: Demonstrates how Finance, Product, and Credit define "Active Customers" differently, alongside the single certified enterprise definition used throughout the platform.
4. **KPI Dictionary**: 26 business metrics documenting domain ownership, business definitions, calculation logic, data sources, refresh cadence, and certification status.
5. **Self-Service Analytics**: Available datasets, access request process, governance guidelines, and service-level expectations for business users.

---

## Why This Matters: Metric Conflict Resolution

The case study assumes Finance, Product, and Credit each report "Active Customers" differently without a common definition. The **Metric Conflict Resolution** section demonstrates how this ambiguity is resolved through BI governance.

* **Finance** ("Balance Holders"): Customers with a positive balance in any account.
* **Product** ("Active Transactors"): Customers who performed at least one transaction within the previous 30 days.
* **Credit** ("Current Borrowers"): Customers with an active or delinquent loan.
* **Certified Enterprise KPI** ("Active Customers"): Customers with an open account and at least one qualifying financial activity (transaction or loan repayment) within the previous 90 days.

Each operational metric is retained because it serves a valid business purpose, but each is given a distinct name. The certified enterprise definition is the only version used in executive reporting, preventing metric ambiguity while preserving domain-specific analysis.

The resulting values are intentionally different and logically consistent with their respective definitions, demonstrating that the underlying data model and business rules are internally consistent rather than artificially aligned.

---

## Technology Stack

**Metabase** (self-hosted on Render) + **Supabase PostgreSQL**

The technology stack was selected to mirror a realistic enterprise BI environment.

* Metabase aligns closely with the role's emphasis on SQL-first analytics, semantic modeling, governed metrics, and executive reporting.
* Native SQL questions and reusable models demonstrate production-style BI development rather than spreadsheet-based reporting.
* Supabase PostgreSQL provides a persistent relational database, allowing Metabase to operate against normalized banking data rather than flat files.
* The combination provides an enterprise-ready workflow while remaining lightweight enough for a prototype completed within the assessment timeframe.

---

## Data

The dataset used in this project is a custom synthetic banking dataset built specifically for this case study.

Development started from a publicly available synthetic banking dataset ("Synthetic Banking Dataset – CSV/SQL/SQLite" by akrambelha) as an initial reference, but the schema, data model, and generation logic were extensively redesigned to support the business scenarios required for an enterprise BI platform.

The final dataset includes six relational tables covering customers, accounts, transactions, loan applications, funded loans, and loan repayments. Several new attributes were introduced, including customer acquisition channel, account lifecycle information, and additional governance fields to support realistic business reporting.

Significant enhancements include:

- Redesigned customer, account, transaction, and loan data to produce more realistic banking relationships and reporting patterns.
- Added a complete **loan_applications** table to model the full lending pipeline (Applied → Qualified → Approved → Funded or Rejected), with approval probability correlated to customer credit score.
- Added an installment-level **loan_repayments** table, enabling realistic repayment behavior, delinquency, DPD buckets, overdue exposure, and NPL calculations.
- Added additional business attributes such as acquisition channel, account closure dates, and status tracking to support Product, Finance, and Credit reporting.
- Generated correlated data rather than random values so that executive and operational KPIs reflect realistic business behaviour.

As a result, portfolio quality metrics including loan status, DPD buckets, overdue exposure, approval rates, and NPL Ratio are calculated from the generated data rather than assigned manually, allowing dashboards and KPI definitions to remain internally consistent.

## Data Model

| Table               | Grain                             | Primary Key                                                  |
| ------------------- | --------------------------------- | ------------------------------------------------------------ |
| `customers`         | One row per customer              | `customer_id`                                                |
| `accounts`          | One row per account               | `account_id` (FK: `customer_id`)                             |
| `transactions`      | One row per transaction           | `transaction_id` (FK: `account_id`)                          |
| `loans`             | One row per funded loan           | `loan_id` (FK: `customer_id`)                                |
| `loan_applications` | One row per application           | `application_id` (FK: `customer_id`, optional FK: `loan_id`) |
| `loan_repayments`   | One row per repayment installment | `repayment_id` (FK: `loan_id`)                               |

**Relationships**

* Customers → Accounts → Transactions
* Customers → Loan Applications → Loans → Loan Repayments

**Business Domain Mapping**

* **Credit**: `loan_applications`, `loans`, `loan_repayments`
* **Savings**: `accounts`
* **Payments**: `transactions`

---

## Design Decisions

* Built a normalized relational model instead of a single denormalized table to better reflect enterprise banking systems.
* Established a governed KPI Dictionary separating certified enterprise KPIs from domain-specific operational metrics.
* Resolved metric ambiguity by preserving business-specific definitions while introducing a single certified enterprise definition.
* Implemented SQL-native analytics within Metabase to demonstrate production-style BI development.
* Modeled repayments at the installment level to enable realistic DPD, overdue, and NPL calculations.
* Separated loan applications from funded loans to accurately represent the lending lifecycle.

---

## Setup / Reproduction

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

```bash
# Generate synthetic data
python3 scripts/generate_synthetic_data.py

# Load into Supabase PostgreSQL
python3 scripts/load_to_supabase.py

# Regenerate a single table
python3 scripts/generate_synthetic_data.py --accounts-only
python3 scripts/load_to_supabase.py accounts
```

---

## Dataset Scale

* 3,000 customers
* 3,900 accounts
* 20,000 transactions
* 2,200 loan applications
* 1,140 funded loans (51.8% funding rate)
* 40,404 repayment installments
* Approximately 12% delinquent/defaulted loan portfolio
* Referential integrity verified across all foreign-key relationships

---

## Notes

* Monetary values are represented in AED-equivalent amounts.
* Sensitive credentials are stored in `.env`, which is excluded from version control. `.env.example` provides the required configuration template.
* This is a static-data prototype. Dashboard refresh cadence, access workflows, and service-level agreements represent the intended production operating model rather than a live implementation.
