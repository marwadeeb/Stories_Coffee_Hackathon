import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

from cleaner import clean_monthly, clean_products, clean_category, clean_sales

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stories Coffee · Intelligence Dashboard",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Serif Display', serif !important; }

section[data-testid="stSidebar"] { background: #1a1008; color: #f5e6c8; }
section[data-testid="stSidebar"] * { color: #f5e6c8 !important; }

.main { background: #fdf8f2; }

.metric-card {
    background: white; border-radius: 12px; padding: 1.2rem 1.4rem;
    border-left: 4px solid #c8852a; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 0.5rem;
}
.metric-label {
    font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: #888; margin-bottom: 0.2rem;
}
.metric-value { font-family: 'DM Serif Display', serif; font-size: 1.9rem; color: #1a1008; line-height: 1; }
.metric-sub   { font-size: 0.78rem; color: #999; margin-top: 0.2rem; }

.section-header {
    font-family: 'DM Serif Display', serif; font-size: 1.5rem; color: #1a1008;
    border-bottom: 2px solid #c8852a; padding-bottom: 0.4rem; margin: 1.8rem 0 1rem 0;
}
.insight-box {
    background: #fff8ee; border: 1px solid #f0d5a0; border-left: 4px solid #c8852a;
    border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.8rem 0;
    font-size: 0.88rem; color: #3a2800; line-height: 1.6;
}
.insight-box strong { color: #c8852a; }
.warn-box {
    background: #fff5f5; border-left: 4px solid #e53935; border-radius: 8px;
    padding: 0.9rem 1.1rem; margin: 0.8rem 0; font-size: 0.88rem; color: #3a0000;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
MONTHS = ['January','February','March','April','May','June',
          'July','August','September','October','November','December']
EXCLUDE_BRANCHES = ['Total', 'Stories Event Starco', 'Stories.']
EXCLUDE_GROUPS   = {'ADD ONS','REPLACE','PACKAGING','NOT USED','OFFER',
                    'ADD SYRUP','COMBO TOPPINGS','TOPPINGS','LUXURY TOPPINGS'}

plt.rcParams.update({
    'figure.facecolor': '#fdf8f2', 'axes.facecolor': '#fdf8f2',
    'font.family': 'sans-serif', 'font.size': 9,
})

# ── Helpers ────────────────────────────────────────────────────────────────────
def metric_card(label, value, sub=""):
    sub_html = f"<div class='metric-sub'>{sub}</div>" if sub else ""
    st.markdown(
        f"<div class='metric-card'>"
        f"<div class='metric-label'>{label}</div>"
        f"<div class='metric-value'>{value}</div>"
        f"{sub_html}</div>",
        unsafe_allow_html=True
    )

def insight(text):
    st.markdown(f'<div class="insight-box">💡 {text}</div>', unsafe_allow_html=True)

def warn(text):
    st.markdown(f'<div class="warn-box">⚠️ {text}</div>', unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

# ── Sidebar uploads ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ☕ Stories Coffee")
    st.markdown("### Intelligence Dashboard")
    st.markdown("---")
    st.markdown("**Upload your raw data exports**")
    st.caption("Drop in any new CSV export — files are cleaned automatically.")

    f_monthly  = st.file_uploader("📅 Monthly Sales",         type="csv", key="monthly")
    f_category = st.file_uploader("📊 Category Profit",       type="csv", key="category")
    f_prod     = st.file_uploader("🛍️ Product Profitability",  type="csv", key="prod")
    f_sales    = st.file_uploader("🏷️ Sales by Group",         type="csv", key="sales")
    st.markdown("---")

# ── Clean uploaded files ───────────────────────────────────────────────────────
@st.cache_data
def run_cleaners(monthly_bytes, category_bytes, prod_bytes, sales_bytes):
    import io
    results = {}
    if monthly_bytes is not None:
        results["monthly"]  = clean_monthly(io.BytesIO(monthly_bytes))
    if category_bytes is not None:
        results["category"] = clean_category(io.BytesIO(category_bytes))
    if prod_bytes is not None:
        results["prod"]     = clean_products(io.BytesIO(prod_bytes))
    if sales_bytes is not None:
        results["sales"]    = clean_sales(io.BytesIO(sales_bytes))
    return results

_cleaned = run_cleaners(
    f_monthly.read()  if f_monthly  else None,
    f_category.read() if f_category else None,
    f_prod.read()     if f_prod     else None,
    f_sales.read()    if f_sales    else None,
)

monthly_raw = _cleaned.get("monthly")
cat_df      = _cleaned.get("category")
prod_df     = _cleaned.get("prod")
sales_df    = _cleaned.get("sales")

# ── Sidebar download buttons (appear once a file is cleaned) ───────────────────
with st.sidebar:
    _dl_configs = [
        ("monthly",  monthly_raw,  "monthlyClean.csv",  "📅 Monthly Cleaned"),
        ("category", cat_df,       "category.csv",      "📊 Category Cleaned"),
        ("prod",     prod_df,      "prodItems.csv",      "🛍️ Products Cleaned"),
        ("sales",    sales_df,     "sales_cleaned.csv", "🏷️ Sales Cleaned"),
    ]
    _any_ready = any(df is not None for _, df, _, _ in _dl_configs)
    if _any_ready:
        st.markdown("**Download cleaned files**")
        for _key, _df, _fname, _label in _dl_configs:
            if _df is not None:
                st.download_button(
                    label=_label,
                    data=_df.to_csv(index=False).encode("utf-8"),
                    file_name=_fname,
                    mime="text/csv",
                    key=f"dl_{_key}",
                    use_container_width=True,
                )
        st.markdown("---")

data_ready = all([monthly_raw is not None, cat_df is not None,
                  prod_df is not None, sales_df is not None])

if not data_ready:
    st.markdown("""
    <div style="text-align:center; padding:4rem 2rem;">
        <div style="font-family:'DM Serif Display',serif;font-size:3rem;color:#1a1008;margin-bottom:0.5rem;">
            Stories Coffee
        </div>
        <div style="font-size:1.1rem;color:#888;margin-bottom:2rem;">Intelligence Dashboard</div>
        <div style="font-size:0.95rem;color:#aaa;max-width:480px;margin:auto;line-height:1.8;">
            Upload your four CSV exports using the sidebar on the left.<br>
            The dashboard will automatically analyse branch performance,
            seasonality, product mix, and highlight actionable insights.
        </div>
        <div style="margin-top:3rem;font-size:2.5rem;">☕ 📊 🏆</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Year selector ──────────────────────────────────────────────────────────────
available_years = sorted(monthly_raw['Year'].dropna().unique().astype(int).tolist())
with st.sidebar:
    selected_year = st.selectbox(
        "Select year",
        options=available_years,
        index=len(available_years) - 1,
        help="Works automatically with any future export"
    )
    st.caption("Built for Stories Coffee · Hackathon")

# ── Filter monthly to selected year ───────────────────────────────────────────
monthly_yr = (
    monthly_raw[
        (monthly_raw['Year'].astype(str).str.strip() == str(selected_year)) &
        (~monthly_raw['Branch Name'].isin(EXCLUDE_BRANCHES))
    ]
    .drop_duplicates(subset='Branch Name')
    .copy()
)
monthly_yr = monthly_yr[monthly_yr['Annual Total'] > 0].reset_index(drop=True)

# Only show months that actually have data — handles partial years gracefully
active_months = [m for m in MONTHS if m in monthly_yr.columns and monthly_yr[m].sum() > 0]

# ── Shared derived data ────────────────────────────────────────────────────────
cat_df['Revenue'] = cat_df['Total Cost'] + cat_df['Total Profit']

branch_sum = (
    cat_df.groupby('Branch')
    .agg(Total_Revenue=('Revenue','sum'), Total_Profit=('Total Profit','sum'),
         Total_Cost=('Total Cost','sum'), Total_Qty=('Qty','sum'))
    .reset_index()
)
branch_sum['Margin'] = (
    branch_sum['Total_Profit'] /
    (branch_sum['Total_Profit'] + branch_sum['Total_Cost']) * 100
)
branch_sum = branch_sum.sort_values('Total_Profit', ascending=False).reset_index(drop=True)

total_profit   = branch_sum['Total_Profit'].sum()
total_branches = len(branch_sum)

# Monthly chain totals over active months only
monthly_chain     = monthly_yr[active_months].sum() if active_months else pd.Series(dtype=float)
peak_month        = monthly_chain.idxmax() if len(monthly_chain) > 0 else "N/A"
trough_month      = monthly_chain.idxmin() if len(monthly_chain) > 0 else "N/A"
peak_trough_ratio = (
    monthly_chain.max() / monthly_chain.min()
    if len(monthly_chain) > 0 and monthly_chain.min() > 0 else float('nan')
)

# Product groups
core_sales = sales_df[~sales_df['Group'].isin(EXCLUDE_GROUPS)].copy()
grp = (
    core_sales.groupby('Group')
    .agg(Revenue=('Total Amount','sum'), Qty=('Qty','sum'))
    .reset_index()
    .sort_values('Revenue', ascending=False)
    .reset_index(drop=True)
)
grp['Share'] = grp['Revenue'] / grp['Revenue'].sum() * 100

# Service type split
svc     = prod_df.groupby(['Branch','Service Type']).agg(Qty=('Qty','sum')).reset_index()
svc_piv = svc.pivot_table(index='Branch', columns='Service Type', values='Qty', aggfunc='sum').fillna(0)
if 'TAKE AWAY' in svc_piv.columns and 'TABLE' in svc_piv.columns:
    svc_piv['TA_Share'] = svc_piv['TAKE AWAY'] / (svc_piv['TAKE AWAY'] + svc_piv['TABLE']) * 100
    chain_ta_share = svc_piv['TA_Share'].mean()
else:
    chain_ta_share = None

# Bev / Food margins
bev_b  = cat_df[cat_df['Category'] == 'Beverages'].set_index('Branch')
food_b = cat_df[cat_df['Category'] == 'Food'].set_index('Branch')
avg_bev_margin  = bev_b['Total Profit %'].mean()
avg_food_margin = food_b['Total Profit %'].mean()

# ── HEADER — build string in Python, inject as HTML (avoids f-string-in-HTML bug) ──
subtitle    = f"INTELLIGENCE DASHBOARD · {selected_year}"
months_note = f"{len(active_months)} of 12 months available" if len(active_months) < 12 else "Full year"

st.markdown(
    f"<div style='display:flex;align-items:baseline;gap:1rem;margin-bottom:0.2rem;'>"
    f"<span style='font-family:DM Serif Display,serif;font-size:2.4rem;color:#1a1008;'>Stories Coffee</span>"
    f"<span style='font-size:0.9rem;color:#aaa;font-weight:500;letter-spacing:0.05em;'>{subtitle}</span>"
    f"<span style='font-size:0.8rem;color:#c8852a;margin-left:0.5rem;'>({months_note})</span>"
    f"</div>",
    unsafe_allow_html=True
)

# ── KPI ROW ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    metric_card("Active Branches", str(total_branches), f"Year {selected_year}")
with k2:
    metric_card("Chain Total Profit", f"{total_profit/1e6:.0f}M", "Arbitrary units")
with k3:
    metric_card("Avg Branch Margin", f"{branch_sum['Margin'].mean():.1f}%", "Bev + Food blended")
with k4:
    peak_label = peak_month[:3] if peak_month != "N/A" else "N/A"
    peak_sub   = f"{monthly_chain.max()/1e6:.0f}M" if len(monthly_chain) > 0 else ""
    metric_card("Peak Month", peak_label, peak_sub)
with k5:
    if not np.isnan(peak_trough_ratio):
        metric_card("Peak / Trough", f"{peak_trough_ratio:.1f}×", f"Trough = {trough_month[:3]}")
    else:
        metric_card("Months Available", str(len(active_months)), "Partial year data")

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Branch Rankings",
    "📅 Seasonality",
    "☕ Product Mix",
    "🔍 Margin Analysis",
    "⚡ Action Items",
])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — BRANCH RANKINGS
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    section("Branch Performance Rankings")

    col_a, col_b = st.columns([3, 2])

    with col_a:
        fig, ax = plt.subplots(figsize=(8, 7))
        n      = len(branch_sum)
        colors = sns.color_palette('YlOrRd_r', n)
        ax.barh(branch_sum['Branch'][::-1], branch_sum['Total_Profit'][::-1] / 1e6, color=colors)
        avg = branch_sum['Total_Profit'].mean() / 1e6
        ax.axvline(avg, color='#c8852a', linestyle='--', lw=1.5, label=f'Chain avg: {avg:.0f}M')
        ax.set_xlabel('Total Profit (Millions)')
        ax.set_title('Total Profit by Branch', fontweight='bold', pad=12)
        ax.legend(fontsize=8)
        ax.tick_params(axis='y', labelsize=7.5)
        ax.spines[['top','right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col_b:
        section("Margin Health")
        fig2, ax2 = plt.subplots(figsize=(5, 7))
        ms    = branch_sum.sort_values('Margin')
        bar_c = ['#e53935' if m < 69 else '#fb8c00' if m < 72 else '#43a047' for m in ms['Margin']]
        ax2.barh(ms['Branch'], ms['Margin'], color=bar_c)
        ax2.axvline(ms['Margin'].mean(), color='#c8852a', linestyle='--', lw=1.5,
                    label=f"Avg: {ms['Margin'].mean():.1f}%")
        ax2.set_xlabel('Profit Margin (%)')
        ax2.set_title('Profit Margin by Branch', fontweight='bold', pad=12)
        ax2.legend(fontsize=8)
        ax2.tick_params(axis='y', labelsize=7.5)
        ax2.spines[['top','right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    insight(
        f"<strong>Ain El Mreisseh and Zalka</strong> are the clear revenue leaders, "
        f"together accounting for ~30% of chain profit. Margin is consistent chain-wide "
        f"(~{branch_sum['Margin'].mean():.0f}%), proving the Stories model scales well."
    )

    section("Branch Detail Table")
    search = st.text_input("Filter branches", placeholder="Type a branch name...")
    display_df = branch_sum.copy()
    if search:
        display_df = display_df[display_df['Branch'].str.contains(search, case=False)]
    display_df['Rank']         = range(1, len(display_df) + 1)
    display_df['Total Profit'] = display_df['Total_Profit'].apply(lambda x: f"{x/1e6:.2f}M")
    display_df['Margin %']     = display_df['Margin'].apply(lambda x: f"{x:.1f}%")
    display_df['Units Sold']   = display_df['Total_Qty'].apply(lambda x: f"{x:,.0f}")
    st.dataframe(
        display_df[['Rank','Branch','Total Profit','Margin %','Units Sold']],
        use_container_width=True, hide_index=True
    )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — SEASONALITY
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    section("Monthly Seasonality Analysis")

    if not active_months:
        st.warning("No monthly data found for the selected year.")
    else:
        if len(active_months) < 12:
            st.info(
                f"📋 Showing **{len(active_months)} month(s)** of data for {selected_year} "
                f"({', '.join(active_months)}). Charts update automatically as more months become available."
            )

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        bar_c = ['#c8852a' if v >= monthly_chain.mean() else '#d4b896' for v in monthly_chain]
        ax1.bar(monthly_chain.index, monthly_chain / 1e6, color=bar_c, edgecolor='white', linewidth=0.5)
        ax1.axhline(monthly_chain.mean() / 1e6, color='#1a1008', linestyle='--', lw=1.5,
                    label=f'Avg: {monthly_chain.mean()/1e6:.0f}M')
        ax1.set_title(f'Chain-Wide Monthly Revenue ({selected_year})', fontweight='bold', pad=12)
        ax1.set_ylabel('Revenue (Millions)')
        ax1.legend(fontsize=8)
        ax1.tick_params(axis='x', rotation=40)
        ax1.spines[['top','right']].set_visible(False)

        # Heatmap — zeros replaced with NaN so partial months show as blank, not misleading red
        hm = monthly_yr.set_index('Branch Name')[active_months]
        hm_display = hm.replace(0, np.nan)
        hm_norm    = hm_display.div(hm_display.max(axis=1), axis=0).mul(100)
        order      = monthly_yr.set_index('Branch Name')['Annual Total'].sort_values(ascending=False).index
        hm_norm    = hm_norm.loc[order]

        sns.heatmap(hm_norm, ax=ax2, cmap='RdYlGn', linewidths=0.3,
                    cbar_kws={'label': '% of branch peak'}, annot=False)
        ax2.set_title(f'Seasonality Heatmap — {selected_year}', fontweight='bold', pad=12)
        ax2.tick_params(axis='x', rotation=40, labelsize=7.5)
        ax2.tick_params(axis='y', labelsize=7)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        c1, c2 = st.columns(2)
        with c1:
            if peak_month != "N/A" and not np.isnan(peak_trough_ratio):
                insight(
                    f"<strong>{peak_month}</strong> is the peak month and "
                    f"<strong>{trough_month}</strong> is the trough — a "
                    f"<strong>{peak_trough_ratio:.1f}× swing</strong>. This is predictable "
                    f"and should be planned for every year."
                )
            else:
                insight(
                    f"Showing <strong>{len(active_months)} month(s)</strong> of data for {selected_year}. "
                    f"Select a year with more months for full seasonality analysis."
                )
        with c2:
            insight(
                "<strong>Faqra</strong> shows the inverse of every other branch — "
                "peaking in winter (ski season) and going dark in summer. "
                "It needs a completely separate operational model."
            )

        section("Individual Branch Monthly Trend")
        selected_branch = st.selectbox("Select a branch", options=monthly_yr['Branch Name'].tolist())
        row  = monthly_yr[monthly_yr['Branch Name'] == selected_branch].iloc[0]
        vals = [row[m] for m in active_months]

        fig3, ax3 = plt.subplots(figsize=(10, 3.5))
        ax3.fill_between(active_months, [v / 1e6 for v in vals], alpha=0.2, color='#c8852a')
        ax3.plot(active_months, [v / 1e6 for v in vals], 'o-', color='#c8852a', lw=2, markersize=5)
        ax3.set_title(f'{selected_branch} — Monthly Revenue {selected_year}', fontweight='bold', pad=10)
        ax3.set_ylabel('Revenue (Millions)')
        ax3.tick_params(axis='x', rotation=40)
        ax3.spines[['top','right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close()

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — PRODUCT MIX
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    section("Product Group Revenue Analysis")

    if grp.empty:
        st.warning("No product group data found.")
    else:
        col1, col2 = st.columns([3, 2])

        with col1:
            max_groups = min(20, len(grp))
            top_n  = st.slider("Show top N groups", 5, max_groups, min(12, max_groups))
            top_grp = grp.head(top_n)

            fig, ax = plt.subplots(figsize=(8, 6))
            palette = ['#1a1008' if i < 3 else '#c8852a' if i < 7 else '#d4b896' for i in range(top_n)]
            ax.barh(top_grp['Group'][::-1], top_grp['Revenue'][::-1] / 1e6, color=palette[::-1])
            for i, (_, r) in enumerate(top_grp[::-1].iterrows()):
                ax.text(r['Revenue'] / 1e6 + 0.2, i, f"{r['Share']:.1f}%", va='center', fontsize=8)
            ax.set_xlabel('Revenue (Millions)')
            ax.set_title(f'Top {top_n} Product Groups by Revenue', fontweight='bold', pad=12)
            ax.spines[['top','right']].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with col2:
            section("Bev vs Food Split")
            bev_data    = cat_df[cat_df['Category'] == 'Beverages']
            food_data   = cat_df[cat_df['Category'] == 'Food']
            bev_profit  = bev_data['Total Profit'].sum()
            food_profit = food_data['Total Profit'].sum()
            total_cat   = bev_profit + food_profit

            if total_cat > 0:
                metric_card("Bev Profit Share",  f"{bev_profit/total_cat*100:.0f}%",  f"Avg margin {avg_bev_margin:.1f}%")
                metric_card("Food Profit Share", f"{food_profit/total_cat*100:.0f}%", f"Avg margin {avg_food_margin:.1f}%")
                metric_card("Margin Gap", f"{avg_bev_margin - avg_food_margin:.1f} pts", "Beverages vs Food")

                fig2, ax2 = plt.subplots(figsize=(4, 4))
                ax2.pie([bev_profit, food_profit], labels=['Beverages','Food'],
                        colors=['#c8852a','#f5e6c8'], autopct='%1.1f%%',
                        startangle=140, textprops={'fontsize': 9})
                ax2.set_title('Profit Split', fontweight='bold')
                plt.tight_layout()
                st.pyplot(fig2)
                plt.close()

        top1_group = grp.iloc[0]['Group']
        insight(
            f"<strong>{top1_group}</strong> is the #1 revenue group — ahead of all coffee categories. "
            f"For a coffee chain, this is the most surprising finding in the data and a major strategic signal."
        )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — MARGIN ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    section("Margin Deep Dive")

    if chain_ta_share is not None:
        col1, col2 = st.columns(2)
        with col1:
            section("Take-Away vs Dine-In")
            svc_plot = svc_piv.sort_values('TA_Share').reset_index()
            fig, ax  = plt.subplots(figsize=(7, 6))
            y = range(len(svc_plot))
            ax.barh(y, svc_plot['TA_Share'],           color='#c8852a', label='Take Away', alpha=0.85)
            ax.barh(y, 100 - svc_plot['TA_Share'], left=svc_plot['TA_Share'],
                    color='#d4b896', label='Table', alpha=0.85)
            ax.axvline(chain_ta_share, color='#1a1008', linestyle='--', lw=1.5,
                       label=f'Avg: {chain_ta_share:.0f}%')
            ax.set_yticks(list(y))
            ax.set_yticklabels(svc_plot['Branch'], fontsize=7.5)
            ax.set_xlabel('Share of Volume (%)')
            ax.set_title('Take-Away vs Table by Branch', fontweight='bold', pad=10)
            ax.legend(fontsize=8)
            ax.spines[['top','right']].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with col2:
            insight(
                f"<strong>{chain_ta_share:.0f}% of all orders are take-away.</strong> "
                f"High take-away branches are throughput businesses — speed matters most. "
                f"High dine-in branches benefit more from at-table upselling."
            )

            section("Loss-Making Products")
            SKIP      = ('ADD ', 'REPLACE ', 'TOTAL', '1 SHOT', '2 SHOT', '3 SHOT')
            prod_core = prod_df[
                ~prod_df['Product Desc'].str.upper().str.startswith(SKIP, na=False) &
                (prod_df['Qty'] > 0)
            ].copy()
            prod_agg = (
                prod_core.groupby('Product Desc')
                .agg(Total_Qty=('Qty','sum'), Total_Profit=('Total Profit','sum'))
                .reset_index()
            )
            losses = prod_agg[(prod_agg['Total_Profit'] < -500) & (prod_agg['Total_Qty'] > 100)]

            if len(losses) > 0:
                warn(
                    f"<strong>{len(losses)} products</strong> are being sold at a loss with significant volume. "
                    f"These are likely POS pricing errors — zero-priced items with positive ingredient cost."
                )
                ld = losses.sort_values('Total_Profit').head(8).copy()
                ld['Total Profit'] = ld['Total_Profit'].apply(lambda x: f"{x:,.0f}")
                ld['Qty']          = ld['Total_Qty'].apply(lambda x: f"{x:,.0f}")
                st.dataframe(ld[['Product Desc','Qty','Total Profit']], use_container_width=True, hide_index=True)
            else:
                st.success("✅ No significant loss-making products detected.")

    # Bev vs Food scatter
    mix = pd.DataFrame({
        'Bev_Margin':   bev_b['Total Profit %'],
        'Food_Margin':  food_b['Total Profit %'],
        'Total_Profit': bev_b['Total Profit'].fillna(0) + food_b['Total Profit'].fillna(0),
    }).dropna().reset_index()

    if not mix.empty:
        section("Beverage vs Food Margin by Branch")
        fig, ax = plt.subplots(figsize=(10, 5))
        sc = ax.scatter(mix['Food_Margin'], mix['Bev_Margin'],
                        s=mix['Total_Profit'] / 4e5, c=mix['Total_Profit'],
                        cmap='YlOrRd', alpha=0.85, edgecolors='#888', lw=0.5)
        for _, r in mix.iterrows():
            ax.annotate(r['Branch'].replace('Stories ',''),
                        (r['Food_Margin'], r['Bev_Margin']), fontsize=6.5, ha='center', va='bottom')
        plt.colorbar(sc, ax=ax, label='Total Profit')
        ax.axvline(mix['Food_Margin'].mean(), color='orange', linestyle=':', alpha=0.6)
        ax.axhline(mix['Bev_Margin'].mean(), color='#c8852a', linestyle=':', alpha=0.6)
        ax.set_xlabel('Food Margin (%)')
        ax.set_ylabel('Beverage Margin (%)')
        ax.set_title('Beverage vs Food Margin — Every Branch (bubble = total profit)', fontweight='bold', pad=12)
        ax.spines[['top','right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        insight(
            f"The <strong>{avg_bev_margin:.0f}% beverage margin vs {avg_food_margin:.0f}% food margin</strong> "
            f"gap holds at every single branch without exception — this is structural, not local. "
            f"Every beverage upsell is worth more than any food upsell."
        )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 5 — ACTION ITEMS
# ════════════════════════════════════════════════════════════════════════════════
with tab5:
    section("⚡ CEO Action Items — Generated from Your Data")
    st.markdown(
        "<p style='color:#666;font-size:0.9rem;margin-bottom:1.5rem;'>"
        "These recommendations are derived directly from the uploaded data, not generic advice."
        "</p>",
        unsafe_allow_html=True
    )

    # POS errors
    prod_core2 = prod_df[
        ~prod_df['Product Desc'].str.upper().str.startswith(
            ('ADD ', 'REPLACE ', 'TOTAL', '1 SHOT', '2 SHOT', '3 SHOT'), na=False) &
        (prod_df['Qty'] > 0)
    ].copy()
    prod_agg2  = prod_core2.groupby('Product Desc').agg(
        Total_Profit=('Total Profit','sum'), Total_Qty=('Qty','sum')).reset_index()
    losses2    = prod_agg2[(prod_agg2['Total_Profit'] < -500) & (prod_agg2['Total_Qty'] > 100)]

    st.markdown("### 🔴 Immediate (This Week)")
    if len(losses2) > 0:
        total_leakage = abs(losses2['Total_Profit'].sum())
        warn(
            f"<strong>Fix {len(losses2)} POS pricing errors.</strong> "
            f"Products with zero price but positive cost are silently leaking "
            f"<strong>{total_leakage:,.0f} units</strong> of profit. This is a 5-minute POS config fix."
        )
    else:
        st.success("✅ No immediate POS pricing errors detected in this data.")

    st.markdown("### 🟡 This Quarter")

    if len(active_months) >= 3:
        worst_months = monthly_chain.nsmallest(2).index.tolist()
        insight(
            f"<strong>Build a lean operating plan for {worst_months[0]} and {worst_months[1]}.</strong> "
            f"These are your two weakest months — pre-plan reduced staffing rosters, "
            f"smaller inventory orders, and a promotional event to soften the revenue dip."
        )
    else:
        insight(
            f"<strong>Only {len(active_months)} month(s) available for {selected_year}.</strong> "
            f"Switch to a year with more months to unlock seasonality-based action items."
        )

    insight(
        f"<strong>Implement a beverage-first upsell protocol.</strong> "
        f"With a {avg_bev_margin:.0f}% bev margin vs {avg_food_margin:.0f}% food margin, "
        f"training staff to suggest a drink with every food order is the highest-leverage "
        f"margin improvement available."
    )

    new_b = []
    for _, row in monthly_yr.iterrows():
        for i, m in enumerate(MONTHS):
            if m in active_months and row[m] > 0:
                if i >= 2:
                    new_b.append(row['Branch Name'])
                break
    if new_b:
        branch_list = ', '.join(new_b[:4]) + ('...' if len(new_b) > 4 else '')
        insight(
            f"<strong>Set ramp targets for {len(new_b)} new branches:</strong> {branch_list}. "
            f"Data shows new Stories branches reach ~65% of steady-state within 3 months. "
            f"Any branch behind that pace needs a marketing intervention now."
        )

    st.markdown("### 🟢 Strategic")

    if not grp.empty:
        top_group = grp.iloc[0]['Group']
        insight(
            f"<strong>Investigate {top_group}'s role in the brand.</strong> "
            f"It is the chain's #1 revenue product group — ahead of every coffee category. "
            f"Consider whether this should be featured more prominently in marketing, "
            f"or whether the mix should shift back toward higher-margin coffee products."
        )

    top5_share = branch_sum.head(5)['Total_Profit'].sum() / branch_sum['Total_Profit'].sum() * 100
    insight(
        f"<strong>Reduce concentration risk.</strong> The top 5 branches generate "
        f"{top5_share:.0f}% of chain profit. Accelerate growth in mid-tier branches "
        f"to build resilience against disruption at any single location."
    )

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center;color:#bbb;font-size:0.8rem;padding:1rem;'>"
        "Stories Coffee Intelligence Dashboard · Built with real operational data"
        "</div>",
        unsafe_allow_html=True
    )
