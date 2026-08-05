# Self-Service Analytics

## Available Datasets

| Dataset               | Description                                                                                                | Data Owner |
| --------------------- | ---------------------------------------------------------------------------------------------------------- | ---------- |
| **customers**         | Customer profile data including demographics, segment, credit score, acquisition channel, and signup date. | Product    |
| **accounts**          | Deposit account records including account type, balance, status, and lifecycle dates.                      | Finance    |
| **transactions**      | Transaction-level activity including transaction amount, type, and date.                                   | Finance    |
| **loans**             | Loan-level records including loan amount, interest rate, tenure, start date, and current status.           | Credit     |
| **loan_applications** | Credit application pipeline including application stage, outcome, and rejection reason.                    | Credit     |
| **loan_repayments**   | Installment-level repayment history including due dates, payment dates, and delinquency information.       | Credit     |

---

## Access Request Process

1. Submit an access request through the **IT Service Portal** or by emailing the **Data Governance Team**.
2. Include the following information in your request:

   * Team or department
   * Requested dataset(s)
   * Business justification
   * Required access level:

     * **Certified datasets** (recommended for reporting and self-service analytics)
     * **Raw table access** (granted only when certified datasets do not meet the business requirement)
3. Requests involving sensitive fields such as customer PII, credit scores, or rejection reasons require approval from the respective Data Owner and are logged for audit purposes.
4. Once approved, access is provisioned in Metabase according to your role and the principle of least privilege.

---

## Governance

* Executive and management reporting must use **Certified** metrics defined in the **KPI Dictionary**.
* Domain-specific metrics may be used for operational analysis but should not replace certified enterprise KPIs.
* Metric definitions, ownership, and calculation logic are maintained centrally to ensure a single source of truth.
* Certified datasets are the preferred source for self-service analytics. Raw tables should only be used when a certified dataset does not satisfy the business requirement.

---

## Service Levels (SLA)

| Service                            | Target                                                  |
| ---------------------------------- | ------------------------------------------------------- |
| Data Refresh                       | Daily                                                   |
| Standard Access Request            | Within 2 business days                                  |
| Sensitive Data Access              | Within 5 business days (subject to Data Owner approval) |
| Data Quality Issue Acknowledgement | Within 1 business day                                   |

> **Note:** This prototype uses static synthetic data. In a production environment, refresh schedules, access workflows, and SLAs would be aligned with the underlying data platform and enterprise data governance policies.
