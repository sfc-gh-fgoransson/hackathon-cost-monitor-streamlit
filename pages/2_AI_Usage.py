import streamlit as st
import altair as alt
import pandas as pd

from utils.connection import run_query
from utils.ui import freshness_tag, data_sources_sidebar
from utils.queries import get_ai_function_usage, get_agent_usage, get_coco_usage

st.set_page_config(page_title="AI Usage", page_icon=":snowflake:", layout="wide")

data_sources_sidebar("ai_usage")

st.title("AI & Cortex Usage")

# Section 1: Tokens by Model
st.subheader("Tokens by Model")
st.markdown(freshness_tag("~45min"), unsafe_allow_html=True)

try:
    df_functions = run_query(get_ai_function_usage["sql"], ttl=300)
    if df_functions.empty:
        st.info("No AI function usage data available for the last 7 days.")
    else:
        # Group by model, sum input/output tokens
        df_by_model = df_functions.groupby("MODEL_NAME", as_index=False).agg(
            {"INPUT_TOKENS": "sum", "OUTPUT_TOKENS": "sum"}
        )

        # Melt to long format for grouped bar chart
        df_tokens_long = df_by_model.melt(
            id_vars=["MODEL_NAME"],
            value_vars=["INPUT_TOKENS", "OUTPUT_TOKENS"],
            var_name="Token Type",
            value_name="Tokens",
        )
        df_tokens_long["Token Type"] = df_tokens_long["Token Type"].map(
            {"INPUT_TOKENS": "Input", "OUTPUT_TOKENS": "Output"}
        )

        chart = (
            alt.Chart(df_tokens_long)
            .mark_bar()
            .encode(
                x=alt.X("MODEL_NAME:N", title="Model", sort="-y"),
                y=alt.Y("Tokens:Q", title="Token Count"),
                color=alt.Color(
                    "Token Type:N",
                    scale=alt.Scale(
                        domain=["Input", "Output"],
                        range=["#29B5E8", "#3DD68C"],
                    ),
                ),
                xOffset="Token Type:N",
                tooltip=["MODEL_NAME:N", "Token Type:N", "Tokens:Q"],
            )
            .properties(height=400)
        )
        st.altair_chart(chart, width="stretch")
except Exception as e:
    st.error(f"Error loading AI function usage: {e}")

# Section 2: Credits by AI Service
st.subheader("Credits by AI Service")
st.markdown(freshness_tag("~45min"), unsafe_allow_html=True)

try:
    frames = []

    df_fn = run_query(get_ai_function_usage["sql"], ttl=300)
    if not df_fn.empty:
        fn_credits = df_fn["CREDITS"].sum()
        frames.append({"Service": "AI Functions", "Credits": fn_credits})

    df_agents = run_query(get_agent_usage["sql"], ttl=300)
    if not df_agents.empty:
        agent_credits = df_agents["CREDITS"].sum()
        frames.append({"Service": "Cortex Agents", "Credits": agent_credits})

    df_coco = run_query(get_coco_usage["sql"], ttl=300)
    if not df_coco.empty:
        coco_credits = df_coco["CREDITS"].sum()
        frames.append({"Service": "Cortex Code", "Credits": coco_credits})

    if frames:
        df_services = pd.DataFrame(frames)

        chart = (
            alt.Chart(df_services)
            .mark_bar()
            .encode(
                x=alt.X("Credits:Q", title="Credits"),
                y=alt.Y("Service:N", sort="-x", title=""),
                color=alt.Color(
                    "Service:N",
                    scale=alt.Scale(range=["#29B5E8", "#3DD68C", "#9B8FFF"]),
                    legend=None,
                ),
                tooltip=["Service:N", "Credits:Q"],
            )
            .properties(height=200)
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.info("No AI service usage data available for the last 7 days.")
except Exception as e:
    st.error(f"Error loading AI service credits: {e}")

# Section 3: Per-User AI Usage
st.subheader("Per-User AI Usage")
st.markdown(freshness_tag("~45min"), unsafe_allow_html=True)

try:
    user_frames = []

    df_agents = run_query(get_agent_usage["sql"], ttl=300)
    if not df_agents.empty:
        agent_users = df_agents.rename(
            columns={"TOTAL_TOKENS": "TOKENS", "CREDITS": "TOKEN_CREDITS"}
        )[["USER_NAME", "TOKENS", "TOKEN_CREDITS"]]
        user_frames.append(agent_users)

    df_coco = run_query(get_coco_usage["sql"], ttl=300)
    if not df_coco.empty:
        coco_users = df_coco.rename(
            columns={"TOTAL_TOKENS": "TOKENS", "CREDITS": "TOKEN_CREDITS"}
        )[["USER_NAME", "TOKENS", "TOKEN_CREDITS"]]
        user_frames.append(coco_users)

    if user_frames:
        df_all_users = pd.concat(user_frames, ignore_index=True)
        df_merged = df_all_users.groupby("USER_NAME", as_index=False).agg(
            {"TOKENS": "sum", "TOKEN_CREDITS": "sum"}
        )
        df_merged = df_merged.sort_values("TOKEN_CREDITS", ascending=False)
        df_merged.columns = ["User", "Tokens", "Credits"]
        st.dataframe(df_merged, width="stretch", hide_index=True)
    else:
        st.info("No per-user AI usage data available for the last 7 days.")
except Exception as e:
    st.error(f"Error loading per-user AI usage: {e}")
