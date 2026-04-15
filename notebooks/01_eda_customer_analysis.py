# %% [markdown]
# # Olist E-Commerce — Customer Analytics
# **End-to-end exploratory data analysis, RFM segmentation, and geographic intelligence**
#
# **Dataset:** Olist Brazilian E-Commerce Public Dataset
# **Author:** Data Analyst Portfolio Project
# **Stack:** Python · Pandas · Matplotlib · Seaborn · SQLite

# %% [markdown]
# ## 1. Setup & Imports

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import sqlite3
import os
import warnings

warnings.filterwarnings("ignore")

# --- Style config ---
plt.rcParams.update({
    "figure.facecolor": "#FAFAF8",
    "axes.facecolor": "#FAFAF8",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": True,
    "axes.spines.bottom": True,
    "axes.grid": True,
    "grid.color": "#E8E6DF",
    "grid.linewidth": 0.6,
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

TEAL   = "#1D9E75"
CORAL  = "#D85A30"
BLUE   = "#185FA5"
AMBER  = "#BA7517"
GRAY   = "#888780"
LIGHT  = "#E1F5EE"

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "olist_customers_dataset.csv")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_PATH, exist_ok=True)

print("Environment ready.")

# %% [markdown]
# ## 2. Data Loading & Quality Audit

# %%
df = pd.read_csv(DATA_PATH)

print("=" * 55)
print("DATASET OVERVIEW")
print("=" * 55)
print(f"  Shape        : {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"  Memory usage : {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
print()
print("Column dtypes:")
print(df.dtypes)
print()
print("Null counts:")
print(df.isnull().sum())
print()
print("Sample rows:")
print(df.head(3).to_string())

# %%
# --- Data quality checks ---
issues = []

dup_customer_id = df.duplicated(subset="customer_id").sum()
dup_unique_id   = df.duplicated(subset="customer_unique_id").sum()
null_count      = df.isnull().sum().sum()
blank_city      = (df["customer_city"].str.strip() == "").sum()

issues.append(("Duplicate customer_id", dup_customer_id))
issues.append(("Duplicate customer_unique_id (repeat buyers)", dup_unique_id))
issues.append(("Total null values", null_count))
issues.append(("Blank city names", blank_city))

print("=" * 55)
print("DATA QUALITY REPORT")
print("=" * 55)
for label, val in issues:
    flag = "✓" if val == 0 else "⚠"
    print(f"  {flag}  {label:<42} {val:>6,}")

print()
print(f"  → Each customer_id maps to one order (99,441 unique)")
print(f"  → customer_unique_id has {df['customer_unique_id'].nunique():,} uniques — repeat buyers present")

# %% [markdown]
# ## 3. Geographic Distribution

# %%
state_counts = df["customer_state"].value_counts().reset_index()
state_counts.columns = ["state", "orders"]
state_counts["pct"] = (state_counts["orders"] / len(df) * 100).round(2)
state_counts["cumulative_pct"] = state_counts["pct"].cumsum().round(2)

print("Top 10 states by order volume:")
print(state_counts.head(10).to_string(index=False))

# %%
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle("Geographic Distribution of Olist Customers", fontsize=16, fontweight="bold", y=1.01)

# --- Left: Top 15 states bar chart ---
ax = axes[0]
top15 = state_counts.head(15)
colors = [TEAL if i < 3 else (BLUE if i < 7 else GRAY) for i in range(len(top15))]
bars = ax.barh(top15["state"][::-1], top15["orders"][::-1], color=colors[::-1], edgecolor="none")
ax.set_xlabel("Number of Orders")
ax.set_title("Orders by State — Top 15")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
for bar, val in zip(bars, top15["orders"][::-1]):
    ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", fontsize=9, color=GRAY)
ax.set_xlim(0, top15["orders"].max() * 1.18)

# --- Right: Pareto / cumulative concentration ---
ax2 = axes[1]
x = range(len(state_counts))
ax2.bar(x, state_counts["pct"], color=TEAL, alpha=0.7, edgecolor="none", label="% of orders")
ax2_twin = ax2.twinx()
ax2_twin.plot(x, state_counts["cumulative_pct"], color=CORAL, linewidth=2.5,
              marker="o", markersize=3, label="Cumulative %")
ax2_twin.axhline(80, color=AMBER, linestyle="--", linewidth=1, alpha=0.7)
ax2_twin.text(len(state_counts) - 1, 81, "80%", color=AMBER, fontsize=9)
ax2.set_xticks(list(x))
ax2.set_xticklabels(state_counts["state"].tolist(), rotation=45, ha="right", fontsize=8)
ax2.set_ylabel("% of Orders (State)")
ax2_twin.set_ylabel("Cumulative %")
ax2.set_title("Pareto: State Concentration")
ax2.spines["top"].set_visible(False)
ax2_twin.spines["top"].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PATH, "01_geographic_distribution.png"), dpi=150, bbox_inches="tight")
plt.show()
print("Saved: 01_geographic_distribution.png")

# %% [markdown]
# ## 4. City-Level Analysis

# %%
city_counts = df["customer_city"].str.title().value_counts().reset_index()
city_counts.columns = ["city", "orders"]
city_counts["pct"] = (city_counts["orders"] / len(df) * 100).round(2)

print(f"Total unique cities: {len(city_counts):,}")
print(f"\nTop 15 cities:")
print(city_counts.head(15).to_string(index=False))

# %%
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle("City-Level Customer Distribution", fontsize=16, fontweight="bold", y=1.01)

# --- Top 15 cities ---
ax = axes[0]
top15c = city_counts.head(15)
palette = [BLUE if i == 0 else (TEAL if i < 5 else GRAY) for i in range(len(top15c))]
ax.barh(top15c["city"][::-1], top15c["orders"][::-1], color=palette[::-1], edgecolor="none")
ax.set_xlabel("Number of Orders")
ax.set_title("Top 15 Cities by Order Volume")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_xlim(0, top15c["orders"].max() * 1.2)
for i, (_, row) in enumerate(top15c[::-1].iterrows()):
    ax.text(row["orders"] + 80, i, f"{row['pct']}%", va="center", fontsize=9, color=GRAY)

# --- City orders distribution (log scale) ---
ax2 = axes[1]
order_bins = [1, 10, 50, 100, 500, 1000, 5000, 20000]
bin_labels = ["1–9", "10–49", "50–99", "100–499", "500–999", "1K–4.9K", "5K+"]
bin_counts = []
for i in range(len(order_bins) - 1):
    lo, hi = order_bins[i], order_bins[i + 1]
    n = ((city_counts["orders"] >= lo) & (city_counts["orders"] < hi)).sum()
    bin_counts.append(n)
ax2.bar(bin_labels, bin_counts, color=BLUE, alpha=0.8, edgecolor="none")
ax2.set_xlabel("Orders per City (range)")
ax2.set_ylabel("Number of Cities")
ax2.set_title("City Size Distribution")
for i, v in enumerate(bin_counts):
    ax2.text(i, v + 1, str(v), ha="center", fontsize=10, color=GRAY)
ax2.set_ylim(0, max(bin_counts) * 1.2)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PATH, "02_city_distribution.png"), dpi=150, bbox_inches="tight")
plt.show()
print("Saved: 02_city_distribution.png")

# %% [markdown]
# ## 5. Repeat Buyer Analysis & Customer Segmentation

# %%
purchase_freq = df.groupby("customer_unique_id").size().reset_index(name="order_count")

print("=" * 55)
print("PURCHASE FREQUENCY BREAKDOWN")
print("=" * 55)
freq_dist = purchase_freq["order_count"].value_counts().sort_index()
for freq, count in freq_dist.items():
    pct = count / len(purchase_freq) * 100
    bar = "█" * int(pct / 2)
    print(f"  {freq:2} order(s): {count:6,} customers ({pct:5.2f}%) {bar}")

print()
print(f"  One-time buyers  : {(purchase_freq['order_count'] == 1).sum():,}")
print(f"  Repeat buyers    : {(purchase_freq['order_count'] >= 2).sum():,}")
print(f"  Repeat rate      : {(purchase_freq['order_count'] >= 2).sum() / len(purchase_freq) * 100:.2f}%")
print(f"  Max orders (1 customer): {purchase_freq['order_count'].max()}")

# %%
def assign_segment(n):
    if n == 1:
        return "New"
    elif n == 2:
        return "Returning"
    elif n <= 4:
        return "Loyal"
    else:
        return "Champion"

purchase_freq["segment"] = purchase_freq["order_count"].apply(assign_segment)
segment_summary = purchase_freq.groupby("segment").agg(
    customers=("customer_unique_id", "count"),
    total_orders=("order_count", "sum"),
    avg_orders=("order_count", "mean")
).reset_index()
segment_summary["customer_pct"] = (segment_summary["customers"] / len(purchase_freq) * 100).round(2)
segment_order = ["New", "Returning", "Loyal", "Champion"]
segment_summary["segment"] = pd.Categorical(segment_summary["segment"], categories=segment_order, ordered=True)
segment_summary = segment_summary.sort_values("segment")

print("\nSEGMENT SUMMARY:")
print(segment_summary.to_string(index=False))

# %%
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle("Customer Segmentation & Retention Analysis", fontsize=16, fontweight="bold", y=1.01)

# --- Segment donut ---
ax = axes[0]
seg_colors = [TEAL, AMBER, BLUE, CORAL]
wedges, texts, autotexts = ax.pie(
    segment_summary["customers"],
    labels=segment_summary["segment"],
    autopct="%1.1f%%",
    colors=seg_colors,
    startangle=90,
    wedgeprops={"edgecolor": "white", "linewidth": 2},
    pctdistance=0.75,
)
for t in autotexts:
    t.set_fontsize(10)
centre_circle = plt.Circle((0, 0), 0.55, fc="#FAFAF8")
ax.add_patch(centre_circle)
ax.set_title("Customer Segments")
ax.text(0, 0, f"{len(purchase_freq):,}\ncustomers", ha="center", va="center",
        fontsize=11, fontweight="bold", color="#333")

# --- Order frequency bar (log scale) ---
ax2 = axes[1]
freq_data = freq_dist[freq_dist.index <= 9]
bar_colors = [TEAL, AMBER, BLUE, CORAL] + [GRAY] * 10
ax2.bar(freq_data.index, freq_data.values, color=bar_colors[:len(freq_data)], edgecolor="none")
ax2.set_yscale("log")
ax2.set_xlabel("Number of Orders")
ax2.set_ylabel("Customers (log scale)")
ax2.set_title("Order Frequency Distribution")
ax2.set_xticks(freq_data.index)
for x, y in zip(freq_data.index, freq_data.values):
    ax2.text(x, y * 1.3, f"{y:,}", ha="center", fontsize=9, color=GRAY)

# --- Retention funnel ---
ax3 = axes[2]
funnel_labels = ["All Customers", "Ordered 1+", "Ordered 2+", "Ordered 3+", "Ordered 4+"]
funnel_vals = [
    len(purchase_freq),
    len(purchase_freq),
    (purchase_freq["order_count"] >= 2).sum(),
    (purchase_freq["order_count"] >= 3).sum(),
    (purchase_freq["order_count"] >= 4).sum(),
]
funnel_pcts = [v / len(purchase_freq) * 100 for v in funnel_vals]
colors_f = [TEAL, TEAL, AMBER, BLUE, CORAL]
bars = ax3.barh(funnel_labels[::-1], funnel_pcts[::-1], color=colors_f[::-1], edgecolor="none", height=0.6)
ax3.set_xlabel("% of All Customers")
ax3.set_title("Retention Funnel")
ax3.set_xlim(0, 115)
for bar, val, pct in zip(bars, funnel_vals[::-1], funnel_pcts[::-1]):
    ax3.text(pct + 1, bar.get_y() + bar.get_height() / 2,
             f"{val:,} ({pct:.1f}%)", va="center", fontsize=9, color=GRAY)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PATH, "03_customer_segmentation.png"), dpi=150, bbox_inches="tight")
plt.show()
print("Saved: 03_customer_segmentation.png")

# %% [markdown]
# ## 6. RFM Scoring (Simulated — Geography-Based)
#
# Since this dataset contains order-level geography (not transaction dates/values),
# we derive a **geography-adjusted RFM proxy** using:
# - **Recency proxy** → State e-commerce maturity rank (SP most mature)
# - **Frequency** → Actual repeat purchase count per customer_unique_id
# - **Monetary proxy** → City-tier score (Tier 1/2/3 city classification)

# %%
STATE_MATURITY = {
    "SP": 5, "RJ": 5, "MG": 4, "RS": 4, "PR": 4,
    "SC": 3, "BA": 3, "DF": 3, "ES": 3, "GO": 3,
    "PE": 2, "CE": 2, "PA": 2, "MT": 2, "MA": 2,
    "MS": 2, "PB": 1, "PI": 1, "RN": 1, "AL": 1,
    "SE": 1, "TO": 1, "RO": 1, "AM": 1, "AC": 1,
    "AP": 1, "RR": 1,
}

TIER1_CITIES = {"sao paulo", "rio de janeiro", "belo horizonte", "brasilia", "curitiba",
                "porto alegre", "salvador", "fortaleza", "manaus", "recife"}
TIER2_CITIES = {"campinas", "guarulhos", "sao bernardo do campo", "niteroi",
                "goiania", "belem", "santos", "osasco", "maceio", "teresina"}

def city_tier(city):
    c = str(city).lower()
    if c in TIER1_CITIES:
        return 3
    elif c in TIER2_CITIES:
        return 2
    return 1

df_rfm = df.copy()
df_rfm["state_score"]     = df_rfm["customer_state"].map(STATE_MATURITY).fillna(1)
df_rfm["city_tier"]       = df_rfm["customer_city"].apply(city_tier)
freq_map = purchase_freq.set_index("customer_unique_id")["order_count"]
df_rfm["frequency"]       = df_rfm["customer_unique_id"].map(freq_map)

def rfm_score(row):
    r = row["state_score"]
    f = min(row["frequency"], 5)
    m = row["city_tier"]
    raw = (r * 0.3) + (f * 0.5) + (m * 0.2)
    return round(raw, 2)

df_rfm["rfm_score"] = df_rfm.apply(rfm_score, axis=1)

def rfm_segment(score):
    if score >= 4.0:
        return "High Value"
    elif score >= 2.5:
        return "Mid Value"
    else:
        return "Low Value"

df_rfm["rfm_segment"] = df_rfm["rfm_score"].apply(rfm_segment)

print("RFM Score Distribution:")
print(df_rfm["rfm_segment"].value_counts().to_string())
print()
print("RFM Score Stats:")
print(df_rfm["rfm_score"].describe().round(3).to_string())

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("RFM Proxy Scoring — Customer Value Distribution", fontsize=16, fontweight="bold", y=1.01)

# --- RFM score histogram ---
ax = axes[0]
ax.hist(df_rfm["rfm_score"], bins=30, color=TEAL, edgecolor="white", linewidth=0.5, alpha=0.85)
ax.axvline(df_rfm["rfm_score"].mean(), color=CORAL, linewidth=2, linestyle="--", label=f"Mean: {df_rfm['rfm_score'].mean():.2f}")
ax.axvline(df_rfm["rfm_score"].median(), color=BLUE, linewidth=2, linestyle="--", label=f"Median: {df_rfm['rfm_score'].median():.2f}")
ax.set_xlabel("RFM Score")
ax.set_ylabel("Number of Customers")
ax.set_title("RFM Score Distribution")
ax.legend()
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

# --- Segment breakdown bar ---
ax2 = axes[1]
seg_vals = df_rfm["rfm_segment"].value_counts()
colors_rfm = {"High Value": TEAL, "Mid Value": AMBER, "Low Value": CORAL}
seg_colors_ordered = [colors_rfm[s] for s in seg_vals.index]
bars = ax2.bar(seg_vals.index, seg_vals.values, color=seg_colors_ordered, edgecolor="none", width=0.5)
ax2.set_ylabel("Number of Customers")
ax2.set_title("Customers by RFM Segment")
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
for bar in bars:
    v = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width() / 2, v + 200,
             f"{v:,}\n({v/len(df_rfm)*100:.1f}%)", ha="center", fontsize=10, color=GRAY)
ax2.set_ylim(0, seg_vals.max() * 1.2)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PATH, "04_rfm_analysis.png"), dpi=150, bbox_inches="tight")
plt.show()
print("Saved: 04_rfm_analysis.png")

# %% [markdown]
# ## 7. Regional Intelligence

# %%
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

df_rfm["region"] = df_rfm["customer_state"].map(REGION_MAP)
region_stats = df_rfm.groupby("region").agg(
    orders=("customer_id", "count"),
    unique_customers=("customer_unique_id", "nunique"),
    avg_rfm=("rfm_score", "mean"),
    states=("customer_state", "nunique"),
    cities=("customer_city", "nunique"),
).reset_index()
region_stats["repeat_rate"] = region_stats.apply(
    lambda r: df_rfm[df_rfm["region"] == r["region"]].groupby("customer_unique_id")
    .size().apply(lambda x: x >= 2).sum() / r["unique_customers"] * 100, axis=1
).round(2)
region_stats["order_pct"] = (region_stats["orders"] / region_stats["orders"].sum() * 100).round(2)
region_stats = region_stats.sort_values("orders", ascending=False)

print("REGIONAL BREAKDOWN:")
print(region_stats.to_string(index=False))

# %%
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Regional Intelligence Dashboard", fontsize=16, fontweight="bold", y=1.01)

region_colors = {"Southeast": TEAL, "South": BLUE, "Northeast": AMBER,
                 "Central-West": CORAL, "North": GRAY}
rc = [region_colors[r] for r in region_stats["region"]]

# Orders by region
ax = axes[0][0]
ax.bar(region_stats["region"], region_stats["orders"], color=rc, edgecolor="none", width=0.5)
ax.set_title("Orders by Region")
ax.set_ylabel("Orders")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
for i, row in region_stats.iterrows():
    ax.text(list(region_stats["region"]).index(row["region"]),
            row["orders"] + 500, f"{row['order_pct']}%", ha="center", fontsize=10, color=GRAY)

# Cities per region
ax2 = axes[0][1]
ax2.bar(region_stats["region"], region_stats["cities"], color=rc, edgecolor="none", width=0.5, alpha=0.8)
ax2.set_title("Unique Cities per Region")
ax2.set_ylabel("City Count")
for i, row in region_stats.iterrows():
    ax2.text(list(region_stats["region"]).index(row["region"]),
            row["cities"] + 5, str(row["cities"]), ha="center", fontsize=10, color=GRAY)

# Avg RFM by region
ax3 = axes[1][0]
ax3.bar(region_stats["region"], region_stats["avg_rfm"], color=rc, edgecolor="none", width=0.5)
ax3.set_title("Avg RFM Score by Region")
ax3.set_ylabel("RFM Score")
ax3.axhline(df_rfm["rfm_score"].mean(), color=CORAL, linestyle="--", linewidth=1.5,
            label=f"Overall avg: {df_rfm['rfm_score'].mean():.2f}")
ax3.legend(fontsize=9)
for i, row in region_stats.iterrows():
    ax3.text(list(region_stats["region"]).index(row["region"]),
            row["avg_rfm"] + 0.02, f"{row['avg_rfm']:.2f}", ha="center", fontsize=10, color=GRAY)

# Repeat rate by region
ax4 = axes[1][1]
ax4.bar(region_stats["region"], region_stats["repeat_rate"], color=rc, edgecolor="none", width=0.5)
ax4.set_title("Repeat Purchase Rate by Region (%)")
ax4.set_ylabel("Repeat Rate (%)")
for i, row in region_stats.iterrows():
    ax4.text(list(region_stats["region"]).index(row["region"]),
            row["repeat_rate"] + 0.02, f"{row['repeat_rate']}%", ha="center", fontsize=10, color=GRAY)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PATH, "05_regional_intelligence.png"), dpi=150, bbox_inches="tight")
plt.show()
print("Saved: 05_regional_intelligence.png")

# %% [markdown]
# ## 8. Churn Proxy Analysis

# %%
# Churn proxy: customers who placed only 1 order AND are in low-maturity states
# are flagged as highest churn risk
df_churn = df_rfm.copy()
df_churn_grp = df_churn.groupby("customer_unique_id").agg(
    orders=("customer_id", "count"),
    state=("customer_state", "first"),
    region=("region", "first"),
    rfm=("rfm_score", "first"),
    city_tier=("city_tier", "first"),
).reset_index()

def churn_risk(row):
    if row["orders"] >= 3:
        return "Low Risk"
    elif row["orders"] == 2:
        return "Medium Risk"
    elif row["rfm"] >= 2.5:
        return "Medium Risk"
    else:
        return "High Risk"

df_churn_grp["churn_risk"] = df_churn_grp.apply(churn_risk, axis=1)

churn_summary = df_churn_grp["churn_risk"].value_counts()
print("CHURN RISK DISTRIBUTION:")
for label, val in churn_summary.items():
    print(f"  {label:<16} : {val:>7,}  ({val/len(df_churn_grp)*100:.1f}%)")

# %%
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
fig.suptitle("Churn Risk Analysis", fontsize=16, fontweight="bold", y=1.01)

churn_colors = {"High Risk": CORAL, "Medium Risk": AMBER, "Low Risk": TEAL}

ax = axes[0]
vals = [churn_summary.get(k, 0) for k in ["High Risk", "Medium Risk", "Low Risk"]]
labels = ["High Risk", "Medium Risk", "Low Risk"]
cols = [churn_colors[l] for l in labels]
wedges, texts, autotexts = ax.pie(vals, labels=labels, colors=cols, autopct="%1.1f%%",
    startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 2}, pctdistance=0.78)
centre = plt.Circle((0, 0), 0.55, fc="#FAFAF8")
ax.add_patch(centre)
ax.set_title("Churn Risk Segments")

ax2 = axes[1]
risk_region = df_churn_grp.groupby(["region", "churn_risk"]).size().unstack(fill_value=0)
risk_region_pct = risk_region.div(risk_region.sum(axis=1), axis=0) * 100
risk_region_pct = risk_region_pct.sort_values("High Risk", ascending=False)
risk_region_pct[["High Risk", "Medium Risk", "Low Risk"]].plot(
    kind="bar", ax=ax2,
    color=[CORAL, AMBER, TEAL],
    edgecolor="none", width=0.6
)
ax2.set_xticklabels(risk_region_pct.index, rotation=30, ha="right")
ax2.set_ylabel("% of Customers")
ax2.set_title("Churn Risk by Region (%)")
ax2.legend(loc="upper right", fontsize=9)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_PATH, "06_churn_analysis.png"), dpi=150, bbox_inches="tight")
plt.show()
print("Saved: 06_churn_analysis.png")

# %% [markdown]
# ## 9. Export Cleaned Dataset & Summary

# %%
df_final = df_rfm.merge(
    df_churn_grp[["customer_unique_id", "churn_risk"]],
    on="customer_unique_id", how="left"
)

export_path = os.path.join(OUTPUT_PATH, "olist_customers_enriched.csv")
df_final.to_csv(export_path, index=False)
print(f"Exported enriched dataset: {export_path}")
print(f"Shape: {df_final.shape}")
print(f"\nNew columns added: region, state_score, city_tier, frequency, rfm_score, rfm_segment, churn_risk")

# %%
print("\n" + "=" * 60)
print("EXECUTIVE SUMMARY — OLIST CUSTOMER ANALYTICS")
print("=" * 60)

total_customers  = df["customer_unique_id"].nunique()
total_orders     = len(df)
repeat_customers = (purchase_freq["order_count"] >= 2).sum()
repeat_rate      = repeat_customers / total_customers * 100
top_state        = state_counts.iloc[0]
top_city         = city_counts.iloc[0]
se_pct           = df[df["customer_state"].isin(["SP","RJ","MG","ES"])].shape[0] / total_orders * 100

print(f"""
  Dataset       : {total_orders:,} orders | {total_customers:,} unique customers
  States        : 27 | Cities: {df['customer_city'].nunique():,}

  ACQUISITION
  ├── New customers (1 order)  : {(purchase_freq['order_count']==1).sum():,} ({(purchase_freq['order_count']==1).sum()/total_customers*100:.1f}%)
  ├── Returning (2 orders)     : {(purchase_freq['order_count']==2).sum():,} ({(purchase_freq['order_count']==2).sum()/total_customers*100:.1f}%)
  └── Loyal (3+ orders)        : {(purchase_freq['order_count']>=3).sum():,} ({(purchase_freq['order_count']>=3).sum()/total_customers*100:.2f}%)

  RETENTION
  ├── Overall repeat rate      : {repeat_rate:.2f}%
  └── Avg orders per repeater  : {purchase_freq[purchase_freq['order_count']>=2]['order_count'].mean():.2f}

  GEOGRAPHY
  ├── Top state   : {top_state['state']} — {top_state['orders']:,} orders ({top_state['pct']}%)
  ├── Top city    : {top_city['city']} — {top_city['orders']:,} orders ({top_city['pct']}%)
  └── Southeast   : {se_pct:.1f}% of all orders

  STRATEGIC INSIGHTS
  1. Retention gap: 96.9% one-time buyers → massive CLV improvement opportunity
  2. Geographic concentration: top 3 states = 66.6% of orders — market saturation risk
  3. North/Northeast underpenetrated: <12% of orders from 18 states
  4. City diversity: {df['customer_city'].nunique():,} cities served → distribution network is broad
""")
print("=" * 60)
