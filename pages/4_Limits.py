import streamlit as st

from utils.connection import run_query, run_ddl
from utils.ui import freshness_tag, data_sources_sidebar, budget_progress_bar
from utils import queries
from utils.queries import create_resource_monitor_sql

st.set_page_config(page_title="Limits - Cost Monitor", page_icon=":snowflake:", layout="wide")

data_sources_sidebar("limits")

st.title("Limits & Monitors")

# --- Section 1: Account Budget ---
st.subheader("Account Budget")
st.markdown(freshness_tag("live"), unsafe_allow_html=True)

try:
    budget_df = run_query(queries.get_budget_details["sql"], ttl=60)
    if not budget_df.empty:
        for _, row in budget_df.iterrows():
            budget_progress_bar(
                float(row["CURRENT_MONTH_SPENDING"] or 0),
                float(row["CREDIT_LIMIT"] or 0),
                row["BUDGET_NAME"],
            )
    else:
        st.info("No budget data available.")
except Exception:
    st.info("Unable to load budget data.")


# --- Section 2: Resource Monitors (auto-refresh) ---
@st.fragment(run_every=30)
def monitors_section():
    st.subheader("Resource Monitors")
    st.markdown(freshness_tag("live"), unsafe_allow_html=True)

    try:
        monitors_df = run_query(queries.get_resource_monitors["sql"], ttl=30)
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


monitors_section()


# --- Section 3: Create Resource Monitor ---
with st.expander("Create Resource Monitor"):
    with st.form("create_monitor_form"):
        name = st.text_input("Monitor Name")
        credit_quota = st.number_input("Credit Quota", min_value=1, value=100)
        notify_at = st.number_input("Notify At %", min_value=0, max_value=100, value=75)
        suspend_at = st.number_input("Suspend At %", min_value=0, max_value=100, value=95)
        suspend_imm_at = st.number_input("Suspend Immediately At %", min_value=0, max_value=100, value=100)
        submitted = st.form_submit_button("Create Monitor")

        if submitted:
            if not name.strip():
                st.error("Monitor name is required.")
            else:
                sql = create_resource_monitor_sql(
                    name=name.strip(),
                    credit_quota=int(credit_quota),
                    notify_at=[int(notify_at)] if notify_at > 0 else None,
                    suspend_at=int(suspend_at) if suspend_at > 0 else None,
                    suspend_immediate_at=int(suspend_imm_at) if suspend_imm_at > 0 else None,
                )
                try:
                    run_ddl(sql)
                    st.success(f"Resource monitor '{name}' created successfully.")
                except Exception as e:
                    st.error(f"Failed to create monitor: {e}")


# --- Section 4: Quota Block History ---
st.subheader("Quota Block History (30d)")
st.markdown(freshness_tag("~45min"), unsafe_allow_html=True)

try:
    quota_df = run_query(queries.get_quota_block_history["sql"], ttl=300)
    if not quota_df.empty:
        st.dataframe(quota_df, width="stretch")
    else:
        st.info("No quota blocks recorded in the last 30 days.")
except Exception:
    st.info("Unable to load quota block history.")
