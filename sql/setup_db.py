"""
setup_db.py — Build SQLite database from raw CSV with derived columns.
Run from project root: python sql/setup_db.py
"""

import pandas as pd
import sqlite3
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "olist_customers_dataset.csv")
DB_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "olist.db")

# --- Region mapping ---
REGION_MAP = {
    "SP": "Southeast", "RJ": "Southeast", "MG": "Southeast", "ES": "Southeast",
    "RS": "South",     "PR": "South",     "SC": "South",
    "BA": "Northeast", "PE": "Northeast", "CE": "Northeast", "MA": "Northeast",
    "PB": "Northeast", "PI": "Northeast", "RN": "Northeast", "AL": "Northeast",
    "SE": "Northeast",
    "DF": "Central-West", "GO": "Central-West", "MT": "Central-West", "MS": "Central-West",
    "PA": "North",    "AM": "North",     "RO": "North",    "TO": "North",
    "AC": "North",    "AP": "North",     "RR": "North",
}

STATE_MATURITY = {
    "SP": 5, "RJ": 5, "MG": 4, "RS": 4, "PR": 4,
    "SC": 3, "BA": 3, "DF": 3, "ES": 3, "GO": 3,
    "PE": 2, "CE": 2, "PA": 2, "MT": 2, "MA": 2,
    "MS": 2, "PB": 1, "PI": 1, "RN": 1, "AL": 1,
    "SE": 1, "TO": 1, "RO": 1, "AM": 1, "AC": 1, "AP": 1, "RR": 1,
}

TIER1 = {"sao paulo", "rio de janeiro", "belo horizonte", "brasilia",
         "curitiba", "porto alegre", "salvador", "fortaleza", "manaus", "recife"}
TIER2 = {"campinas", "guarulhos", "sao bernardo do campo", "niteroi",
         "goiania", "belem", "santos", "osasco", "maceio", "teresina"}

def city_tier(city):
    c = str(city).lower()
    if c in TIER1: return 3
    if c in TIER2: return 2
    return 1


def main():
    print(f"Loading: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"  Rows: {len(df):,}  |  Columns: {df.shape[1]}")

    # Derived columns
    df["region"]         = df["customer_state"].map(REGION_MAP).fillna("Unknown")
    df["state_maturity"] = df["customer_state"].map(STATE_MATURITY).fillna(1).astype(int)
    df["city_tier"]      = df["customer_city"].apply(city_tier)

    # Write to SQLite
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("customers", conn, index=False, if_exists="replace")

    # Create indexes for faster queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_state     ON customers(customer_state)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_unique_id ON customers(customer_unique_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_region    ON customers(region)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_city_tier ON customers(city_tier)")
    conn.commit()

    # Verify
    row_count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    cols      = [r[1] for r in conn.execute("PRAGMA table_info(customers)")]
    conn.close()

    print(f"\nDatabase created: {DB_PATH}")
    print(f"  Rows in DB : {row_count:,}")
    print(f"  Columns    : {cols}")
    print("\nReady — open DBeaver / TablePlus or run queries with:")
    print("  sqlite3 data/olist.db < sql/business_queries.sql")
    print("  python sql/run_query.py")


if __name__ == "__main__":
    main()
