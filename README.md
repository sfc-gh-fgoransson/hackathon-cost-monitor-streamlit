# Cost Monitoring Dashboard (Streamlit)

Snowflake cost and AI usage monitoring dashboard built with Streamlit.

## Quick Start

```bash
pip install streamlit snowflake-connector-python snowflake-snowpark-python
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your credentials, OR use a named connection:
SNOWFLAKE_DEFAULT_CONNECTION_NAME=gn73913_pat streamlit run streamlit_app.py
```

## Deploy to Snowflake

```bash
snow streamlit deploy --replace -c gn73913_pat
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SNOWFLAKE_DEFAULT_CONNECTION_NAME` | Named connection from `~/.snowflake/connections.toml` | `default` |

## Data Freshness

| Source | Latency | Notes |
|--------|---------|-------|
| BUDGET_DETAILS | ~minutes | Live spending |
| METERING_DAILY_HISTORY | Next day | Daily rollup |
| WAREHOUSE_METERING_HISTORY (AU) | ~45 min | Hourly rollup |
| WAREHOUSE_METERING_HISTORY (IS TVF) | Live | Per-query granularity |
| CORTEX_AI_FUNCTIONS_USAGE_HISTORY | ~45 min | AI token counts |
| CORTEX_AGENT_USAGE_HISTORY | ~45 min | Agent sessions |
| SNOWFLAKE_COCO_USAGE_HISTORY | ~45 min | Cortex Code usage |
| QUERY_HISTORY | ~45 min | Query counts |
| QUERY_METERING_HISTORY | ~minutes | Per-query credits |
| SHOW RESOURCE MONITORS | Live | DDL command |
| QUOTA_ACCESS_BLOCK_HISTORY | ~minutes | Quota blocks |
