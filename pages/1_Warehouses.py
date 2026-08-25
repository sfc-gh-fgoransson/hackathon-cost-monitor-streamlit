import streamlit as st
import altair as alt

from utils.connection import run_query
from utils.ui import freshness_tag, data_sources_sidebar
from utils.queries import get_warehouse_metering, get_warehouses

st.set_page_config(page_title="Warehouses", page_icon=":snowflake:", layout="wide")

data_sources_sidebar("warehouses")

st.title("Warehouses")

# Section 1: Hourly Credits (Last 7 Days)
st.subheader("Hourly Credits (Last 7 Days)")
st.markdown(freshness_tag("live"), unsafe_allow_html=True)

try:
    df_metering = run_query(get_warehouse_metering["sql"], ttl=60)
    if df_metering.empty:
        st.info("No warehouse metering data available for the last 7 days.")
    else:
        snowsight_palette = ["#29B5E8", "#3DD68C", "#F0B03E", "#E85D56", "#9B8FFF"]

        chart = (
            alt.Chart(df_metering)
            .mark_line(strokeWidth=2)
            .encode(
                x=alt.X("HOUR:T", title="Hour"),
                y=alt.Y("CREDITS:Q", title="Credits Used"),
                color=alt.Color(
                    "WAREHOUSE_NAME:N",
                    title="Warehouse",
                    scale=alt.Scale(range=snowsight_palette),
                ),
                tooltip=["WAREHOUSE_NAME:N", "HOUR:T", "CREDITS:Q"],
            )
            .properties(height=400)
            .interactive()
        )
        st.altair_chart(chart, width="stretch")
except Exception as e:
    st.error(f"Error loading warehouse metering data: {e}")

# Section 2: Warehouse State
st.subheader("Warehouse State")
st.markdown(freshness_tag("live"), unsafe_allow_html=True)

try:
    df_warehouses = run_query(get_warehouses["sql"], ttl=30)
    if df_warehouses.empty:
        st.info("No warehouses found.")
    else:
        # Normalize column names (SHOW returns lowercase in some cases)
        df_warehouses.columns = [c.lower() for c in df_warehouses.columns]

        display_cols = []
        for col in ["name", "state", "size", "running", "queued", "resource_monitor"]:
            if col in df_warehouses.columns:
                display_cols.append(col)

        if display_cols:
            df_display = df_warehouses[display_cols].copy()

            # Add colored state badges
            def state_badge(state):
                if state and str(state).upper() == "STARTED":
                    return f"🟢 {state}"
                return f"⚪ {state}"

            if "state" in df_display.columns:
                df_display["state"] = df_display["state"].apply(state_badge)

            st.dataframe(df_display, width="stretch", hide_index=True)
        else:
            st.dataframe(df_warehouses, width="stretch", hide_index=True)
except Exception as e:
    st.error(f"Error loading warehouse state: {e}")
