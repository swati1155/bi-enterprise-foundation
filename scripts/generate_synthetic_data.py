"""
Synthetic relational banking data generator for the Mal BI case study.
Fully synthetic (Faker-generated) — no real personal data.
Currency for balance/amount fields is AED-equivalent (no currency label in columns).
"""
import random
import string
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)
fake = Faker()
Faker.seed(RNG_SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "synthetic_dataset"
TODAY = pd.Timestamp("2026-08-01")

N_CUSTOMERS = 3000
N_ACCOUNTS = int(N_CUSTOMERS * 1.3)
N_TRANSACTIONS = 20000
N_LOAN_APPLICATIONS = 2200

ALNUM = string.ascii_uppercase + string.digits


def gen_id(prefix, n=12):
    return prefix + "".join(random.choices(ALNUM, k=n))


def unique_ids(prefix, count, n=12):
    ids = set()
    while len(ids) < count:
        ids.add(gen_id(prefix, n))
    return list(ids)


# ---------------------------------------------------------------------------
# 1. customers.csv
# ---------------------------------------------------------------------------
EMIRATE_CITY_MAP = {
    "Abu Dhabi": ["Abu Dhabi", "Al Ain", "Madinat Zayed", "Ruwais"],
    "Dubai": ["Dubai", "Deira", "Jebel Ali"],
    "Sharjah": ["Sharjah", "Khor Fakkan", "Kalba"],
    "Ajman": ["Ajman"],
    "Ras Al Khaimah": ["Ras Al Khaimah", "Julfar"],
    "Fujairah": ["Fujairah", "Dibba Al-Fujairah"],
    "Umm Al Quwain": ["Umm Al Quwain"],
}
EMIRATES = list(EMIRATE_CITY_MAP.keys())
EMIRATE_WEIGHTS = [0.30, 0.35, 0.20, 0.05, 0.05, 0.03, 0.02]

customer_ids = unique_ids("CUS", N_CUSTOMERS)
email_domains = ["example.com", "example.net", "example.org"]

customers = []
for cid in customer_ids:
    first = fake.first_name()
    last = fake.last_name()
    email = f"{first.lower()}{last.lower()}{random.randint(1, 999)}@{random.choice(email_domains)}"
    region = random.choices(EMIRATES, weights=EMIRATE_WEIGHTS, k=1)[0]
    city = random.choice(EMIRATE_CITY_MAP[region])
    credit_score = int(np.clip(np.random.normal(650, 85), 300, 850))
    # premium segment skews toward higher credit scores
    premium_prob = np.clip((credit_score - 500) / 500, 0.03, 0.6)
    segment = "premium" if random.random() < premium_prob else "retail"
    acquisition_channel = random.choices(
        ["branch", "digital", "referral"], weights=[0.35, 0.5, 0.15], k=1
    )[0]
    created_at = fake.date_between(start_date="-7y", end_date="today")
    customers.append(
        {
            "customer_id": cid,
            "first_name": first,
            "last_name": last,
            "email": email,
            "city": city,
            "region": region,
            "credit_score": credit_score,
            "segment": segment,
            "acquisition_channel": acquisition_channel,
            "created_at": created_at,
        }
    )

customers_df = pd.DataFrame(customers)
customers_df["created_at"] = pd.to_datetime(customers_df["created_at"])

# ---------------------------------------------------------------------------
# 2. accounts.csv
# ---------------------------------------------------------------------------
account_ids = unique_ids("ACC", N_ACCOUNTS)
account_owner_ids = np.random.choice(customer_ids, size=N_ACCOUNTS, replace=True)

customer_created_map = customers_df.set_index("customer_id")["created_at"].to_dict()

accounts = []
for aid, cid in zip(account_ids, account_owner_ids):
    cust_created = customer_created_map[cid]
    open_date = fake.date_between(start_date=cust_created.date(), end_date="today")
    account_type = random.choices(
        ["Savings", "Current", "Business"], weights=[0.5, 0.4, 0.1], k=1
    )[0]
    balance = round(np.random.lognormal(mean=9.0, sigma=1.1), 2)
    status = random.choices(["active", "dormant", "closed"], weights=[0.73, 0.12, 0.15], k=1)[0]

    closed_date = None
    if status == "closed":
        days_available = (TODAY.date() - open_date).days
        if days_available >= 2:
            # closures cluster with a gradual month-over-month ramp toward the
            # present (not a hard skew into the last few days), so churn trends
            # smoothly instead of spiking in the most recent bucket
            max_months_back = max(1, min(24, days_available // 30))
            month_weights = np.linspace(1.3, 0.7, max_months_back)  # recent -> older
            months_back = random.choices(range(max_months_back), weights=month_weights, k=1)[0]
            bucket_hi = min(days_available - int(months_back * 30.44), days_available - 1)
            bucket_lo = max(days_available - int((months_back + 1) * 30.44), 1)
            if bucket_hi < bucket_lo:
                bucket_hi = bucket_lo
            offset = random.randint(bucket_lo, bucket_hi)
            closed_date = open_date + timedelta(days=offset)
        else:
            status = "active"  # not enough room after open_date for a valid closed_date

    accounts.append(
        {
            "account_id": aid,
            "customer_id": cid,
            "account_type": account_type,
            "balance": balance,
            "open_date": open_date,
            "status": status,
            "closed_date": closed_date,
        }
    )

accounts_df = pd.DataFrame(accounts)
accounts_df["open_date"] = pd.to_datetime(accounts_df["open_date"])
accounts_df["closed_date"] = pd.to_datetime(accounts_df["closed_date"])

if len(sys.argv) > 1 and sys.argv[1] == "--accounts-only":
    accounts_df.to_csv(f"{OUT_DIR}/accounts.csv", index=False)
    print("accounts.csv columns:", list(accounts_df.columns))
    print(f"accounts.csv rows: {len(accounts_df):,}")
    print(f"closed rows with closed_date populated: {accounts_df.loc[accounts_df.status == 'closed', 'closed_date'].notna().sum():,}")
    sys.exit(0)

# ---------------------------------------------------------------------------
# 3. transactions.csv
# ---------------------------------------------------------------------------
transaction_ids = unique_ids("TXN", N_TRANSACTIONS, n=14)
# transactions mostly hit active/dormant accounts, rarely closed ones
txn_account_pool = accounts_df[accounts_df.status != "closed"]
if txn_account_pool.empty:
    txn_account_pool = accounts_df
txn_accounts = txn_account_pool.sample(n=N_TRANSACTIONS, replace=True).reset_index(drop=True)

txn_types = ["deposit", "withdrawal", "transfer", "pos_payment", "bill_pay"]
txn_type_weights = [0.20, 0.20, 0.15, 0.35, 0.10]

transactions = []
for i, tid in enumerate(transaction_ids):
    acc_row = txn_accounts.iloc[i]
    open_date = acc_row["open_date"]
    start_ts = max(open_date, TODAY - pd.Timedelta(days=365 * 3))
    txn_date = fake.date_time_between(start_date=start_ts.to_pydatetime(), end_date=TODAY.to_pydatetime())
    ttype = random.choices(txn_types, weights=txn_type_weights, k=1)[0]
    if ttype == "deposit":
        amount = round(np.random.lognormal(mean=7.5, sigma=1.0), 2)
    elif ttype == "pos_payment":
        amount = round(np.random.lognormal(mean=4.5, sigma=0.9), 2)
    elif ttype == "bill_pay":
        amount = round(np.random.lognormal(mean=5.5, sigma=0.6), 2)
    else:
        amount = round(np.random.lognormal(mean=6.5, sigma=1.0), 2)
    transactions.append(
        {
            "transaction_id": tid,
            "account_id": acc_row["account_id"],
            "amount": amount,
            "type": ttype,
            "transaction_date": txn_date,
        }
    )

transactions_df = pd.DataFrame(transactions)

# ---------------------------------------------------------------------------
# 4 & 5. loan_applications.csv + loans.csv
# ---------------------------------------------------------------------------
REJECTION_REASONS = [
    "low credit score",
    "high debt-to-income",
    "insufficient income",
    "incomplete documentation",
]

application_ids = unique_ids("APP", N_LOAN_APPLICATIONS)
applicant_customer_ids = np.random.choice(customer_ids, size=N_LOAN_APPLICATIONS, replace=True)

applications = []
funded_loan_rows = []

for app_id, cid in zip(application_ids, applicant_customer_ids):
    cust = customers_df.loc[customers_df.customer_id == cid].iloc[0]
    credit_score = cust["credit_score"]
    cust_created = cust["created_at"]

    applied_date = fake.date_between(start_date=cust_created.date(), end_date="today")
    applied_ts = pd.Timestamp(applied_date)
    days_since_applied = (TODAY - applied_ts).days

    # approval probability rises meaningfully with credit score (logistic curve)
    p_approve = 1 / (1 + np.exp(-(credit_score - 620) / 60))
    p_approve = np.clip(p_approve, 0.03, 0.95)

    still_in_pipeline = days_since_applied < 20 and random.random() < 0.5

    if still_in_pipeline:
        stage = random.choice(["applied", "qualified"])
        rejection_reason = None
        loan_id = None
    else:
        approved_path = random.random() < p_approve
        if approved_path:
            funded = random.random() < 0.9
            if funded:
                stage = "funded"
                rejection_reason = None
                loan_id = gen_id("LON")

                loan_amount = round(np.random.lognormal(mean=10.0, sigma=0.9), 2)
                # weaker credit -> higher interest rate
                base_rate = 18 - (credit_score - 300) / 550 * 13
                interest_rate = round(np.clip(np.random.normal(base_rate, 1.5), 3.5, 22.0), 2)
                tenure_months = random.choice([12, 24, 36, 48, 60])
                start_date = applied_ts + pd.Timedelta(days=random.randint(2, 14))
                if start_date > TODAY:
                    start_date = TODAY

                funded_loan_rows.append(
                    {
                        "loan_id": loan_id,
                        "customer_id": cid,
                        "loan_amount": loan_amount,
                        "interest_rate": interest_rate,
                        "tenure_months": tenure_months,
                        "start_date": start_date,
                        "credit_score": credit_score,  # kept for repayment risk sim, dropped before save
                    }
                )
            else:
                stage = "approved"
                rejection_reason = None
                loan_id = None
        else:
            stage = "rejected"
            loan_id = None
            if credit_score < 580:
                rejection_reason = random.choices(
                    REJECTION_REASONS, weights=[0.55, 0.2, 0.15, 0.1], k=1
                )[0]
            else:
                rejection_reason = random.choices(
                    REJECTION_REASONS, weights=[0.1, 0.35, 0.35, 0.2], k=1
                )[0]

    applications.append(
        {
            "application_id": app_id,
            "customer_id": cid,
            "applied_date": applied_date,
            "stage": stage,
            "rejection_reason": rejection_reason,
            "loan_id": loan_id,
        }
    )

loan_applications_df = pd.DataFrame(applications)
loan_applications_df["applied_date"] = pd.to_datetime(loan_applications_df["applied_date"])

loans_df = pd.DataFrame(funded_loan_rows)
loans_df["start_date"] = pd.to_datetime(loans_df["start_date"])

# --- loan_applications: outcome + last_status_updated_date -----------------
stage_to_outcome = {
    "rejected": "rejected",
    "funded": "funded",
    "applied": "in_progress",
    "qualified": "in_progress",
    "approved": "in_progress",
}
loan_applications_df["outcome"] = loan_applications_df["stage"].map(stage_to_outcome)

loan_start_map = loans_df.set_index("loan_id")["start_date"]
IN_PROGRESS_OFFSET_DAYS = {
    "applied": (0, 5),
    "qualified": (3, 12),
    "approved": (7, 21),
}
REJECTED_OFFSET_DAYS = (3, 25)


def compute_last_status_date(row):
    if row["outcome"] == "funded":
        return loan_start_map.loc[row["loan_id"]]
    if row["outcome"] == "rejected":
        lo, hi = REJECTED_OFFSET_DAYS
    else:
        lo, hi = IN_PROGRESS_OFFSET_DAYS[row["stage"]]
    offset = random.randint(lo, hi)
    d = row["applied_date"] + pd.Timedelta(days=offset)
    return min(d, TODAY)


loan_applications_df["last_status_updated_date"] = loan_applications_df.apply(compute_last_status_date, axis=1)

# integrity checks
_funded = loan_applications_df[loan_applications_df["outcome"] == "funded"]
_check = _funded.merge(loans_df[["loan_id", "start_date"]], on="loan_id")
assert (_check["last_status_updated_date"] == _check["start_date"]).all(), "funded rows must match loans.start_date"
assert (loan_applications_df["last_status_updated_date"] >= loan_applications_df["applied_date"]).all()

# ---------------------------------------------------------------------------
# 6. loan_repayments.csv (monthly installments, amortized, correlated delinquency)
# ---------------------------------------------------------------------------
repayment_rows = []

# percentile-rank risk so the credit_score/loan_amount -> delinquency
# relationship is a real, strong monotonic effect rather than decorative
loans_df["credit_pct_risk"] = 1 - loans_df["credit_score"].rank(pct=True)  # worst score -> ~1
loans_df["amount_pct_risk"] = loans_df["loan_amount"].rank(pct=True)  # largest loan -> ~1
loans_df["risk"] = 0.65 * loans_df["credit_pct_risk"] + 0.35 * loans_df["amount_pct_risk"]

for _, loan in loans_df.iterrows():
    loan_id = loan["loan_id"]
    principal = loan["loan_amount"]
    annual_rate = loan["interest_rate"]
    n = int(loan["tenure_months"])
    start_date = loan["start_date"]
    risk = loan["risk"]

    monthly_rate = annual_rate / 100 / 12
    if monthly_rate > 0:
        installment_amt = principal * monthly_rate * (1 + monthly_rate) ** n / ((1 + monthly_rate) ** n - 1)
    else:
        installment_amt = principal / n
    installment_amt = round(installment_amt, 2)

    # one outcome per loan (not per-installment) so bad behavior stays a
    # meaningful minority instead of compounding across many installments
    p_default = 0.02 + 0.28 * risk ** 1.5       # ~2%-30%, concentrated in high-risk tail
    p_delinquent = 0.03 + 0.20 * risk ** 1.5    # ~3%-23%
    p_clean = max(0.0, 1 - p_default - p_delinquent)
    outcome = random.choices(
        ["defaulted", "delinquent", "clean"], weights=[p_default, p_delinquent, p_clean], k=1
    )[0]

    due_installments = [
        (i, start_date + pd.DateOffset(months=i))
        for i in range(1, n + 1)
        if start_date + pd.DateOffset(months=i) <= TODAY
    ]

    default_start_idx = None
    if outcome == "defaulted" and due_installments:
        default_start_idx = random.randint(0, len(due_installments) - 1)

    for i in range(1, n + 1):
        due_date = start_date + pd.DateOffset(months=i)
        repayment_id = gen_id("REP")

        if due_date > TODAY:
            # (a) not yet due
            repayment_rows.append(
                {
                    "repayment_id": repayment_id,
                    "loan_id": loan_id,
                    "installment_number": i,
                    "due_date": due_date,
                    "due_amount": installment_amt,
                    "paid_date": pd.NaT,
                    "paid_amount": np.nan,
                    "days_late": np.nan,
                }
            )
            continue

        # (b) already due -> simulate actual payment behavior
        due_idx = i - 1  # position within due_installments (same ordering)
        is_last_due = due_date == due_installments[-1][1]

        unpaid = False
        if outcome == "defaulted" and default_start_idx is not None and due_idx >= default_start_idx:
            unpaid = True
        elif outcome == "delinquent" and is_last_due:
            unpaid = True

        if unpaid:
            paid_date = pd.NaT
            paid_amount = np.nan
            days_late = (TODAY - due_date).days
        else:
            # most good-standing payments land exactly on the due date;
            # only a minority drift a few days late
            if random.random() < 0.68 - 0.15 * risk:
                days_late = 0
            else:
                days_late = max(1, int(np.random.exponential(scale=2 + 4 * risk)))
                days_late = min(days_late, 20)
            paid_date = due_date + pd.Timedelta(days=days_late)
            paid_amount = installment_amt

        repayment_rows.append(
            {
                "repayment_id": repayment_id,
                "loan_id": loan_id,
                "installment_number": i,
                "due_date": due_date,
                "due_amount": installment_amt,
                "paid_date": paid_date,
                "paid_amount": paid_amount,
                "days_late": days_late,
            }
        )

loan_repayments_df = pd.DataFrame(repayment_rows)

# ---------------------------------------------------------------------------
# derive loans.loan_status from loan_repayments
# ---------------------------------------------------------------------------
def derive_status(group):
    due_mask = group["due_date"] <= TODAY
    due_group = group[due_mask]
    total_installments = len(group)
    all_due_paid = due_group["paid_date"].notna().all() if len(due_group) else False
    fully_paid = all_due_paid and len(due_group) == total_installments

    if fully_paid:
        return "fully_paid"

    max_days_late = due_group["days_late"].max() if len(due_group) else np.nan
    if pd.notna(max_days_late) and max_days_late >= 91:
        return "defaulted"
    if pd.notna(max_days_late) and max_days_late >= 31:
        return "delinquent"
    return "active"


loan_status = loan_repayments_df.groupby("loan_id").apply(derive_status)
loans_df["loan_status"] = loans_df["loan_id"].map(loan_status)
loans_df = loans_df.drop(columns=["credit_score", "credit_pct_risk", "amount_pct_risk", "risk"])

loan_applications_df["applied_date"] = loan_applications_df["applied_date"].dt.date
loan_applications_df["last_status_updated_date"] = loan_applications_df["last_status_updated_date"].dt.date

# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------
customers_df.to_csv(f"{OUT_DIR}/customers.csv", index=False)
accounts_df.to_csv(f"{OUT_DIR}/accounts.csv", index=False)
transactions_df.to_csv(f"{OUT_DIR}/transactions.csv", index=False)
loans_df.to_csv(f"{OUT_DIR}/loans.csv", index=False)
loan_applications_df.to_csv(f"{OUT_DIR}/loan_applications.csv", index=False)
loan_repayments_df.to_csv(f"{OUT_DIR}/loan_repayments.csv", index=False)

# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------
print("=== ROW COUNTS ===")
print(f"customers.csv:         {len(customers_df):,}")
print(f"accounts.csv:          {len(accounts_df):,}")
print(f"transactions.csv:      {len(transactions_df):,}")
print(f"loans.csv:             {len(loans_df):,}")
print(f"loan_applications.csv: {len(loan_applications_df):,}")
print(f"loan_repayments.csv:   {len(loan_repayments_df):,}")

print("\n=== SANITY CHECKS ===")
total_apps = len(loan_applications_df)
funded_apps = (loan_applications_df["stage"] == "funded").sum()
rejected_apps = (loan_applications_df["stage"] == "rejected").sum()
resolved_apps = funded_apps + rejected_apps + (loan_applications_df["stage"] == "approved").sum()
print(f"Overall funding rate (funded / total applications): {funded_apps/total_apps:.1%}")
print(f"Overall rejection rate (rejected / total applications): {rejected_apps/total_apps:.1%}")
print(f"Approval rate among resolved applications (funded+approved / (funded+approved+rejected)): "
      f"{(total_apps - rejected_apps - (loan_applications_df['stage'].isin(['applied','qualified'])).sum()) / max(resolved_apps,1):.1%}")

status_counts = loans_df["loan_status"].value_counts(normalize=True)
print("\nLoan status distribution:")
print(status_counts.round(3))

npl_rate = loans_df["loan_status"].isin(["delinquent", "defaulted"]).mean()
print(f"\nNPL-ish rate (delinquent+defaulted / all funded loans): {npl_rate:.1%}")

# correlation sanity: lower credit score should associate with worse loan status
loans_with_score = loans_df.merge(customers_df[["customer_id", "credit_score"]], on="customer_id")
print("\nMean credit_score by loan_status (should be lower for defaulted/delinquent):")
print(loans_with_score.groupby("loan_status")["credit_score"].mean().round(1))
