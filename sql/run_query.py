"""
run_query.py — Execute any SQL query against olist.db and display results.
Usage: python sql/run_query.py
"""

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "olist.db")


QUERIES = {
    "Scale Overview": """
        SELECT
            COUNT(*) AS total_orders,
            COUNT(DISTINCT customer_unique_id) AS unique_customers,
            COUNT(DISTINCT customer_state) AS states,
            COUNT(DISTINCT customer_city) AS cities,
            ROUND((COUNT(*) - COUNT(DISTINCT customer_unique_id)) * 100.0
                  / COUNT(DISTINCT customer_unique_id), 2) AS repeat_rate_pct
        FROM customers
    """,
    "Top 10 States": """
        SELECT customer_state AS state,
               COUNT(*) AS orders,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS share_pct
        FROM customers
        GROUP BY state ORDER BY orders DESC LIMIT 10
    """,
    "Customer Segments": """
        SELECT
            CASE WHEN order_count=1 THEN 'New'
                 WHEN order_count=2 THEN 'Returning'
                 WHEN order_count<=4 THEN 'Loyal'
                 ELSE 'Champion' END AS segment,
            COUNT(*) AS customers,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
        FROM (SELECT customer_unique_id, COUNT(*) AS order_count
              FROM customers GROUP BY customer_unique_id)
        GROUP BY segment ORDER BY customers DESC
    """,
    "Regional Breakdown": """
        SELECT region,
               COUNT(*) AS orders,
               COUNT(DISTINCT customer_unique_id) AS customers,
               COUNT(DISTINCT customer_city) AS cities,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS share_pct
        FROM customers
        GROUP BY region ORDER BY orders DESC
    """,
    "Retention Funnel": """
        WITH freq AS (
            SELECT customer_unique_id, COUNT(*) AS n
            FROM customers GROUP BY customer_unique_id
        )
        SELECT '1+ orders' AS cohort, COUNT(*) AS customers,
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM freq),2) AS pct FROM freq WHERE n>=1
        UNION ALL
        SELECT '2+ orders', COUNT(*),
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM freq),2) FROM freq WHERE n>=2
        UNION ALL
        SELECT '3+ orders', COUNT(*),
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM freq),2) FROM freq WHERE n>=3
        UNION ALL
        SELECT '4+ orders', COUNT(*),
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM freq),2) FROM freq WHERE n>=4
        UNION ALL
        SELECT '5+ orders', COUNT(*),
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM freq),2) FROM freq WHERE n>=5
    """,
}


def run_all():
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        print("Run: python sql/setup_db.py first")
        return

    conn = sqlite3.connect(DB_PATH)
    print("=" * 60)
    print("OLIST — SQL QUERY RESULTS")
    print("=" * 60)

    for name, sql in QUERIES.items():
        print(f"\n{'─' * 60}")
        print(f"  {name}")
        print(f"{'─' * 60}")
        df = pd.read_sql_query(sql, conn)
        print(df.to_string(index=False))

    conn.close()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_all()
