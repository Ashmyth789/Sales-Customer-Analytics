"""
app.py — E-commerce Analytics Dashboard
Run: streamlit run streamlit_app/app.py
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import streamlit as st

# ── Path setup ────────────────────────────────────────────────
ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH = os.path.join(ROOT, "data", "olist_customers_dataset.csv")

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Olist Customer Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .stMetric { background: #F5F4F0; border-radius: 10px; padding: 12px 16px; }
    .block-container { padding-top: 1.5rem; }
    h1 { font-size: 1.8rem !important; }
    .insight-box {
        background: #F0FBF6;
        border-left: 4px solid #1D9E75;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.93rem;
    }
    .warn-box {
        background: #FEF9EC;
        border-left: 4px solid #BA7517;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.93rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────
TEAL  = "#1D9E75"
CORAL = "#D85A30"
BLUE  = "#185FA5"
AMBER = "#BA7517"
GRAY  = "#888780"

REGION_MAP = {
    "SP":"Southeast","RJ":"Southeast","MG":"Southeast","ES":"Southeast",
    "RS":"South","PR":"South","SC":"South",
    "BA":"Northeast","PE":"Northeast","CE":"Northeast","MA":"Northeast",
    "PB":"Northeast","PI":"Northeast","RN":"Northeast","AL":"Northeast","SE":"Northeast",
    "DF":"Central-West","GO":"Central-West","MT":"Central-West","MS":"Central-West",
    "PA":"North","AM":"North","RO":"North","TO":"North","AC":"North","AP":"North","RR":"North",
}
STATE_MATURITY = {
    "SP":5,"RJ":5,"MG":4,"RS":4,"PR":4,"SC":3,"BA":3,"DF":3,"ES":3,"GO":3,
    "PE":2,"CE":2,"PA":2,"MT":2,"MA":2,"MS":2,"PB":1,"PI":1,"RN":1,"AL":1,
    "SE":1,"TO":1,"RO":1,"AM":1,"AC":1,"AP":1,"RR":1,
}
TIER1 = {"sao paulo","rio de janeiro","belo horizonte","brasilia","curitiba",
          "porto alegre","salvador","fortaleza","manaus","recife"}
TIER2 = {"campinas","guarulhos","sao bernardo do campo","niteroi",
          "goiania","belem","santos","osasco","maceio","teresina"}

STATE_FULL = {
    "AC":"Acre","AL":"Alagoas","AP":"Amapá","AM":"Amazonas","BA":"Bahia",
    "CE":"Ceará","DF":"Distrito Federal","ES":"Espírito Santo","GO":"Goiás",
    "MA":"Maranhão","MT":"Mato Grosso","MS":"Mato Grosso do Sul","MG":"Minas Gerais",
    "PA":"Pará","PB":"Paraíba","PR":"Paraná","PE":"Pernambuco","PI":"Piauí",
    "RJ":"Rio de Janeiro","RN":"Rio Grande do Norte","RS":"Rio Grande do Sul",
    "RO":"Rondônia","RR":"Roraima","SC":"Santa Catarina","SP":"São Paulo",
    "SE":"Sergipe","TO":"Tocantins",
}

# ── Data loading ──────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["region"]         = df["customer_state"].map(REGION_MAP).fillna("Unknown")
    df["state_maturity"] = df["customer_state"].map(STATE_MATURITY).fillna(1)
    df["city_tier"]      = df["customer_city"].apply(
        lambda c: 3 if str(c).lower() in TIER1 else (2 if str(c).lower() in TIER2 else 1)
    )
    freq = df.groupby("customer_unique_id").size().reset_index(name="order_count")
    df = df.merge(freq, on="customer_unique_id", how="left")

    def rfm(row):
        r = row["state_maturity"]
        f = min(row["order_count"], 5)
        m = row["city_tier"]
        return round(r * 0.3 + f * 0.5 + m * 0.2, 2)

    df["rfm_score"] = df.apply(rfm, axis=1)
    df["rfm_segment"] = df["rfm_score"].apply(
        lambda s: "High Value" if s >= 4 else ("Mid Value" if s >= 2.5 else "Low Value")
    )
    df["customer_city_title"] = df["customer_city"].str.title()
    return df

df = load_data()

# ── Sidebar filters ───────────────────────────────────────────
st.sidebar.image("https://via.placeholder.com/220x50/1D9E75/FFFFFF?text=Olist+Analytics", width=220)
st.sidebar.markdown("### Filters")

all_regions = ["All"] + sorted(df["region"].unique().tolist())
sel_region = st.sidebar.selectbox("Region", all_regions)

all_states = ["All"] + sorted(df["customer_state"].unique().tolist())
sel_state = st.sidebar.selectbox("State", all_states)

rfm_segments = st.sidebar.multiselect(
    "RFM Segment",
    ["High Value", "Mid Value", "Low Value"],
    default=["High Value", "Mid Value", "Low Value"]
)

# Apply filters
dff = df.copy()
if sel_region != "All":
    dff = dff[dff["region"] == sel_region]
if sel_state != "All":
    dff = dff[dff["customer_state"] == sel_state]
if rfm_segments:
    dff = dff[dff["rfm_segment"].isin(rfm_segments)]

# ── Header ────────────────────────────────────────────────────
st.title("📦 Olist E-Commerce — Customer Analytics")
st.caption("Brazilian e-commerce customer segmentation, geographic intelligence, and retention analysis")

# ── KPI row ───────────────────────────────────────────────────
total_orders    = len(dff)
unique_cust     = dff["customer_unique_id"].nunique()
repeat_rate     = (dff.groupby("customer_unique_id")["customer_id"].count() >= 2).mean() * 100
states_covered  = dff["customer_state"].nunique()
cities_covered  = dff["customer_city"].nunique()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Orders",     f"{total_orders:,}")
k2.metric("Unique Customers", f"{unique_cust:,}")
k3.metric("Repeat Rate",      f"{repeat_rate:.1f}%")
k4.metric("States",           f"{states_covered}")
k5.metric("Cities",           f"{cities_covered:,}")

st.divider()

# ── Row 1: Geography ──────────────────────────────────────────
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("Orders by State")
    state_df = dff["customer_state"].value_counts().reset_index()
    state_df.columns = ["state", "orders"]
    state_df["state_name"] = state_df["state"].map(STATE_FULL)
    state_df["label"] = state_df["state"] + " — " + state_df["state_name"].fillna("")

    top_n = st.slider("Show top N states", 5, 27, 15, key="top_n_states")
    plot_df = state_df.head(top_n)
    colors = [TEAL if i < 3 else (BLUE if i < 8 else GRAY) for i in range(len(plot_df))]

    fig, ax = plt.subplots(figsize=(8, top_n * 0.42 + 1))
    fig.patch.set_facecolor("#FAFAF8")
    ax.set_facecolor("#FAFAF8")
    ax.barh(plot_df["label"][::-1], plot_df["orders"][::-1],
            color=colors[::-1], edgecolor="none")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.spines[["top","right"]].set_visible(False)
    ax.set_xlabel("Orders")
    ax.grid(axis="x", color="#E8E6DF", linewidth=0.6)
    for i, (_, row) in enumerate(plot_df[::-1].iterrows()):
        ax.text(row["orders"] + 50, i, f"{row['orders']:,}", va="center", fontsize=8.5, color=GRAY)
    ax.set_xlim(0, plot_df["orders"].max() * 1.2)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("Regional Breakdown")
    region_df = dff.groupby("region").agg(
        orders=("customer_id", "count"),
        customers=("customer_unique_id", "nunique"),
        cities=("customer_city", "nunique")
    ).reset_index().sort_values("orders", ascending=False)

    region_colors_map = {
        "Southeast": TEAL, "South": BLUE, "Northeast": AMBER,
        "Central-West": CORAL, "North": GRAY
    }
    fig2, ax2 = plt.subplots(figsize=(5, 4.5))
    fig2.patch.set_facecolor("#FAFAF8")
    ax2.set_facecolor("#FAFAF8")
    rc = [region_colors_map.get(r, GRAY) for r in region_df["region"]]
    wedges, texts, autos = ax2.pie(
        region_df["orders"], labels=region_df["region"],
        colors=rc, autopct="%1.1f%%",
        startangle=90, wedgeprops={"edgecolor":"white","linewidth":2},
        pctdistance=0.78
    )
    centre = plt.Circle((0,0), 0.55, fc="#FAFAF8")
    ax2.add_patch(centre)
    ax2.text(0, 0, f"{total_orders:,}\norders", ha="center", va="center",
             fontsize=10, fontweight="bold", color="#333")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

    st.dataframe(
        region_df.assign(share=lambda x: (x["orders"] / x["orders"].sum() * 100).round(1))
                 [["region","orders","customers","cities","share"]]
                 .rename(columns={"share":"share %"}),
        use_container_width=True, hide_index=True
    )

st.divider()

# ── Row 2: Segmentation ───────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Customer Segmentation")
    freq_df = dff.groupby("customer_unique_id")["customer_id"].count().reset_index()
    freq_df.columns = ["customer_unique_id", "orders"]
    freq_df["segment"] = freq_df["orders"].apply(
        lambda n: "New" if n == 1 else ("Returning" if n == 2 else ("Loyal" if n <= 4 else "Champion"))
    )
    seg_counts = freq_df["segment"].value_counts().reindex(
        ["New", "Returning", "Loyal", "Champion"], fill_value=0
    )
    seg_col = {"New": TEAL, "Returning": AMBER, "Loyal": BLUE, "Champion": CORAL}

    fig3, axes3 = plt.subplots(1, 2, figsize=(8, 4))
    fig3.patch.set_facecolor("#FAFAF8")

    # Donut
    ax_d = axes3[0]
    ax_d.set_facecolor("#FAFAF8")
    colors_seg = [seg_col[s] for s in seg_counts.index]
    ax_d.pie(seg_counts.values, labels=seg_counts.index, colors=colors_seg,
             autopct="%1.1f%%", startangle=90,
             wedgeprops={"edgecolor":"white","linewidth":2}, pctdistance=0.78)
    c2 = plt.Circle((0,0), 0.55, fc="#FAFAF8")
    ax_d.add_patch(c2)

    # Bar
    ax_b = axes3[1]
    ax_b.set_facecolor("#FAFAF8")
    bars = ax_b.bar(seg_counts.index, seg_counts.values,
                    color=colors_seg, edgecolor="none", width=0.55)
    ax_b.spines[["top","right"]].set_visible(False)
    ax_b.set_ylabel("Customers")
    ax_b.grid(axis="y", color="#E8E6DF", linewidth=0.6)
    ax_b.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{int(x):,}"))
    for bar in bars:
        v = bar.get_height()
        ax_b.text(bar.get_x()+bar.get_width()/2, v+50, f"{v:,}",
                  ha="center", fontsize=9, color=GRAY)

    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

with col4:
    st.subheader("Retention Funnel")
    freq_counts = freq_df["orders"]
    funnel_data = {
        "1+ order":  len(freq_counts),
        "2+ orders": (freq_counts >= 2).sum(),
        "3+ orders": (freq_counts >= 3).sum(),
        "4+ orders": (freq_counts >= 4).sum(),
        "5+ orders": (freq_counts >= 5).sum(),
    }
    funnel_pcts = {k: v / len(freq_counts) * 100 for k, v in funnel_data.items()}

    fig4, ax4 = plt.subplots(figsize=(6.5, 4))
    fig4.patch.set_facecolor("#FAFAF8")
    ax4.set_facecolor("#FAFAF8")
    funnel_colors = [TEAL, AMBER, BLUE, CORAL, GRAY]
    labels_f = list(funnel_data.keys())
    vals_f   = list(funnel_pcts.values())
    bars_f = ax4.barh(labels_f[::-1], vals_f[::-1],
                      color=funnel_colors[::-1], edgecolor="none", height=0.55)
    ax4.set_xlabel("% of Customers")
    ax4.set_xlim(0, 115)
    ax4.spines[["top","right"]].set_visible(False)
    ax4.grid(axis="x", color="#E8E6DF", linewidth=0.6)
    for bar, (k, v), pct in zip(bars_f, list(funnel_data.items())[::-1], vals_f[::-1]):
        ax4.text(pct + 0.5, bar.get_y()+bar.get_height()/2,
                 f"{v:,}  ({pct:.1f}%)", va="center", fontsize=9, color=GRAY)
    plt.tight_layout()
    st.pyplot(fig4)
    plt.close()

st.divider()

# ── Row 3: RFM + City ─────────────────────────────────────────
col5, col6 = st.columns(2)

with col5:
    st.subheader("RFM Score Distribution")
    fig5, ax5 = plt.subplots(figsize=(6.5, 4))
    fig5.patch.set_facecolor("#FAFAF8")
    ax5.set_facecolor("#FAFAF8")
    ax5.hist(dff["rfm_score"], bins=30, color=TEAL, edgecolor="white", linewidth=0.5, alpha=0.85)
    ax5.axvline(dff["rfm_score"].mean(), color=CORAL, linewidth=2,
                linestyle="--", label=f"Mean: {dff['rfm_score'].mean():.2f}")
    ax5.axvline(dff["rfm_score"].median(), color=BLUE, linewidth=2,
                linestyle="--", label=f"Median: {dff['rfm_score'].median():.2f}")
    ax5.set_xlabel("RFM Score")
    ax5.set_ylabel("Customers")
    ax5.legend(fontsize=9)
    ax5.spines[["top","right"]].set_visible(False)
    ax5.grid(axis="y", color="#E8E6DF", linewidth=0.6)
    ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{int(x):,}"))
    plt.tight_layout()
    st.pyplot(fig5)
    plt.close()

with col6:
    st.subheader("Top 15 Cities")
    city_df = dff["customer_city_title"].value_counts().head(15).reset_index()
    city_df.columns = ["city","orders"]
    fig6, ax6 = plt.subplots(figsize=(6.5, 4.5))
    fig6.patch.set_facecolor("#FAFAF8")
    ax6.set_facecolor("#FAFAF8")
    city_colors = [BLUE if i == 0 else (TEAL if i < 5 else GRAY) for i in range(len(city_df))]
    ax6.barh(city_df["city"][::-1], city_df["orders"][::-1],
             color=city_colors[::-1], edgecolor="none")
    ax6.spines[["top","right"]].set_visible(False)
    ax6.set_xlabel("Orders")
    ax6.grid(axis="x", color="#E8E6DF", linewidth=0.6)
    ax6.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{int(x):,}"))
    plt.tight_layout()
    st.pyplot(fig6)
    plt.close()

st.divider()

# ── Insights ──────────────────────────────────────────────────
st.subheader("Key Analyst Insights")
i1, i2 = st.columns(2)
with i1:
    st.markdown("""
    <div class="insight-box">
      <b>Southeast dominance:</b> SP + RJ + MG + ES = 68.6% of all orders.
      Strong urbanization and logistics infrastructure drive e-commerce adoption.
    </div>
    <div class="insight-box">
      <b>Retention gap:</b> Only 3.1% of customers reorder. This is the #1 growth lever —
      a 1pp improvement in repeat rate equals ~960 additional loyal customers.
    </div>
    """, unsafe_allow_html=True)
with i2:
    st.markdown("""
    <div class="warn-box">
      <b>Geographic expansion:</b> North & Northeast states (18 states combined) account for
      &lt;14% of orders — significant untapped market with growing internet penetration.
    </div>
    <div class="warn-box">
      <b>City concentration risk:</b> São Paulo city alone = 15.6% of all orders.
      Platform revenue is vulnerable to local competitive disruption.
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Raw data explorer ─────────────────────────────────────────
with st.expander("🔍 Raw Data Explorer"):
    st.write(f"Showing {len(dff):,} rows with current filters applied.")
    search = st.text_input("Filter by city name")
    display_df = dff if not search else dff[dff["customer_city_title"].str.contains(search, case=False, na=False)]
    st.dataframe(
        display_df[["customer_id","customer_unique_id","customer_city_title",
                    "customer_state","region","city_tier","order_count","rfm_score","rfm_segment"]]
        .rename(columns={"customer_city_title":"city","customer_state":"state"})
        .head(500),
        use_container_width=True, hide_index=True
    )

st.caption("Data source: Olist Brazilian E-Commerce Public Dataset | Built with Python · Pandas · Matplotlib · Streamlit")
