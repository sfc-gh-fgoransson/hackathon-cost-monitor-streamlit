import os
import streamlit as st
import pandas as pd


@st.cache_resource
def get_connection():
    connection_name = os.environ.get("SNOWFLAKE_DEFAULT_CONNECTION_NAME", "default")
    return st.connection(connection_name, type="snowflake")


def run_query(sql: str, ttl: int = 300) -> pd.DataFrame:
    conn = get_connection()
    return conn.query(sql, ttl=ttl)


def run_ddl(sql: str):
    conn = get_connection()
    conn._instance.cursor().execute(sql)
