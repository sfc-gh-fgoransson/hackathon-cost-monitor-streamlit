import streamlit as st
import pandas as pd

from utils.connection import run_query
from utils.ui import freshness_tag, data_sources_sidebar
from utils import queries

st.set_page_config(page_title="Users - Cost Monitor", page_icon=":snowflake:", layout="wide")

data_sources_sidebar("users")

st.title("Users")

period = st.radio("Period", ["24h", "7d"], horizontal=True)

# Select queries based on period
if period == "24h":
    activity_q = queries.get_user_activity_24h
    ai_q = queries.get_user_ai_usage_24h
    compute_q = queries.get_user_compute_credits_24h
else:
    activity_q = queries.get_user_activity_7d
    ai_q = queries.get_user_ai_usage_7d
    compute_q = queries.get_user_compute_credits_7d

# Fetch data
try:
    activity_df = run_query(activity_q["sql"], ttl=300)
except Exception:
    activity_df = pd.DataFrame()

try:
    ai_df = run_query(ai_q["sql"], ttl=300)
except Exception:
    ai_df = pd.DataFrame()

try:
    compute_df = run_query(compute_q["sql"], ttl=300)
except Exception:
    compute_df = pd.DataFrame()

# Merge all three on USER_NAME
if not activity_df.empty:
    merged = activity_df.copy()
    merged["ELAPSED_S"] = (merged["TOTAL_ELAPSED_MS"].fillna(0) / 1000).round(1)
else:
    merged = pd.DataFrame(columns=["USER_NAME", "QUERY_COUNT", "WAREHOUSES_USED", "ELAPSED_S"])

if not compute_df.empty:
    merged = merged.merge(compute_df[["USER_NAME", "COMPUTE_CREDITS"]], on="USER_NAME", how="left")
else:
    merged["COMPUTE_CREDITS"] = 0.0

if not ai_df.empty:
    merged = merged.merge(ai_df[["USER_NAME", "AI_TOKENS", "AI_CREDITS"]], on="USER_NAME", how="left")
else:
    merged["AI_TOKENS"] = 0.0
    merged["AI_CREDITS"] = 0.0

merged = merged.fillna(0)

# Display
if not merged.empty:
    display_df = merged.rename(columns={
        "USER_NAME": "User",
        "QUERY_COUNT": "Queries",
        "WAREHOUSES_USED": "Warehouses",
        "ELAPSED_S": "Elapsed (s)",
        "COMPUTE_CREDITS": "Compute Credits",
        "AI_TOKENS": "AI Tokens",
        "AI_CREDITS": "AI Credits",
    })[["User", "Queries", "Warehouses", "Elapsed (s)", "Compute Credits", "AI Tokens", "AI Credits"]]

    st.markdown(
        f"Compute Credits {freshness_tag('live')} &nbsp; AI Usage {freshness_tag('~45min')}",
        unsafe_allow_html=True,
    )

    st.dataframe(
        display_df, width="stretch",
        column_config={
            "User": st.column_config.TextColumn("User"),
            "Queries": st.column_config.NumberColumn("Queries", format="%d"),
            "Warehouses": st.column_config.NumberColumn("Warehouses", format="%d"),
            "Elapsed (s)": st.column_config.NumberColumn("Elapsed (s)", format="%.1f"),
            "Compute Credits": st.column_config.NumberColumn("Compute Credits", format="%.2f"),
            "AI Tokens": st.column_config.NumberColumn("AI Tokens", format="%d"),
            "AI Credits": st.column_config.NumberColumn("AI Credits", format="%.4f"),
        },
    )
else:
    st.info("No user activity data available for this period.")

st.caption("Note: Compute Credits may show 0 if QUERY_METERING_HISTORY is not enabled on this account.")
