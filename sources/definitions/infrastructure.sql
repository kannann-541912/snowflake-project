-- Infrastructure: Warehouses
-- Objects defined here are managed by DCM and deployed declaratively.

DEFINE WAREHOUSE ANALYTICS_WH{{env_suffix}}
    WAREHOUSE_SIZE = '{{wh_size}}'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;
