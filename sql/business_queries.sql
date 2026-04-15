-- ============================================================
--  OLIST E-COMMERCE — SQL BUSINESS INTELLIGENCE QUERIES
--  Database: SQLite (olist.db)
--  Run setup via: python sql/setup_db.py
-- ============================================================

-- ============================================================
-- SECTION 1: DATABASE SETUP REFERENCE
-- ============================================================
-- Table: customers
--   customer_id           TEXT  PRIMARY KEY
--   customer_unique_id    TEXT
--   customer_zip_code_prefix INTEGER
--   customer_city         TEXT
--   customer_state        TEXT
--   region                TEXT   (derived)
--   city_tier             INTEGER (1/2/3 derived)
--   state_maturity        INTEGER (1-5 derived)

-- ============================================================
-- SECTION 2: FOUNDATIONAL METRICS
-- ============================================================

-- Q1: Total orders, unique customers, and overall scale
SELECT
    COUNT(*)                                        AS total_orders,
    COUNT(DISTINCT customer_unique_id)              AS unique_customers,
    COUNT(*) - COUNT(DISTINCT customer_unique_id)   AS repeat_orders,
    COUNT(DISTINCT customer_state)                  AS states_covered,
    COUNT(DISTINCT customer_city)                   AS cities_covered,
    ROUND(
        (COUNT(*) - COUNT(DISTINCT customer_unique_id)) * 1.0
        / COUNT(DISTINCT customer_unique_id) * 100, 2
    )                                               AS repeat_rate_pct
FROM customers;


-- Q2: Average and max orders per customer
SELECT
    ROUND(AVG(order_count), 3)   AS avg_orders_per_customer,
    MAX(order_count)             AS max_orders_by_one_customer,
    MIN(order_count)             AS min_orders
FROM (
    SELECT customer_unique_id, COUNT(*) AS order_count
    FROM customers
    GROUP BY customer_unique_id
);


-- ============================================================
-- SECTION 3: GEOGRAPHIC ANALYSIS
-- ============================================================

-- Q3: Orders and market share by state (full table)
SELECT
    customer_state                              AS state,
    COUNT(*)                                    AS total_orders,
    COUNT(DISTINCT customer_unique_id)          AS unique_customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS order_share_pct,
    ROUND(
        SUM(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) * 100.0
        / SUM(COUNT(*)) OVER (), 2
    )                                           AS cumulative_pct
FROM customers
GROUP BY customer_state
ORDER BY total_orders DESC;


-- Q4: Regional breakdown with key metrics
SELECT
    region,
    COUNT(*)                            AS total_orders,
    COUNT(DISTINCT customer_unique_id)  AS unique_customers,
    COUNT(DISTINCT customer_state)      AS states_in_region,
    COUNT(DISTINCT customer_city)       AS cities_in_region,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS order_share_pct
FROM customers
GROUP BY region
ORDER BY total_orders DESC;


-- Q5: Top 20 cities by order volume
SELECT
    customer_city                       AS city,
    customer_state                      AS state,
    region,
    city_tier,
    COUNT(*)                            AS orders,
    COUNT(DISTINCT customer_unique_id)  AS unique_customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 3) AS share_pct
FROM customers
GROUP BY customer_city
ORDER BY orders DESC
LIMIT 20;


-- Q6: Geographic concentration (Pareto analysis)
WITH state_ranked AS (
    SELECT
        customer_state,
        COUNT(*) AS orders,
        ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rnk
    FROM customers
    GROUP BY customer_state
),
cumulative AS (
    SELECT
        customer_state,
        orders,
        rnk,
        SUM(orders) OVER (ORDER BY rnk) AS running_total,
        SUM(orders) OVER () AS grand_total
    FROM state_ranked
)
SELECT
    customer_state,
    orders,
    rnk,
    ROUND(running_total * 100.0 / grand_total, 1) AS cumulative_pct
FROM cumulative
ORDER BY rnk;


-- ============================================================
-- SECTION 4: CUSTOMER SEGMENTATION
-- ============================================================

-- Q7: Customer segmentation by purchase frequency
SELECT
    CASE
        WHEN order_count = 1 THEN '1_New'
        WHEN order_count = 2 THEN '2_Returning'
        WHEN order_count BETWEEN 3 AND 4 THEN '3_Loyal'
        ELSE '4_Champion'
    END                              AS segment,
    COUNT(*)                         AS customers,
    SUM(order_count)                 AS total_orders,
    ROUND(AVG(order_count), 2)       AS avg_orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS customer_pct
FROM (
    SELECT customer_unique_id, COUNT(*) AS order_count
    FROM customers
    GROUP BY customer_unique_id
)
GROUP BY segment
ORDER BY segment;


-- Q8: Retention funnel — step-by-step drop-off
WITH freq AS (
    SELECT customer_unique_id, COUNT(*) AS n
    FROM customers
    GROUP BY customer_unique_id
)
SELECT
    '1+ orders' AS cohort, COUNT(*) AS customers FROM freq WHERE n >= 1
UNION ALL
SELECT '2+ orders', COUNT(*) FROM freq WHERE n >= 2
UNION ALL
SELECT '3+ orders', COUNT(*) FROM freq WHERE n >= 3
UNION ALL
SELECT '4+ orders', COUNT(*) FROM freq WHERE n >= 4
UNION ALL
SELECT '5+ orders', COUNT(*) FROM freq WHERE n >= 5;


-- Q9: Repeat buyer rate by state (which states drive loyalty?)
SELECT
    customer_state                              AS state,
    COUNT(DISTINCT customer_unique_id)          AS total_customers,
    SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) AS repeat_buyers,
    ROUND(
        SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) * 100.0
        / COUNT(DISTINCT customer_unique_id), 2
    )                                           AS repeat_rate_pct
FROM (
    SELECT customer_unique_id, customer_state, COUNT(*) AS order_count
    FROM customers
    GROUP BY customer_unique_id, customer_state
)
GROUP BY customer_state
HAVING COUNT(DISTINCT customer_unique_id) > 100
ORDER BY repeat_rate_pct DESC;


-- Q10: Repeat buyer rate by region
SELECT
    c.region,
    COUNT(DISTINCT c.customer_unique_id)        AS total_customers,
    SUM(CASE WHEN f.order_count >= 2 THEN 1 ELSE 0 END) AS repeat_buyers,
    ROUND(
        SUM(CASE WHEN f.order_count >= 2 THEN 1 ELSE 0 END) * 100.0
        / COUNT(DISTINCT c.customer_unique_id), 2
    )                                           AS repeat_rate_pct
FROM customers c
JOIN (
    SELECT customer_unique_id, COUNT(*) AS order_count
    FROM customers
    GROUP BY customer_unique_id
) f ON c.customer_unique_id = f.customer_unique_id
GROUP BY c.region
ORDER BY repeat_rate_pct DESC;


-- ============================================================
-- SECTION 5: MARKET OPPORTUNITY ANALYSIS
-- ============================================================

-- Q11: Underpenetrated states (low order share, high potential)
WITH national AS (
    SELECT COUNT(*) AS total FROM customers
)
SELECT
    c.customer_state            AS state,
    COUNT(*)                    AS orders,
    ROUND(COUNT(*) * 100.0 / n.total, 3) AS share_pct,
    c.state_maturity,
    COUNT(DISTINCT c.customer_city) AS cities_with_orders
FROM customers c, national n
GROUP BY c.customer_state
HAVING share_pct < 1.0
ORDER BY c.state_maturity DESC, share_pct DESC;


-- Q12: City-tier order distribution (Tier 1 vs Tier 2 vs Tier 3 cities)
SELECT
    city_tier,
    CASE city_tier
        WHEN 3 THEN 'Tier 1 — Major metros'
        WHEN 2 THEN 'Tier 2 — Secondary cities'
        ELSE 'Tier 3 — Smaller towns'
    END                                         AS tier_label,
    COUNT(*)                                    AS orders,
    COUNT(DISTINCT customer_unique_id)          AS unique_customers,
    COUNT(DISTINCT customer_city)               AS cities,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS order_share_pct
FROM customers
GROUP BY city_tier
ORDER BY city_tier DESC;


-- ============================================================
-- SECTION 6: ADVANCED ANALYTICS
-- ============================================================

-- Q13: Customer concentration risk — top N% of states driving X% of orders
WITH ranked AS (
    SELECT
        customer_state,
        COUNT(*) AS orders,
        RANK() OVER (ORDER BY COUNT(*) DESC) AS rnk
    FROM customers
    GROUP BY customer_state
),
total AS (SELECT SUM(orders) AS grand_total FROM ranked)
SELECT
    rnk                     AS state_rank,
    customer_state,
    orders,
    ROUND(orders * 100.0 / t.grand_total, 2) AS share_pct,
    ROUND(SUM(orders) OVER (ORDER BY rnk) * 100.0 / t.grand_total, 2) AS cumulative_pct,
    CASE
        WHEN SUM(orders) OVER (ORDER BY rnk) * 100.0 / t.grand_total <= 80 THEN 'Core 80%'
        ELSE 'Long Tail'
    END AS market_tier
FROM ranked r, total t
ORDER BY rnk;


-- Q14: Zip code prefix analysis — density of customers in same area
SELECT
    customer_zip_code_prefix,
    customer_state,
    COUNT(*)                                    AS orders,
    COUNT(DISTINCT customer_unique_id)          AS unique_customers,
    COUNT(DISTINCT customer_city)               AS cities
FROM customers
GROUP BY customer_zip_code_prefix
HAVING orders > 10
ORDER BY orders DESC
LIMIT 25;


-- Q15: Cross-state champion buyers (highest order counts)
SELECT
    customer_unique_id,
    COUNT(*)                AS total_orders,
    customer_state          AS home_state,
    customer_city           AS home_city,
    region,
    city_tier,
    state_maturity
FROM customers
GROUP BY customer_unique_id
HAVING total_orders >= 5
ORDER BY total_orders DESC;


-- ============================================================
-- SECTION 7: BUSINESS RECOMMENDATION QUERIES
-- ============================================================

-- Q16: States with growth potential
--      (high state maturity, low current order share)
WITH state_stats AS (
    SELECT
        customer_state,
        state_maturity,
        COUNT(*) AS orders,
        COUNT(DISTINCT customer_unique_id) AS customers,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 3) AS share_pct
    FROM customers
    GROUP BY customer_state
)
SELECT
    customer_state,
    state_maturity,
    orders,
    share_pct,
    CASE
        WHEN state_maturity >= 4 AND share_pct < 5.0 THEN 'HIGH priority expansion'
        WHEN state_maturity = 3 AND share_pct < 2.0 THEN 'MEDIUM priority expansion'
        ELSE 'Monitor'
    END AS growth_recommendation
FROM state_stats
ORDER BY state_maturity DESC, share_pct ASC;


-- Q17: Retention lever analysis — repeat buyers by city tier
SELECT
    city_tier,
    COUNT(DISTINCT customer_unique_id)          AS customers,
    SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) AS repeat_buyers,
    ROUND(
        SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) * 100.0
        / COUNT(DISTINCT customer_unique_id), 2
    )                                           AS repeat_rate_pct
FROM (
    SELECT
        c.customer_unique_id,
        c.city_tier,
        COUNT(*) AS order_count
    FROM customers c
    GROUP BY c.customer_unique_id, c.city_tier
)
GROUP BY city_tier
ORDER BY city_tier DESC;
