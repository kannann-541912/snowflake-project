# streamlit — Developer Guide

This directory manages multiple **Streamlit in Snowflake (SiS)** applications. Each app is self-contained in its own sub-folder. A shared utilities layer and a single deploy script keep things consistent across all apps.

## Directory Layout

```
streamlit/
├── deploy_all.py              # Deploy one or all apps via Snowflake CLI
├── shared/
│   └── utils.py               # Shared session helper + formatting functions
└── apps/
    ├── data-platform/         # Customer order KPI dashboard
    │   ├── main.py            # App entry point
    │   ├── snowflake.yml      # SiS deployment manifest → DATA_PLATFORM_APP
    │   ├── environment.yml    # Snowflake Anaconda dependencies
    │   └── pages/             # Additional pages (multi-page nav)
    └── ml-monitor/            # ML model health and deployment tracker
        ├── main.py            # App entry point
        ├── snowflake.yml      # SiS deployment manifest → ML_MONITOR_APP
        ├── environment.yml    # Snowflake Anaconda dependencies
        └── pages/             # Additional pages
```

## Apps

| App folder | Snowflake name | Description |
|------------|---------------|-------------|
| `data-platform` | `SANDBOX.TPCH.DATA_PLATFORM_APP` | Customer order KPIs from `CUSTOMER_ORDER_SUMMARY` |
| `ml-monitor` | `SANDBOX.TPCH.ML_MONITOR_APP` | Active models, 7-day health view, deployment events from `ML_PROD.MLOPS` |

## Prerequisites

```bash
pip install snowflake-cli
```

Configure a local connection in `config.toml` at the project root (see `config.toml.example`).

## Deploying Apps

```bash
# Deploy all apps
python streamlit/deploy_all.py -c default

# Deploy a single app by folder name
python streamlit/deploy_all.py -c default --app data-platform

# Dry-run: print commands without executing
python streamlit/deploy_all.py -c default --dry-run

# List all discovered apps
python streamlit/deploy_all.py --list
```

`deploy_all.py` discovers every `apps/*/snowflake.yml` automatically — adding a new app folder is all that's needed.

## Local Development

Apps use `shared/utils.get_session()`, which works both inside SiS and locally:

```bash
export SNOWFLAKE_ACCOUNT=xna38553.east-us-2.azure
export SNOWFLAKE_USER=<your_user>
export SNOWFLAKE_PAT=<your_token>

pip install streamlit snowflake-snowpark-python

streamlit run streamlit/apps/data-platform/main.py
```

No code changes are needed for local vs SiS — `get_session()` falls back to env-var credentials automatically.

## Adding a New App

1. Create a folder under `streamlit/apps/`:

   ```bash
   mkdir -p streamlit/apps/my-new-app/pages
   ```

2. Create the three required files:

   **`main.py`** — your app entry point:
   ```python
   import sys, pathlib
   sys.path.append(str(pathlib.Path(__file__).parents[2]))

   import streamlit as st
   from shared.utils import get_session

   st.title("My New App")
   session = get_session()
   ```

   **`snowflake.yml`** — deployment manifest:
   ```yaml
   definition_version: 2
   entities:
     my_new_app:
       type: streamlit
       identifier:
         name: MY_NEW_APP
         schema: TPCH
         database: SANDBOX
       title: "My New App"
       query_warehouse: COMPUTE_WH
       main_file: main.py
       pages_dir: pages/
       additional_source_files:
         - ../../shared/utils.py
   ```

   **`environment.yml`** — Python dependencies:
   ```yaml
   name: sf_env
   channels:
     - snowflake
   dependencies:
     - snowflake-snowpark-python
   ```

3. Deploy it:
   ```bash
   python streamlit/deploy_all.py -c default --app my-new-app
   ```

The new app is automatically picked up by CI on the next push to `main`.

## Adding Pages to an Existing App

Add a `.py` file to `apps/<app-name>/pages/`. Snowflake SiS renders each file as a navigation entry automatically.

```python
# apps/data-platform/pages/orders.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parents[3]))

import streamlit as st
from shared.utils import get_session

st.header("Orders")
session = get_session()
df = session.sql("SELECT * FROM SANDBOX.TPCH.ORDERS LIMIT 100").to_pandas()
st.dataframe(df, use_container_width=True)
```

## Adding Python Dependencies

Edit the app's `environment.yml`. Only packages available in the Snowflake Anaconda channel are supported.

```yaml
dependencies:
  - snowflake-snowpark-python
  - matplotlib        # add packages here
  - scikit-learn
```

## Shared Utilities (`shared/utils.py`)

| Function | Description |
|----------|-------------|
| `get_session()` | Returns a Snowpark session — SiS native or env-var fallback for local dev |
| `fmt_currency(value)` | Formats a float as `$1,234.56` |
| `fmt_number(value)` | Formats a number as `1,234` |

Import in any app:
```python
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parents[2]))
from shared.utils import get_session, fmt_currency
```

## CI/CD

| Workflow | Trigger | What runs |
|----------|---------|-----------|
| `validate.yml` | PR to `main` | AST syntax check on all `apps/*/main.py`, shared utils check, presence check for required files |
| `deploy.yml` | Push to `main` | `deploy_all.py -c prod` — deploys every app in `apps/` |
