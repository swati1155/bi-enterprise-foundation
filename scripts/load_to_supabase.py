"""
Load the 6 synthetic_dataset CSVs into Supabase Postgres.
Drops and recreates each table, infers column types from the data, bulk-loads via COPY.
"""
import io
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "synthetic_dataset"

TABLES = {
    "customers": ("customers.csv", "customer_id"),
    "accounts": ("accounts.csv", "account_id"),
    "transactions": ("transactions.csv", "transaction_id"),
    "loans": ("loans.csv", "loan_id"),
    "loan_applications": ("loan_applications.csv", "application_id"),
    "loan_repayments": ("loan_repayments.csv", "repayment_id"),
}


def infer_pg_type(colname, series):
    if colname.endswith("_date") or colname.endswith("_at"):
        parsed = pd.to_datetime(series, errors="coerce")
        non_null = parsed.dropna()
        has_time = len(non_null) and (non_null.dt.time != pd.Timestamp("00:00:00").time()).any()
        return "TIMESTAMP" if has_time else "DATE"
    if pd.api.types.is_numeric_dtype(series):
        return "NUMERIC"
    return "TEXT"


def load_table(cur, table, csv_name, pk_col):
    df = pd.read_csv(f"{DATA_DIR}/{csv_name}")

    col_types = {col: infer_pg_type(col, df[col]) for col in df.columns}
    col_defs = ", ".join(f'"{col}" {col_types[col]}' for col in df.columns)

    cur.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
    cur.execute(f'CREATE TABLE "{table}" ({col_defs}, PRIMARY KEY ("{pk_col}"));')

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="")
    buf.seek(0)
    cur.copy_expert(f'COPY "{table}" FROM STDIN WITH (FORMAT csv, NULL \'\')', buf)

    cur.execute(f'SELECT COUNT(*) FROM "{table}";')
    return cur.fetchone()[0]


def main():
    tables = TABLES
    if len(sys.argv) > 1:
        requested = sys.argv[1:]
        tables = {name: TABLES[name] for name in requested if name in TABLES}

    conn = psycopg2.connect(
        host=os.environ["SUPABASE_HOST"],
        port=os.environ["SUPABASE_PORT"],
        dbname=os.environ["SUPABASE_DB"],
        user=os.environ["SUPABASE_USER"],
        password=os.environ["SUPABASE_PASSWORD"],
    )
    conn.autocommit = False

    counts = {}
    try:
        with conn.cursor() as cur:
            for table, (csv_name, pk_col) in tables.items():
                counts[table] = load_table(cur, table, csv_name, pk_col)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("=== ROW COUNTS (Supabase) ===")
    for table, count in counts.items():
        print(f"{table}: {count:,}")


if __name__ == "__main__":
    main()
