"""All SQL queries ported from the TypeScript source with latency metadata."""


# --- Summary queries ---

get_summary_budget = {
    "sql": """SELECT BUDGET_NAME, CREDIT_LIMIT, CURRENT_MONTH_SPENDING,
    (CURRENT_MONTH_SPENDING / NULLIF(CREDIT_LIMIT, 0) * 100) AS PCT_USED
  FROM SNOWFLAKE.ACCOUNT_USAGE.BUDGET_DETAILS
  ORDER BY CREDIT_LIMIT DESC LIMIT 1""",
    "latency": {"source": "BUDGET_DETAILS", "lag": "~minutes"},
}

get_summary_daily_credits = {
    "sql": """SELECT SERVICE_TYPE, SUM(CREDITS_USED) AS CREDITS
  FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY
  WHERE USAGE_DATE >= DATEADD('day', -7, CURRENT_DATE())
  GROUP BY SERVICE_TYPE
  ORDER BY CREDITS DESC""",
    "latency": {"source": "METERING_DAILY_HISTORY", "lag": "next day"},
}

get_summary_resource_monitors = {
    "sql": "SHOW RESOURCE MONITORS",
    "latency": {"source": "SHOW RESOURCE MONITORS", "lag": "Live"},
}

get_top_warehouses = {
    "sql": """SELECT WAREHOUSE_NAME, SUM(CREDITS_USED) AS CREDITS
  FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
  WHERE START_TIME >= DATEADD('day', -7, CURRENT_DATE())
  GROUP BY WAREHOUSE_NAME
  ORDER BY CREDITS DESC
  LIMIT 5""",
    "latency": {"source": "WAREHOUSE_METERING_HISTORY", "lag": "~45 min"},
}

get_ai_summary_tokens = {
    "sql": """SELECT
    SUM(CASE WHEN m.value:key:metric::STRING = 'input' THEN m.value:value::NUMBER ELSE 0 END) AS INPUT_TOKENS,
    SUM(CASE WHEN m.value:key:metric::STRING = 'output' THEN m.value:value::NUMBER ELSE 0 END) AS OUTPUT_TOKENS,
    SUM(CREDITS) AS CREDITS
  FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY,
    LATERAL FLATTEN(input => METRICS) m
  WHERE START_TIME >= DATEADD('day', -7, CURRENT_DATE())""",
    "latency": {"source": "CORTEX_AI_FUNCTIONS_USAGE_HISTORY", "lag": "~45 min"},
}

# --- Warehouse queries ---

get_warehouse_metering = {
    "sql": """SELECT WAREHOUSE_NAME,
    DATE_TRUNC('hour', START_TIME) AS HOUR,
    SUM(CREDITS_USED) AS CREDITS
  FROM TABLE(XIND_DATA_GEN.INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
    DATE_RANGE_START => DATEADD('day', -7, CURRENT_DATE())
  ))
  GROUP BY WAREHOUSE_NAME, HOUR
  ORDER BY HOUR""",
    "latency": {"source": "INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY", "lag": "Live"},
}

get_warehouses = {
    "sql": "SHOW WAREHOUSES",
    "latency": {"source": "SHOW WAREHOUSES", "lag": "Live"},
}

# --- AI Usage queries ---

get_ai_function_usage = {
    "sql": """SELECT MODEL_NAME, FUNCTION_NAME,
    SUM(CASE WHEN m.value:key:metric::STRING = 'input' THEN m.value:value::NUMBER ELSE 0 END) AS INPUT_TOKENS,
    SUM(CASE WHEN m.value:key:metric::STRING = 'output' THEN m.value:value::NUMBER ELSE 0 END) AS OUTPUT_TOKENS,
    SUM(CREDITS) AS CREDITS
  FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY,
    LATERAL FLATTEN(input => METRICS) m
  WHERE START_TIME >= DATEADD('day', -7, CURRENT_DATE())
  GROUP BY MODEL_NAME, FUNCTION_NAME
  ORDER BY CREDITS DESC""",
    "latency": {"source": "CORTEX_AI_FUNCTIONS_USAGE_HISTORY", "lag": "~45 min"},
}

get_agent_usage = {
    "sql": """SELECT USER_NAME,
    SUM(TOKENS) AS TOTAL_TOKENS,
    SUM(TOKEN_CREDITS) AS CREDITS
  FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
  WHERE START_TIME >= DATEADD('day', -7, CURRENT_DATE())
  GROUP BY USER_NAME
  ORDER BY CREDITS DESC""",
    "latency": {"source": "CORTEX_AGENT_USAGE_HISTORY", "lag": "~45 min"},
}

get_coco_usage = {
    "sql": """SELECT USER_NAME, INTERFACE,
    SUM(TOKENS) AS TOTAL_TOKENS,
    SUM(TOKEN_CREDITS) AS CREDITS
  FROM SNOWFLAKE.ACCOUNT_USAGE.SNOWFLAKE_COCO_USAGE_HISTORY
  WHERE USAGE_TIME >= DATEADD('day', -7, CURRENT_DATE())
  GROUP BY USER_NAME, INTERFACE
  ORDER BY CREDITS DESC""",
    "latency": {"source": "SNOWFLAKE_COCO_USAGE_HISTORY", "lag": "~45 min"},
}

# --- User Activity queries ---

get_user_activity_24h = {
    "sql": """SELECT USER_NAME,
    COUNT(*) AS QUERY_COUNT,
    COUNT(DISTINCT WAREHOUSE_NAME) AS WAREHOUSES_USED,
    SUM(TOTAL_ELAPSED_TIME) AS TOTAL_ELAPSED_MS
  FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
  WHERE START_TIME >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
  GROUP BY USER_NAME
  ORDER BY QUERY_COUNT DESC""",
    "latency": {"source": "QUERY_HISTORY", "lag": "~45 min"},
}

get_user_activity_7d = {
    "sql": """SELECT USER_NAME,
    COUNT(*) AS QUERY_COUNT,
    COUNT(DISTINCT WAREHOUSE_NAME) AS WAREHOUSES_USED,
    SUM(TOTAL_ELAPSED_TIME) AS TOTAL_ELAPSED_MS
  FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
  WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
  GROUP BY USER_NAME
  ORDER BY QUERY_COUNT DESC""",
    "latency": {"source": "QUERY_HISTORY", "lag": "~45 min"},
}

get_user_compute_credits_24h = {
    "sql": """SELECT USER_NAME,
    SUM(CREDITS_USED) AS COMPUTE_CREDITS
  FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY
  WHERE QUERY_START_TIME >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
  GROUP BY USER_NAME
  ORDER BY COMPUTE_CREDITS DESC""",
    "latency": {"source": "QUERY_METERING_HISTORY", "lag": "~minutes"},
}

get_user_compute_credits_7d = {
    "sql": """SELECT USER_NAME,
    SUM(CREDITS_USED) AS COMPUTE_CREDITS
  FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY
  WHERE QUERY_START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
  GROUP BY USER_NAME
  ORDER BY COMPUTE_CREDITS DESC""",
    "latency": {"source": "QUERY_METERING_HISTORY", "lag": "~minutes"},
}

get_user_ai_usage_24h = {
    "sql": """SELECT USER_NAME,
    SUM(TOTAL_TOKENS) AS AI_TOKENS,
    SUM(AI_CREDITS) AS AI_CREDITS
  FROM (
    SELECT u.NAME AS USER_NAME,
        SUM(CASE WHEN m.value:key:metric::STRING = 'input' THEN m.value:value::NUMBER ELSE 0 END)
        + SUM(CASE WHEN m.value:key:metric::STRING = 'output' THEN m.value:value::NUMBER ELSE 0 END) AS TOTAL_TOKENS,
        SUM(h.CREDITS) AS AI_CREDITS
      FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY h
      JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON h.USER_ID = u.USER_ID
      , LATERAL FLATTEN(input => h.METRICS) m
      WHERE h.START_TIME >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
      GROUP BY u.NAME
    UNION ALL
    SELECT USER_NAME,
        SUM(TOKENS) AS TOTAL_TOKENS, SUM(TOKEN_CREDITS) AS AI_CREDITS
      FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
      WHERE START_TIME >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
      GROUP BY USER_NAME
    UNION ALL
    SELECT USER_NAME,
        SUM(TOKENS) AS TOTAL_TOKENS, SUM(TOKEN_CREDITS) AS AI_CREDITS
      FROM SNOWFLAKE.ACCOUNT_USAGE.SNOWFLAKE_COCO_USAGE_HISTORY
      WHERE USAGE_TIME >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
      GROUP BY USER_NAME
  )
  GROUP BY USER_NAME""",
    "latency": {"source": "AI_FUNCTIONS + AGENT + COCO", "lag": "~45 min"},
}

get_user_ai_usage_7d = {
    "sql": """SELECT USER_NAME,
    SUM(TOTAL_TOKENS) AS AI_TOKENS,
    SUM(AI_CREDITS) AS AI_CREDITS
  FROM (
    SELECT u.NAME AS USER_NAME,
        SUM(CASE WHEN m.value:key:metric::STRING = 'input' THEN m.value:value::NUMBER ELSE 0 END)
        + SUM(CASE WHEN m.value:key:metric::STRING = 'output' THEN m.value:value::NUMBER ELSE 0 END) AS TOTAL_TOKENS,
        SUM(h.CREDITS) AS AI_CREDITS
      FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY h
      JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON h.USER_ID = u.USER_ID
      , LATERAL FLATTEN(input => h.METRICS) m
      WHERE h.START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
      GROUP BY u.NAME
    UNION ALL
    SELECT USER_NAME,
        SUM(TOKENS) AS TOTAL_TOKENS, SUM(TOKEN_CREDITS) AS AI_CREDITS
      FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
      WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
      GROUP BY USER_NAME
    UNION ALL
    SELECT USER_NAME,
        SUM(TOKENS) AS TOTAL_TOKENS, SUM(TOKEN_CREDITS) AS AI_CREDITS
      FROM SNOWFLAKE.ACCOUNT_USAGE.SNOWFLAKE_COCO_USAGE_HISTORY
      WHERE USAGE_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
      GROUP BY USER_NAME
  )
  GROUP BY USER_NAME""",
    "latency": {"source": "AI_FUNCTIONS + AGENT + COCO", "lag": "~45 min"},
}

# --- Limits queries ---

get_resource_monitors = {
    "sql": "SHOW RESOURCE MONITORS",
    "latency": {"source": "SHOW RESOURCE MONITORS", "lag": "Live"},
}

get_budget_details = {
    "sql": """SELECT BUDGET_NAME, CREDIT_LIMIT, CURRENT_MONTH_SPENDING,
    (CURRENT_MONTH_SPENDING / NULLIF(CREDIT_LIMIT, 0) * 100) AS PCT_USED
  FROM SNOWFLAKE.ACCOUNT_USAGE.BUDGET_DETAILS
  ORDER BY CREDIT_LIMIT DESC
  LIMIT 10""",
    "latency": {"source": "BUDGET_DETAILS", "lag": "~minutes"},
}

get_quota_block_history = {
    "sql": """SELECT ACTION_AT, QUOTA_NAME, USER_NAME, ACTION, PER_USER_LIMIT, CREDITS, BLOCKED_UNTIL
  FROM SNOWFLAKE.ACCOUNT_USAGE.QUOTA_ACCESS_BLOCK_HISTORY
  WHERE ACTION_AT >= DATEADD('day', -30, CURRENT_DATE())
  ORDER BY ACTION_AT DESC
  LIMIT 50""",
    "latency": {"source": "QUOTA_ACCESS_BLOCK_HISTORY", "lag": "~minutes"},
}


# --- Limit management (write) ---

def create_resource_monitor_sql(
    name: str,
    credit_quota: int,
    frequency: str = None,
    start_timestamp: str = None,
    notify_at: list[int] = None,
    suspend_at: int = None,
    suspend_immediate_at: int = None,
) -> str:
    parts = [
        f"CREATE OR REPLACE RESOURCE MONITOR {name}",
        f"WITH CREDIT_QUOTA = {credit_quota}",
    ]
    if frequency:
        parts.append(f"FREQUENCY = {frequency}")
    if start_timestamp:
        parts.append(f"START_TIMESTAMP = '{start_timestamp}'")

    triggers = []
    if notify_at:
        for pct in notify_at:
            triggers.append(f"ON {pct} PERCENT DO NOTIFY")
    if suspend_at:
        triggers.append(f"ON {suspend_at} PERCENT DO SUSPEND")
    if suspend_immediate_at:
        triggers.append(f"ON {suspend_immediate_at} PERCENT DO SUSPEND_IMMEDIATE")
    if triggers:
        parts.append("TRIGGERS " + " ".join(triggers))

    return "\n  ".join(parts)
