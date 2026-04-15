# Olist E-Commerce — Customer Analytics

> End-to-end data analyst portfolio project: geographic intelligence, customer segmentation, RFM scoring, retention analysis, and a live Streamlit dashboard — built on the Brazilian Olist e-commerce dataset.

---

## Project Overview

This project answers five core business questions using 99,441 customer orders from the Olist marketplace:

| Question | Method | Output |
|---|---|---|
| Where are customers located? | State/city aggregation, Pareto analysis | Charts + choropleth |
| Who are our most valuable customers? | RFM proxy scoring | Segment labels per customer |
| What's the retention problem? | Cohort frequency funnel | Drop-off waterfall |
| Which regions are underserved? | Penetration + maturity scoring | Expansion heatmap |
| What's the churn risk profile? | Rule-based risk classification | Risk tier per customer |

---

## Dataset

**Source:** [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle)

**File used:** `olist_customers_dataset.csv`

| Column | Type | Description |
|---|---|---|
| `customer_id` | string | Unique per order (maps to orders table) |
| `customer_unique_id` | string | Unique per customer (identifies repeat buyers) |
| `customer_zip_code_prefix` | int | 5-digit zip prefix |
| `customer_city` | string | City name (lowercase) |
| `customer_state` | string | 2-letter state code (27 states) |

**Scale:** 99,441 rows · 5 columns · ~10 MB

---

## Key Findings

### 1. Geographic Concentration
- **São Paulo state** drives **42.0%** of all orders — a single state dominates the platform
- **Southeast region** (SP + RJ + MG + ES) accounts for **68.6%** of orders
- **Top 5 states** (SP, RJ, MG, RS, PR) = **79.4%** of total volume → classic Pareto 80/20

### 2. Retention Crisis
- **96.9%** of customers placed only **1 order** — acquisition machine, not a loyalty engine
- Repeat rate: **3.1%** (industry benchmark for healthy e-commerce: 25–35%)
- A 1 percentage point improvement in repeat rate = ~960 more loyal customers

### 3. Untapped Markets
- **North + Northeast** = 18 states, ~210M population → only **14%** of orders
- States like AM, AP, RR each contribute **<0.2%** despite significant urban populations
- Logistics infrastructure improvement could unlock this market

### 4. City Dependency
- **São Paulo city** alone = **15,540 orders (15.6%)** — concentration risk
- **4,119 unique cities** served nationally — distribution breadth is a strength
- Tier 1 cities (10 cities) generate disproportionate order share

### 5. RFM Segmentation
- **High Value** customers cluster in Tier 1 cities + mature states
- **Low Value** customers concentrated in low-maturity northern states
- RFM score range: 1.0–4.35 | Mean: 2.1 | Median: 1.95

---

## Analysis Deep-Dives

### RFM Scoring Methodology

Since this dataset contains no transaction dates or revenue, a **geography-adjusted RFM proxy** was engineered:

| Dimension | Proxy | Weight | Score Range |
|---|---|---|---|
| **Recency** | State e-commerce maturity rank (SP=5, RR=1) | 30% | 1–5 |
| **Frequency** | Actual repeat order count (capped at 5) | 50% | 1–5 |
| **Monetary** | City tier classification (Tier 1/2/3) | 20% | 1–3 |

```python
rfm_score = (state_maturity × 0.30) + (min(order_count, 5) × 0.50) + (city_tier × 0.20)
```

**Segments:**
- `High Value`: score ≥ 4.0
- `Mid Value`: 2.5 ≤ score < 4.0
- `Low Value`: score < 2.5

### Churn Risk Classification

```python
if order_count >= 3:       → Low Risk
elif order_count == 2:     → Medium Risk
elif rfm_score >= 2.5:     → Medium Risk
else:                      → High Risk
```

### SQL: 17 Business Queries

Covers: scale overview, state/city rankings, Pareto analysis, regional breakdown, customer segmentation, retention funnel, repeat rate by region/state, underpenetrated markets, city-tier analysis, churn risk, concentration risk, champion buyers.

---

## Tech Stack

| Tool | Version | Use |
|---|---|---|
| Python | 3.10+ | Core language |
| Pandas | 2.0+ | Data manipulation |
| NumPy | 1.24+ | Numerical ops |
| Matplotlib | 3.7+ | Static charts |
| Seaborn | 0.12+ | Statistical plots |
| Streamlit | 1.32+ | Interactive dashboard |
| SQLite | built-in | SQL analytics layer |

---

## Business Recommendations

Based on findings, three high-impact actions for the Olist product team:

**1. Launch a retention campaign targeting first-time buyers**
- Trigger: 7 days post-first-order
- Target: 93,099 one-time buyers
- Goal: Lift repeat rate from 3.1% → 6% (+2,880 loyal customers)

**2. Expand logistics partnerships in Northeast states**
- Target states: BA, PE, CE, MA (combined: 7.1% of orders from 200M+ population)
- Expected impact: Capture 3–5% more order share within 12 months

**3. Reduce São Paulo dependency**
- Current: 42% of orders from 1 state
- Lever: Seller incentive programs for RS, PR, SC, GO merchants
- Goal: Reduce SP concentration to <35%

---
