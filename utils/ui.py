"""UI helper components for the cost monitoring dashboard."""

import streamlit as st


def freshness_tag(level: str) -> str:
    colors = {
        "live": "#3DD68C",
        "~45min": "#F0B03E",
        "~1-3h": "#FF8C00",
        "next-day": "#E85D56",
    }
    color = colors.get(level, "#999999")
    return f'<span style="background:{color};color:#000;padding:2px 8px;border-radius:4px;font-size:0.75em;font-weight:600;">{level}</span>'


def data_sources_sidebar(page: str):
    AU = "SNOWFLAKE.ACCOUNT_USAGE"
    page_sources = {
        "overview": {
            "title": "Overview",
            "sources": [
                {"name": "BUDGET_DETAILS", "schema": AU, "type": "view", "latency": "Minutes", "latencyLevel": "live", "note": "Reflects spending changes within a few minutes of credit consumption."},
                {"name": "METERING_DAILY_HISTORY", "schema": AU, "type": "view", "latency": "Next calendar day", "latencyLevel": "next-day", "note": "Daily rollup per service type. Rows for today appear the following day."},
                {"name": "WAREHOUSE_METERING_HISTORY", "schema": AU, "type": "view", "latency": "~45 minutes", "latencyLevel": "~45min", "note": "Hourly credit rows land ~45 min after the hour closes."},
                {"name": "CORTEX_AI_FUNCTIONS_USAGE_HISTORY", "schema": AU, "type": "view", "latency": "~45 minutes", "latencyLevel": "~45min", "note": "One row per completed AI function call. Includes token counts per model."},
                {"name": "SHOW RESOURCE MONITORS", "type": "command", "latency": "Real-time", "latencyLevel": "live", "note": "DDL command — always reflects the current account state."},
            ],
        },
        "warehouses": {
            "title": "Warehouses",
            "sources": [
                {"name": "WAREHOUSE_METERING_HISTORY", "schema": "<db>.INFORMATION_SCHEMA", "type": "table-function", "latency": "Real-time", "latencyLevel": "live", "note": "TVF updated as queries complete — not hourly. Covers the last 14 days."},
                {"name": "SHOW WAREHOUSES", "type": "command", "latency": "Real-time", "latencyLevel": "live", "note": "Returns live state: STARTED/SUSPENDED, running queries, queue depth."},
            ],
        },
        "ai_usage": {
            "title": "AI Usage",
            "sources": [
                {"name": "CORTEX_AI_FUNCTIONS_USAGE_HISTORY", "schema": AU, "type": "view", "latency": "~45 minutes", "latencyLevel": "~45min", "note": "Covers AI_COMPLETE, AI_CLASSIFY, AI_EXTRACT, AI_SUMMARIZE etc. Token counts stored in METRICS array."},
                {"name": "CORTEX_AGENT_USAGE_HISTORY", "schema": AU, "type": "view", "latency": "~45 minutes", "latencyLevel": "~45min", "note": "One row per Cortex Agent session. Includes TOKEN_CREDITS and raw TOKENS."},
                {"name": "SNOWFLAKE_COCO_USAGE_HISTORY", "schema": AU, "type": "view", "latency": "~45 minutes", "latencyLevel": "~45min", "note": "Cortex Code (CLI, Desktop, Snowsight) usage per user per request."},
            ],
        },
        "users": {
            "title": "Users",
            "sources": [
                {"name": "QUERY_METERING_HISTORY", "schema": AU, "type": "view", "latency": "~minutes", "latencyLevel": "live", "note": "Per-query compute credit attribution with USER_NAME."},
                {"name": "QUERY_HISTORY", "schema": AU, "type": "view", "latency": "~45 minutes", "latencyLevel": "~45min", "note": "Query count and elapsed time per user."},
                {"name": "CORTEX_AI_FUNCTIONS_USAGE_HISTORY", "schema": AU, "type": "view", "latency": "~45 minutes", "latencyLevel": "~45min", "note": "Joined to USERS via USER_ID to resolve a display name."},
                {"name": "CORTEX_AGENT_USAGE_HISTORY", "schema": AU, "type": "view", "latency": "~45 minutes", "latencyLevel": "~45min"},
                {"name": "SNOWFLAKE_COCO_USAGE_HISTORY", "schema": AU, "type": "view", "latency": "~45 minutes", "latencyLevel": "~45min"},
            ],
        },
        "limits": {
            "title": "Limits",
            "sources": [
                {"name": "SHOW RESOURCE MONITORS", "type": "command", "latency": "Real-time", "latencyLevel": "live", "note": "Current credit quota, consumed credits, and trigger thresholds."},
                {"name": "BUDGET_DETAILS", "schema": AU, "type": "view", "latency": "Minutes", "latencyLevel": "live", "note": "Account-level monthly budget."},
                {"name": "QUOTA_ACCESS_BLOCK_HISTORY", "schema": AU, "type": "view", "latency": "~45 minutes", "latencyLevel": "~45min", "note": "Records each time a user was blocked due to a per-user credit quota."},
            ],
        },
    }

    sources = page_sources.get(page)
    if not sources:
        return

    with st.sidebar.expander("Data Sources", expanded=False):
        st.markdown(f"**{sources['title']}**")
        for src in sources["sources"]:
            schema_str = f" ({src['schema']})" if src.get("schema") else ""
            badge = freshness_tag(src["latencyLevel"])
            st.markdown(
                f"{badge} **{src['name']}**{schema_str}  \n"
                f"*{src.get('note', '')}*",
                unsafe_allow_html=True,
            )


def metric_card(label: str, value: str, freshness: str = None):
    st.metric(label=label, value=value)
    if freshness:
        st.markdown(freshness_tag(freshness), unsafe_allow_html=True)


def budget_progress_bar(used: float, total: float, label: str = ""):
    if total <= 0:
        pct = 0.0
    else:
        pct = min(used / total, 1.0)

    if pct >= 0.9:
        color = "#E85D56"
    elif pct >= 0.75:
        color = "#FF8C00"
    elif pct >= 0.5:
        color = "#F0B03E"
    else:
        color = "#3DD68C"

    st.progress(pct)
    st.markdown(
        f'<span style="color:{color};font-weight:600;">{label} — {pct*100:.1f}% used</span>',
        unsafe_allow_html=True,
    )
