import streamlit as st
import altair as alt

from utils.connection import run_query
from utils.ui import freshness_tag, data_sources_sidebar, budget_progress_bar, metric_card
from utils import queries

st.set_page_config(page_title="Cost Monitor", page_icon=":snowflake:", layout="wide")

data_sources_sidebar("overview")

st.title("Overview")

# --- Row 1: Top-level metrics ---
try:
    budget_df = run_query(queries.get_summary_budget["sql"], ttl=60)
except Exception:
    budget_df = None

try:
    daily_credits_df = run_query(queries.get_summary_daily_credits["sql"], ttl=600)
except Exception:
    daily_credits_df = None

try:
    ai_summary_df = run_query(queries.get_ai_summary_tokens["sql"], ttl=300)
except Exception:
    ai_summary_df = None

col1, col2, col3, col4 = st.columns(4)

with col1:
    if daily_credits_df is not None and not daily_credits_df.empty:
        total_credits = daily_credits_df["CREDITS"].sum()
        metric_card("Credits This Week", f"{total_credits:,.1f}", "~45min")
    else:
        metric_card("Credits This Week", "—", "~45min")

with col2:
    if budget_df is not None and not budget_df.empty:
        month_spend = budget_df.iloc[0]["CURRENT_MONTH_SPENDING"]
        metric_card("Credits This Month", f"{month_spend:,.1f}", "live")
    else:
        metric_card("Credits This Month", "—", "live")

with col3:
    if ai_summary_df is not None and not ai_summary_df.empty:
        input_tokens = ai_summary_df.iloc[0]["INPUT_TOKENS"] or 0
        output_tokens = ai_summary_df.iloc[0]["OUTPUT_TOKENS"] or 0
        total_tokens = input_tokens + output_tokens
        metric_card("AI Tokens (7d)", f"{total_tokens:,.0f}", "~45min")
    else:
        metric_card("AI Tokens (7d)", "—", "~45min")

with col4:
    if budget_df is not None and not budget_df.empty:
        pct = budget_df.iloc[0]["PCT_USED"] or 0
        metric_card("Budget Used %", f"{pct:.1f}%", "live")
    else:
        metric_card("Budget Used %", "—", "live")

# --- Row 2: Budget progress bar ---
if budget_df is not None and not budget_df.empty:
    row = budget_df.iloc[0]
    budget_progress_bar(
        float(row["CURRENT_MONTH_SPENDING"] or 0),
        float(row["CREDIT_LIMIT"] or 0),
        row["BUDGET_NAME"],
    )

# --- Row 3: Credits by service type ---
st.subheader("Credits by Service Type (7d)")
st.markdown(freshness_tag("next-day"), unsafe_allow_html=True)

if daily_credits_df is not None and not daily_credits_df.empty:
    top10 = daily_credits_df.head(10)
    chart = (
        alt.Chart(top10)
        .mark_bar()
        .encode(
            x=alt.X("CREDITS:Q", title="Credits"),
            y=alt.Y("SERVICE_TYPE:N", sort="-x", title="Service Type"),
            color=alt.value("#29B5E8"),
        )
        .properties(height=300)
    )
    st.altair_chart(chart, width="stretch")
else:
    st.info("No service credit data available for the last 7 days.")

# --- Row 4: Top warehouses + AI tokens ---
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Top 5 Warehouses (7d)")
    st.markdown(freshness_tag("~45min"), unsafe_allow_html=True)
    try:
        wh_df = run_query(queries.get_top_warehouses["sql"], ttl=300)
        if not wh_df.empty:
            chart = (
                alt.Chart(wh_df)
                .mark_bar()
                .encode(
                    x=alt.X("CREDITS:Q", title="Credits"),
                    y=alt.Y("WAREHOUSE_NAME:N", sort="-x", title="Warehouse"),
                    color=alt.value("#29B5E8"),
                )
                .properties(height=200)
            )
            st.altair_chart(chart, width="stretch")
        else:
            st.info("No warehouse data available.")
    except Exception:
        st.info("Unable to load warehouse data.")

with right_col:
    st.subheader("AI Tokens by Model (7d)")
    st.markdown(freshness_tag("~45min"), unsafe_allow_html=True)
    try:
        ai_model_df = run_query(queries.get_ai_function_usage["sql"], ttl=300)
        if not ai_model_df.empty:
            ai_model_df["TOTAL_TOKENS"] = ai_model_df["INPUT_TOKENS"].fillna(0) + ai_model_df["OUTPUT_TOKENS"].fillna(0)
            chart = (
                alt.Chart(ai_model_df.head(10))
                .mark_bar()
                .encode(
                    x=alt.X("TOTAL_TOKENS:Q", title="Tokens"),
                    y=alt.Y("MODEL_NAME:N", sort="-x", title="Model"),
                    color=alt.value("#F0B03E"),
                )
                .properties(height=200)
            )
            st.altair_chart(chart, width="stretch")
        else:
            st.info("No AI function usage data available.")
    except Exception:
        st.info("Unable to load AI usage data.")


# --- Row 5: Resource Monitors (auto-refresh) ---
@st.fragment(run_every=30)
def resource_monitors_section():
    st.subheader("Resource Monitors")
    st.caption("Resource monitors refresh every 30s")
    st.markdown(freshness_tag("live"), unsafe_allow_html=True)

    try:
        monitors_df = run_query(queries.get_summary_resource_monitors["sql"], ttl=30)
        if monitors_df.empty:
            st.info("No resource monitors configured.")
            return

        cols = st.columns(min(len(monitors_df), 4))
        for i, (_, row) in enumerate(monitors_df.iterrows()):
            with cols[i % len(cols)]:
                name = row.get("name", "Unknown")
                credit_quota = float(row.get("credit_quota", 0) or 0)
                credits_used = float(row.get("credits_used", 0) or 0)

                st.markdown(f"**{name}**")
                if credit_quota > 0:
                    pct = min(credits_used / credit_quota, 1.0)
                    st.progress(pct)
                    st.text(f"{credits_used:,.1f} / {credit_quota:,.1f} credits")
                else:
                    st.progress(0.0)
                    st.text("No quota set")

                suspend_at = row.get("suspend_at", None)
                suspend_imm_at = row.get("suspend_immediately_at", None)
                thresholds = []
                if suspend_at:
                    thresholds.append(f"Suspend: {suspend_at}%")
                if suspend_imm_at:
                    thresholds.append(f"Immediate: {suspend_imm_at}%")
                if thresholds:
                    st.caption(" | ".join(thresholds))
    except Exception:
        st.info("Unable to load resource monitors.")


resource_monitors_section()
