# ============================================================
# Python/Snowpark Stored Procedures
# Schema: DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT
# These are deployed via CI as inline Python procedures.
# ============================================================

# ------------------------------------------------------------
# PROCEDURE: INGEST_COMPETITOR_PRICES_FROM_SERPAPI
# Purpose: Fetches competitor prices from SerpAPI Google Shopping
#          into Bronze layer. Writes feed run log for observability.
# Parameters:
#   - TRIGGERED_BY_PARAM (VARCHAR, default 'MANUAL_REFRESH')
#   - MAX_SKUS_TO_FETCH (NUMBER, default 100)
# Returns: VARCHAR (status summary)
# Dependencies: SERPAPI_ACCESS_INTEGRATION, SERPAPI_ACCESS_CREDENTIALS
# ------------------------------------------------------------

import requests
import json
import uuid
from datetime import datetime, timezone
import _snowflake

SCHEMA = "DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT"


def escape_sql_string(val):
    if val is None:
        return ""
    return val.replace("\\", "\\\\").replace("'", "\\'")


def fetch_competitor_prices_for_sku(serpapi_key, search_query, sku_id):
    try:
        response = requests.get("https://serpapi.com/search",
            params={"engine": "google_shopping", "q": search_query, "api_key": serpapi_key,
                    "num": 5, "gl": "us", "hl": "en"}, timeout=15)
        if response.status_code != 200:
            return []
        data = response.json()
        results = []
        for item in data.get("shopping_results", [])[:5]:
            price_str = item.get("price", "")
            price_clean = price_str.replace("$", "").replace(",", "").strip() if price_str else ""
            product_url = item.get("product_link", "") or item.get("link", "")
            extensions = item.get("extensions", [])
            all_text = f"{' '.join(extensions).lower()} {item.get('delivery', '')} {item.get('snippet', '')}".lower()
            in_stock_status = "out_of_stock" if any(p in all_text for p in ["out of stock", "sold out", "unavailable"]) else "in_stock"
            results.append({
                "competitor_name": item.get("source", "Unknown Retailer"),
                "competitor_price_raw": price_str,
                "competitor_price_clean": price_clean,
                "competitor_in_stock": in_stock_status,
                "product_url": product_url,
                "product_title": item.get("title", ""),
                "full_response_snippet": json.dumps(item)
            })
        return results
    except requests.exceptions.Timeout:
        return [{"error": "SERPAPI_TIMEOUT", "competitor_name": "FETCH_ERROR"}]
    except requests.exceptions.RequestException as e:
        return [{"error": str(e), "competitor_name": "FETCH_ERROR"}]
    except Exception as e:
        return [{"error": str(e), "competitor_name": "PARSE_ERROR"}]


def ingest_competitor_prices_main(session, triggered_by_param="MANUAL_REFRESH", max_skus_to_fetch=100):
    """Handler for INGEST_COMPETITOR_PRICES_FROM_SERPAPI procedure."""
    run_start_time = datetime.now(timezone.utc)
    try:
        serpapi_key = _snowflake.get_generic_secret_string('serpapi_key')
    except Exception as e:
        return f"FAILED: Could not read SerpAPI secret. Error: {str(e)}"
    if not serpapi_key or serpapi_key == 'YOUR_ACTUAL_SERPAPI_KEY_HERE':
        return "FAILED: SerpAPI key is not set."

    feed_run_id = str(uuid.uuid4())
    session.sql(f"""INSERT INTO {SCHEMA}.BRONZE_SERPAPI_FEED_RUN_LOG
        (feed_run_id, run_triggered_at, run_triggered_by, run_status, total_skus_attempted)
        SELECT '{feed_run_id}', CURRENT_TIMESTAMP(), '{triggered_by_param}', 'RUNNING', 0""").collect()

    skus_df = session.sql(f"""SELECT sku_id, product_name, brand, competitor_reference_search_term, current_price
        FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED
        WHERE is_current_record = TRUE AND is_active = TRUE
          AND competitor_reference_search_term IS NOT NULL AND TRIM(competitor_reference_search_term) != ''
        ORDER BY sku_id LIMIT {int(max_skus_to_fetch)}""").collect()

    total_skus_attempted, total_skus_fetched, total_rows_written, skus_with_errors = len(skus_df), 0, 0, 0
    error_log = []
    session.sql(f"UPDATE {SCHEMA}.BRONZE_SERPAPI_FEED_RUN_LOG SET total_skus_attempted = {total_skus_attempted} WHERE feed_run_id = '{feed_run_id}'").collect()

    for sku_row in skus_df:
        sku_id, search_term = sku_row[0], sku_row[3]
        competitor_results = fetch_competitor_prices_for_sku(serpapi_key, search_term, sku_id)
        if not competitor_results:
            skus_with_errors += 1
            error_log.append(f"{sku_id}: no results")
            continue
        sku_got_valid_result = False
        for result in competitor_results:
            if result.get("competitor_name") in ("FETCH_ERROR", "PARSE_ERROR"):
                skus_with_errors += 1
                error_log.append(f"{sku_id}: {result.get('error', 'unknown')}")
                break
            snapshot_id = str(uuid.uuid4())
            cn = escape_sql_string(result["competitor_name"])
            pr = escape_sql_string(result["competitor_price_raw"])
            ist = escape_sql_string(result.get("competitor_in_stock", "in_stock"))
            pu = escape_sql_string(result.get("product_url", "")[:2000])
            sq = escape_sql_string(search_term)
            try:
                fj = json.dumps(result, ensure_ascii=True).replace("\\", "\\\\").replace("'", "\\'")
            except:
                fj = '{}'
            session.sql(f"""INSERT INTO {SCHEMA}.BRONZE_COMPETITOR_PRICE_RAW
                (snapshot_record_id, feed_run_id, ingestion_timestamp, sku_id, product_search_query,
                 competitor_name, competitor_price_raw, competitor_in_stock_status, competitor_product_url,
                 serpapi_full_response_json, scraped_at)
                SELECT '{snapshot_id}', '{feed_run_id}', CURRENT_TIMESTAMP(), '{sku_id}', '{sq}',
                    '{cn}', '{pr}', '{ist}', '{pu}', PARSE_JSON('{fj}'), CURRENT_TIMESTAMP()""").collect()
            total_rows_written += 1
            sku_got_valid_result = True
        if sku_got_valid_result:
            total_skus_fetched += 1

    duration_secs = round((datetime.now(timezone.utc) - run_start_time).total_seconds(), 1)
    final_status = "SUCCESS" if skus_with_errors == 0 else ("PARTIAL_SUCCESS" if total_skus_fetched > 0 else "FAILED")
    error_summary = escape_sql_string("; ".join(error_log[:10])) if error_log else ""
    session.sql(f"""UPDATE {SCHEMA}.BRONZE_SERPAPI_FEED_RUN_LOG SET run_completed_at = CURRENT_TIMESTAMP(),
        run_status = '{final_status}', total_skus_successfully_fetched = {total_skus_fetched},
        total_price_rows_written = {total_rows_written}, skus_with_fetch_errors = {skus_with_errors},
        error_summary = '{error_summary}', run_duration_seconds = {duration_secs}
        WHERE feed_run_id = '{feed_run_id}'""").collect()
    return (f"Feed run {feed_run_id[:8]}... complete. Status: {final_status}. "
            f"SKUs: {total_skus_attempted}, fetched: {total_skus_fetched}, "
            f"rows: {total_rows_written}, errors: {skus_with_errors}. Duration: {duration_secs}s")


# ------------------------------------------------------------
# PROCEDURE: TRANSFORM_BRONZE_TO_SILVER_PIPELINE
# Purpose: Transforms raw Bronze data into cleansed Silver tables.
#          Handles SKU Master, Competitor Prices, Weekly Sales,
#          Promotions, Returns, and Loyalty Members.
# Parameters: None
# Returns: VARCHAR (status summary with row counts)
# ------------------------------------------------------------

def transform_sku_master(session):
    session.sql(f"""INSERT INTO {SCHEMA}.SILVER_SKU_MASTER_CLEANSED
        (bronze_ingestion_batch_id, sku_id, product_name, category, subcategory, brand,
         current_price, cost, margin_pct, margin_amount_usd, stock_level,
         stock_availability_status, is_active, competitor_reference_search_term,
         record_source_created_at, record_source_updated_at, data_quality_check_passed, data_quality_failure_reason)
        SELECT b.ingestion_batch_id, TRIM(b.sku_id), TRIM(b.product_name), UPPER(TRIM(b.category)), UPPER(TRIM(b.subcategory)), TRIM(b.brand),
            TRY_TO_DOUBLE(REGEXP_REPLACE(b.current_price, '[^0-9.]', '')),
            TRY_TO_DOUBLE(REGEXP_REPLACE(b.cost, '[^0-9.]', '')),
            TRY_TO_DOUBLE(REGEXP_REPLACE(b.margin_pct, '[^0-9.]', '')),
            TRY_TO_DOUBLE(REGEXP_REPLACE(b.current_price, '[^0-9.]', '')) - TRY_TO_DOUBLE(REGEXP_REPLACE(b.cost, '[^0-9.]', '')),
            TRY_TO_NUMBER(REGEXP_REPLACE(b.stock_level, '[^0-9]', '')),
            CASE WHEN TRY_TO_NUMBER(REGEXP_REPLACE(b.stock_level,'[^0-9]','')) = 0 THEN 'OUT_OF_STOCK'
                 WHEN TRY_TO_NUMBER(REGEXP_REPLACE(b.stock_level,'[^0-9]','')) <= 20 THEN 'LOW_STOCK' ELSE 'IN_STOCK' END,
            CASE WHEN LOWER(TRIM(b.is_active)) IN ('true','1','yes') THEN TRUE ELSE FALSE END,
            b.competitor_reference_search_term, TRY_TO_TIMESTAMP_LTZ(b.created_at), TRY_TO_TIMESTAMP_LTZ(b.updated_at),
            CASE WHEN TRIM(b.sku_id) IS NULL OR TRIM(b.sku_id) = '' THEN FALSE
                 WHEN TRY_TO_DOUBLE(REGEXP_REPLACE(b.current_price,'[^0-9.]','')) IS NULL THEN FALSE
                 WHEN TRY_TO_DOUBLE(REGEXP_REPLACE(b.current_price,'[^0-9.]','')) < 0 THEN FALSE ELSE TRUE END,
            CASE WHEN TRIM(b.sku_id) IS NULL OR TRIM(b.sku_id) = '' THEN 'MISSING_SKU_ID'
                 WHEN TRY_TO_DOUBLE(REGEXP_REPLACE(b.current_price,'[^0-9.]','')) IS NULL THEN 'UNPARSEABLE_PRICE'
                 WHEN TRY_TO_DOUBLE(REGEXP_REPLACE(b.current_price,'[^0-9.]','')) < 0 THEN 'NEGATIVE_PRICE' ELSE NULL END
        FROM {SCHEMA}.BRONZE_SKU_MASTER_RAW b
        WHERE b.raw_row_has_parse_error = FALSE
          AND (b.ingestion_batch_id IS NULL OR b.ingestion_batch_id NOT IN (
              SELECT DISTINCT bronze_ingestion_batch_id FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED
              WHERE bronze_ingestion_batch_id IS NOT NULL))""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED").collect()[0][0]


def transform_competitor_prices(session):
    session.sql(f"""INSERT INTO {SCHEMA}.SILVER_COMPETITOR_PRICE_ENRICHED
        (bronze_snapshot_record_id, feed_run_id, sku_id, product_name, category,
         competitor_name, competitor_price, our_current_price, scraped_at,
         price_gap_absolute_usd, price_gap_percentage, competitive_positioning_status,
         competitor_has_product_in_stock, is_significant_price_opportunity, is_stockout_opportunity)
        SELECT b.snapshot_record_id, b.feed_run_id, b.sku_id, s.product_name, s.category,
            b.competitor_name, TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw, '[^0-9.]', '')),
            s.current_price, b.scraped_at,
            s.current_price - TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw,'[^0-9.]','')),
            ROUND((s.current_price - TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw,'[^0-9.]','')))
                / NULLIF(TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw,'[^0-9.]','')), 0) * 100, 2),
            CASE WHEN (s.current_price - TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw,'[^0-9.]','')))
                     / NULLIF(TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw,'[^0-9.]','')), 0) * 100 > 5 THEN 'OVERPRICED'
                 WHEN (s.current_price - TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw,'[^0-9.]','')))
                     / NULLIF(TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw,'[^0-9.]','')), 0) * 100 < -5 THEN 'UNDERPRICED'
                 ELSE 'PRICE_PARITY' END,
            CASE WHEN LOWER(b.competitor_in_stock_status) LIKE '%out of stock%' THEN FALSE ELSE TRUE END,
            CASE WHEN (s.current_price - TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw,'[^0-9.]','')))
                     / NULLIF(TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw,'[^0-9.]','')), 0) * 100 > 10 THEN TRUE ELSE FALSE END,
            CASE WHEN LOWER(b.competitor_in_stock_status) LIKE '%out of stock%' AND s.stock_level > 50 THEN TRUE ELSE FALSE END
        FROM {SCHEMA}.BRONZE_COMPETITOR_PRICE_RAW b
        INNER JOIN {SCHEMA}.SILVER_SKU_MASTER_CLEANSED s ON b.sku_id = s.sku_id AND s.is_current_record = TRUE AND s.is_active = TRUE
        WHERE b.snapshot_record_id NOT IN (SELECT bronze_snapshot_record_id FROM {SCHEMA}.SILVER_COMPETITOR_PRICE_ENRICHED WHERE bronze_snapshot_record_id IS NOT NULL)
          AND TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw, '[^0-9.]', '')) IS NOT NULL
          AND TRY_TO_DOUBLE(REGEXP_REPLACE(b.competitor_price_raw, '[^0-9.]', '')) > 0""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.SILVER_COMPETITOR_PRICE_ENRICHED").collect()[0][0]


def transform_weekly_sales(session):
    session.sql(f"""INSERT INTO {SCHEMA}.SILVER_WEEKLY_SALES_CLEANSED
        (week_start_date, week_number, sku_id, brand, category, units_sold, revenue_usd, fiscal_quarter, is_valid)
        SELECT TRY_TO_DATE(b.week_start_date), b.week_number, TRIM(b.sku_id), TRIM(b.brand_raw), UPPER(TRIM(b.category_raw)),
               b.units_sold, b.revenue_usd, b.fiscal_quarter,
               CASE WHEN b.units_sold > 0 AND TRIM(b.brand_raw) IS NOT NULL AND TRIM(b.category_raw) IS NOT NULL THEN TRUE ELSE FALSE END
        FROM {SCHEMA}.BRONZE_WEEKLY_SALES_RAW b
        WHERE b.record_id NOT IN (SELECT record_id FROM {SCHEMA}.SILVER_WEEKLY_SALES_CLEANSED WHERE record_id IS NOT NULL)
          AND b.units_sold IS NOT NULL""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.SILVER_WEEKLY_SALES_CLEANSED").collect()[0][0]


def transform_promotions(session):
    session.sql(f"""INSERT INTO {SCHEMA}.SILVER_PROMOTIONS_ENRICHED
        (promotion_id, promotion_name, promotion_type, discount_type, discount_value,
         start_date, end_date, target_category, target_brand, channel,
         planned_unit_lift_pct, planned_revenue_target_usd, status, budget_usd,
         promo_duration_days, sku_id, product_name, brand, category,
         original_price, promo_price, discount_amount_usd, discount_percentage, is_currently_active)
        SELECT p.promotion_id, p.promotion_name, p.promotion_type, p.discount_type,
            TRY_TO_DOUBLE(p.discount_value), TRY_TO_DATE(p.start_date), TRY_TO_DATE(p.end_date),
            UPPER(TRIM(p.target_category)), TRIM(p.target_brand), UPPER(TRIM(p.channel)),
            TRY_TO_DOUBLE(p.planned_unit_lift_pct), TRY_TO_DOUBLE(p.planned_revenue_target_usd),
            p.status, TRY_TO_DOUBLE(p.budget_usd),
            DATEDIFF('day', TRY_TO_DATE(p.start_date), TRY_TO_DATE(p.end_date)),
            a.sku_id, s.product_name, s.brand, s.category,
            TRY_TO_DOUBLE(a.original_price), TRY_TO_DOUBLE(a.promo_price),
            TRY_TO_DOUBLE(a.original_price) - TRY_TO_DOUBLE(a.promo_price),
            ROUND((TRY_TO_DOUBLE(a.original_price) - TRY_TO_DOUBLE(a.promo_price)) / NULLIF(TRY_TO_DOUBLE(a.original_price), 0) * 100, 1),
            CASE WHEN CURRENT_DATE BETWEEN TRY_TO_DATE(p.start_date) AND TRY_TO_DATE(p.end_date) THEN TRUE ELSE FALSE END
        FROM {SCHEMA}.BRONZE_PROMOTIONS_RAW p
        INNER JOIN {SCHEMA}.BRONZE_PROMOTION_SKU_ASSIGNMENTS_RAW a ON p.promotion_id = a.promotion_id
        LEFT JOIN {SCHEMA}.SILVER_SKU_MASTER_CLEANSED s ON a.sku_id = s.sku_id AND s.is_current_record = TRUE
        WHERE p.promotion_id NOT IN (SELECT DISTINCT promotion_id FROM {SCHEMA}.SILVER_PROMOTIONS_ENRICHED WHERE promotion_id IS NOT NULL)""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.SILVER_PROMOTIONS_ENRICHED").collect()[0][0]


def transform_returns(session):
    session.sql(f"""INSERT INTO {SCHEMA}.SILVER_RETURNS_ENRICHED
        (return_id, order_date, return_date, sku_id, product_name, brand, category,
         units_returned, return_reason, return_condition, refund_amount_usd,
         channel, resolution, our_margin_percentage, margin_lost_usd, days_to_return)
        SELECT b.return_id, TRY_TO_DATE(b.order_date), TRY_TO_DATE(b.return_date),
            b.sku_id, s.product_name, s.brand, s.category,
            b.units_returned, b.return_reason, b.return_condition,
            b.refund_amount_usd, b.channel, b.resolution, s.margin_pct,
            ROUND(b.refund_amount_usd * (s.margin_pct / 100.0), 2),
            DATEDIFF('day', TRY_TO_DATE(b.order_date), TRY_TO_DATE(b.return_date))
        FROM {SCHEMA}.BRONZE_RETURNS_RAW b
        LEFT JOIN {SCHEMA}.SILVER_SKU_MASTER_CLEANSED s ON b.sku_id = s.sku_id AND s.is_current_record = TRUE
        WHERE b.return_id NOT IN (SELECT DISTINCT return_id FROM {SCHEMA}.SILVER_RETURNS_ENRICHED WHERE return_id IS NOT NULL)""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.SILVER_RETURNS_ENRICHED").collect()[0][0]


def transform_loyalty(session):
    """Bronze Loyalty -> Silver Loyalty (MERGE with pre-computed aggregates)."""
    session.sql(f"""CREATE OR REPLACE TEMPORARY TABLE _tmp_loyalty_top_cat AS
        SELECT member_id, category AS top_category FROM (
            SELECT t.member_id, s.category,
                   ROW_NUMBER() OVER (PARTITION BY t.member_id ORDER BY SUM(t.transaction_amount_usd) DESC) AS rn
            FROM {SCHEMA}.BRONZE_LOYALTY_TRANSACTIONS_RAW t
            LEFT JOIN {SCHEMA}.SILVER_SKU_MASTER_CLEANSED s ON t.sku_id = s.sku_id AND s.is_current_record = TRUE
            GROUP BY t.member_id, s.category) WHERE rn = 1""").collect()
    session.sql(f"""CREATE OR REPLACE TEMPORARY TABLE _tmp_loyalty_top_brand AS
        SELECT member_id, brand AS top_brand FROM (
            SELECT t.member_id, s.brand,
                   ROW_NUMBER() OVER (PARTITION BY t.member_id ORDER BY SUM(t.transaction_amount_usd) DESC) AS rn
            FROM {SCHEMA}.BRONZE_LOYALTY_TRANSACTIONS_RAW t
            LEFT JOIN {SCHEMA}.SILVER_SKU_MASTER_CLEANSED s ON t.sku_id = s.sku_id AND s.is_current_record = TRUE
            GROUP BY t.member_id, s.brand) WHERE rn = 1""").collect()
    session.sql(f"""MERGE INTO {SCHEMA}.SILVER_LOYALTY_MEMBERS_ENRICHED tgt USING (
        SELECT m.member_id, m.first_name, m.last_name, m.email, TRY_TO_DATE(m.enrollment_date) AS enrollment_date,
            m.tier, m.preferred_category, m.preferred_channel, m.loyalty_points_balance, m.status,
            COUNT(t.transaction_id) AS total_transactions, ROUND(COALESCE(SUM(t.transaction_amount_usd), 0), 2) AS total_spend_usd,
            ROUND(COALESCE(AVG(t.transaction_amount_usd), 0), 2) AS avg_order_value,
            COALESCE(SUM(t.units_purchased), 0) AS total_units_purchased, COALESCE(SUM(t.points_earned), 0) AS total_points_earned,
            MIN(TRY_TO_DATE(t.transaction_date)) AS first_purchase_date, MAX(TRY_TO_DATE(t.transaction_date)) AS last_purchase_date,
            DATEDIFF('day', MAX(TRY_TO_DATE(t.transaction_date)), CURRENT_DATE) AS days_since_last_purchase,
            tc.top_category, tb.top_brand, DATEDIFF('day', TRY_TO_DATE(m.enrollment_date), CURRENT_DATE) AS tenure_days
        FROM {SCHEMA}.BRONZE_LOYALTY_MEMBERS_RAW m
        LEFT JOIN {SCHEMA}.BRONZE_LOYALTY_TRANSACTIONS_RAW t ON m.member_id = t.member_id
        LEFT JOIN _tmp_loyalty_top_cat tc ON m.member_id = tc.member_id
        LEFT JOIN _tmp_loyalty_top_brand tb ON m.member_id = tb.member_id
        GROUP BY m.member_id, m.first_name, m.last_name, m.email, m.enrollment_date,
                 m.tier, m.preferred_category, m.preferred_channel, m.loyalty_points_balance, m.status,
                 tc.top_category, tb.top_brand
    ) src ON tgt.member_id = src.member_id
    WHEN MATCHED THEN UPDATE SET
        tgt.processed_at = CURRENT_TIMESTAMP(), tgt.total_transactions = src.total_transactions,
        tgt.total_spend_usd = src.total_spend_usd, tgt.avg_order_value = src.avg_order_value,
        tgt.total_units_purchased = src.total_units_purchased, tgt.total_points_earned = src.total_points_earned,
        tgt.last_purchase_date = src.last_purchase_date, tgt.days_since_last_purchase = src.days_since_last_purchase,
        tgt.top_category = src.top_category, tgt.top_brand = src.top_brand, tgt.tenure_days = src.tenure_days
    WHEN NOT MATCHED THEN INSERT (member_id, first_name, last_name, email, enrollment_date, tier,
        preferred_category, preferred_channel, loyalty_points_balance, status, total_transactions, total_spend_usd,
        avg_order_value, total_units_purchased, total_points_earned, first_purchase_date, last_purchase_date,
        days_since_last_purchase, top_category, top_brand, tenure_days)
    VALUES (src.member_id, src.first_name, src.last_name, src.email, src.enrollment_date, src.tier,
        src.preferred_category, src.preferred_channel, src.loyalty_points_balance, src.status,
        src.total_transactions, src.total_spend_usd, src.avg_order_value, src.total_units_purchased,
        src.total_points_earned, src.first_purchase_date, src.last_purchase_date,
        src.days_since_last_purchase, src.top_category, src.top_brand, src.tenure_days)""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.SILVER_LOYALTY_MEMBERS_ENRICHED").collect()[0][0]


def transform_bronze_to_silver_main(session):
    """Handler for TRANSFORM_BRONZE_TO_SILVER_PIPELINE procedure."""
    start = datetime.now(timezone.utc)
    sku_count = transform_sku_master(session)
    competitor_count = transform_competitor_prices(session)
    sales_count = transform_weekly_sales(session)
    promo_count = transform_promotions(session)
    returns_count = transform_returns(session)
    loyalty_count = transform_loyalty(session)
    duration = round((datetime.now(timezone.utc) - start).total_seconds(), 1)
    return (f"Bronze->Silver complete. SKU: {sku_count}, Competitors: {competitor_count}, "
            f"Sales: {sales_count}, Promotions: {promo_count}, "
            f"Returns: {returns_count}, Loyalty: {loyalty_count}. Duration: {duration}s")


# ------------------------------------------------------------
# PROCEDURE: RUN_DATA_QUALITY_VALIDATION_SUITE
# Purpose: Runs 6 data quality checks across Bronze/Silver layers.
#          Logs results to SILVER_DATA_QUALITY_CHECK_LOG.
# Parameters:
#   - TRIGGERED_BY_PARAM (VARCHAR, default 'MANUAL')
# Returns: VARIANT (JSON summary of all check results)
# ------------------------------------------------------------

def run_check(session, check_name, target_table, target_layer, count_sql, sample_sql, threshold_pct, triggered_by):
    """Generic DQ check runner."""
    result = session.sql(count_sql).collect()
    total_rows, rows_passed, rows_failed = result[0][0], result[0][1], result[0][2]
    failure_rate = round((rows_failed * 100.0 / total_rows), 2) if total_rows > 0 else 0.0
    overall_passed = failure_rate < threshold_pct
    sample_json = None
    if rows_failed > 0 and sample_sql:
        sample_rows = session.sql(sample_sql).collect()
        if sample_rows:
            col_names = [col.name for col in session.sql(sample_sql).schema.fields]
            sample_json = json.dumps([{col_names[i]: str(row[i]) for i in range(len(col_names))} for row in sample_rows[:5]])
    sample_insert = f"PARSE_JSON('{sample_json.replace(chr(39), chr(39)+chr(39))}')" if sample_json else "NULL"
    session.sql(f"""INSERT INTO {SCHEMA}.SILVER_DATA_QUALITY_CHECK_LOG
        (check_name, target_table_name, target_layer, total_rows_evaluated, rows_that_passed,
         rows_that_failed, failure_rate_percentage, overall_check_passed, sample_of_failing_rows, check_triggered_by)
        SELECT '{check_name}', '{target_table}', '{target_layer}', {total_rows}, {rows_passed},
            {rows_failed}, {failure_rate}, {str(overall_passed).upper()}, {sample_insert}, '{triggered_by}'""").collect()
    return {"check_name": check_name, "passed": overall_passed, "total_rows": total_rows,
            "rows_failed": rows_failed, "failure_rate_pct": failure_rate}


def run_dq_validation_main(session, triggered_by_param="MANUAL"):
    """Handler for RUN_DATA_QUALITY_VALIDATION_SUITE procedure."""
    results = []
    results.append(run_check(session, "NULL_OR_EMPTY_SKU_ID_CHECK", "BRONZE_SKU_MASTER_RAW", "BRONZE",
        f"SELECT COUNT(*), COUNT(CASE WHEN sku_id IS NOT NULL AND TRIM(sku_id) != '' THEN 1 END), COUNT(CASE WHEN sku_id IS NULL OR TRIM(sku_id) = '' THEN 1 END) FROM {SCHEMA}.BRONZE_SKU_MASTER_RAW",
        f"SELECT ingestion_record_id, sku_id, product_name, source_file_name FROM {SCHEMA}.BRONZE_SKU_MASTER_RAW WHERE sku_id IS NULL OR TRIM(sku_id) = '' LIMIT 5", 5.0, triggered_by_param))
    results.append(run_check(session, "UNPARSEABLE_CURRENT_PRICE_CHECK", "BRONZE_SKU_MASTER_RAW", "BRONZE",
        f"SELECT COUNT(*), COUNT(CASE WHEN TRY_TO_DOUBLE(REGEXP_REPLACE(current_price,'[^0-9.]','')) IS NOT NULL THEN 1 END), COUNT(CASE WHEN TRY_TO_DOUBLE(REGEXP_REPLACE(current_price,'[^0-9.]','')) IS NULL THEN 1 END) FROM {SCHEMA}.BRONZE_SKU_MASTER_RAW",
        f"SELECT ingestion_record_id, sku_id, current_price FROM {SCHEMA}.BRONZE_SKU_MASTER_RAW WHERE TRY_TO_DOUBLE(REGEXP_REPLACE(current_price,'[^0-9.]','')) IS NULL LIMIT 5", 5.0, triggered_by_param))
    results.append(run_check(session, "DUPLICATE_ACTIVE_SKU_ID_CHECK", "SILVER_SKU_MASTER_CLEANSED", "SILVER",
        f"SELECT COUNT(*), COUNT(CASE WHEN cnt = 1 THEN 1 END), COUNT(CASE WHEN cnt > 1 THEN 1 END) FROM (SELECT sku_id, COUNT(*) AS cnt FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED WHERE is_current_record = TRUE GROUP BY sku_id)",
        f"SELECT sku_id, COUNT(*) AS duplicate_count FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED WHERE is_current_record = TRUE GROUP BY sku_id HAVING COUNT(*) > 1 LIMIT 5", 0.01, triggered_by_param))
    results.append(run_check(session, "NEGATIVE_MARGIN_ANOMALY_CHECK", "SILVER_SKU_MASTER_CLEANSED", "SILVER",
        f"SELECT COUNT(*), COUNT(CASE WHEN margin_pct >= 0 OR margin_pct IS NULL THEN 1 END), COUNT(CASE WHEN margin_pct < 0 THEN 1 END) FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED WHERE is_current_record = TRUE",
        f"SELECT sku_id, product_name, current_price, cost, margin_pct FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED WHERE is_current_record = TRUE AND margin_pct < 0 LIMIT 5", 2.0, triggered_by_param))
    results.append(run_check(session, "BRONZE_SILVER_SKU_RECONCILIATION_CHECK", "SILVER_SKU_MASTER_CLEANSED", "SILVER",
        f"SELECT (SELECT COUNT(*) FROM {SCHEMA}.BRONZE_SKU_MASTER_RAW WHERE raw_row_has_parse_error = FALSE), (SELECT COUNT(*) FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED WHERE is_current_record = TRUE), (SELECT COUNT(*) FROM {SCHEMA}.BRONZE_SKU_MASTER_RAW WHERE raw_row_has_parse_error = FALSE) - (SELECT COUNT(*) FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED WHERE is_current_record = TRUE)",
        None, 5.0, triggered_by_param))
    results.append(run_check(session, "COMPETITOR_PRICE_COVERAGE_CHECK", "SILVER_COMPETITOR_PRICE_ENRICHED", "SILVER",
        f"SELECT (SELECT COUNT(DISTINCT sku_id) FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED WHERE is_current_record = TRUE AND is_active = TRUE), (SELECT COUNT(DISTINCT sku_id) FROM {SCHEMA}.SILVER_COMPETITOR_PRICE_ENRICHED), (SELECT COUNT(DISTINCT sku_id) FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED WHERE is_current_record = TRUE AND is_active = TRUE) - (SELECT COUNT(DISTINCT sku_id) FROM {SCHEMA}.SILVER_COMPETITOR_PRICE_ENRICHED)",
        f"SELECT s.sku_id, s.product_name, s.category FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED s WHERE s.is_current_record = TRUE AND s.is_active = TRUE AND s.sku_id NOT IN (SELECT DISTINCT sku_id FROM {SCHEMA}.SILVER_COMPETITOR_PRICE_ENRICHED) LIMIT 5", 10.0, triggered_by_param))
    summary = {r["check_name"]: r["passed"] for r in results}
    summary["ALL_CHECKS_PASSED"] = all(r["passed"] for r in results)
    summary["TOTAL_CHECKS_RUN"] = len(results)
    return summary


# ------------------------------------------------------------
# PROCEDURE: REFRESH_GOLD_LAYER_PIPELINE
# Purpose: Refreshes all Gold layer tables including:
#          - SKU Pricing Intelligence
#          - Cortex AI Recommendations
#          - Weekly Sell-Through
#          - Promotion Performance
#          - Returns Margin Analysis
#          - Loyalty Customer Insights
# Parameters:
#   - FEED_RUN_ID_PARAM (VARCHAR, default NULL — uses latest)
# Returns: VARCHAR (status summary with row counts)
# Note: GOLD_CATEGORY_PERFORMANCE_SUMMARY auto-refreshes via dynamic table.
# ------------------------------------------------------------

def refresh_sku_pricing(session, feed_run_id):
    """Refresh GOLD_SKU_PRICING_INTELLIGENCE with latest competitor data."""
    session.sql(f"DELETE FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE WHERE feed_run_id = '{feed_run_id}'").collect()
    session.sql(f"""INSERT INTO {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
        (feed_run_id, sku_id, product_name, category, subcategory, brand,
         our_current_price, our_cost_price, our_margin_percentage, our_margin_amount_usd,
         lowest_competitor_price_found, highest_competitor_price_found, number_of_competitors_found,
         primary_competitor_name, primary_competitor_price, price_gap_vs_primary_competitor_pct,
         overall_competitive_positioning_status, requires_immediate_price_review,
         current_stock_level, stock_availability_status, requires_replenishment_action, estimated_days_until_stockout)
        WITH competitor_agg AS (
            SELECT sku_id, MIN(competitor_price) AS lowest_price, MAX(competitor_price) AS highest_price,
                   COUNT(DISTINCT competitor_name) AS num_competitors
            FROM {SCHEMA}.SILVER_COMPETITOR_PRICE_ENRICHED
            WHERE feed_run_id = '{feed_run_id}' AND competitor_price > 0 GROUP BY sku_id),
        primary_competitor AS (
            SELECT sku_id, competitor_name, competitor_price,
                   ROW_NUMBER() OVER (PARTITION BY sku_id ORDER BY competitor_price ASC) AS rn
            FROM {SCHEMA}.SILVER_COMPETITOR_PRICE_ENRICHED
            WHERE feed_run_id = '{feed_run_id}' AND competitor_price > 0)
        SELECT '{feed_run_id}', s.sku_id, s.product_name, s.category, s.subcategory, s.brand,
            s.current_price, s.cost, s.margin_pct, s.margin_amount_usd,
            ca.lowest_price, ca.highest_price, ca.num_competitors, pc.competitor_name, pc.competitor_price,
            ROUND((s.current_price - pc.competitor_price) / NULLIF(pc.competitor_price, 0) * 100, 2),
            CASE WHEN (s.current_price - ca.lowest_price) / NULLIF(ca.lowest_price, 0) * 100 > 5 THEN 'OVERPRICED'
                 WHEN (s.current_price - ca.lowest_price) / NULLIF(ca.lowest_price, 0) * 100 < -5 THEN 'UNDERPRICED'
                 ELSE 'PRICE_PARITY' END,
            CASE WHEN ABS((s.current_price - ca.lowest_price) / NULLIF(ca.lowest_price, 0) * 100) > 10 THEN TRUE ELSE FALSE END,
            s.stock_level, s.stock_availability_status,
            CASE WHEN s.stock_level < 30 THEN TRUE ELSE FALSE END,
            CASE WHEN s.stock_level = 0 THEN 0
                 WHEN s.category = 'SMARTPHONES' THEN ROUND(s.stock_level / 8.0)
                 WHEN s.category = 'LAPTOPS' THEN ROUND(s.stock_level / 5.0)
                 WHEN s.category = 'GAMING' THEN ROUND(s.stock_level / 6.0)
                 WHEN s.category = 'AUDIO' THEN ROUND(s.stock_level / 4.0)
                 WHEN s.category = 'HOME_THEATER' THEN ROUND(s.stock_level / 3.0)
                 ELSE ROUND(s.stock_level / 5.0) END
        FROM {SCHEMA}.SILVER_SKU_MASTER_CLEANSED s
        LEFT JOIN competitor_agg ca ON s.sku_id = ca.sku_id
        LEFT JOIN primary_competitor pc ON s.sku_id = pc.sku_id AND pc.rn = 1
        WHERE s.is_current_record = TRUE AND s.is_active = TRUE AND s.data_quality_check_passed = TRUE""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE WHERE feed_run_id = '{feed_run_id}'").collect()[0][0]


def generate_ai_recommendations(session, feed_run_id):
    """Generate Cortex AI recommendations for SKUs needing action."""
    skus = session.sql(f"""SELECT sku_id, product_name, overall_competitive_positioning_status,
        price_gap_vs_primary_competitor_pct, stock_availability_status,
        our_margin_percentage, estimated_days_until_stockout
        FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
        WHERE feed_run_id = '{feed_run_id}'
          AND (requires_immediate_price_review = TRUE OR requires_replenishment_action = TRUE)""").collect()
    ai_count = 0
    for row in skus:
        sku_id, product_name = row[0], str(row[1]).replace("'", "''")
        positioning = row[2] or 'UNKNOWN'
        gap_pct = row[3] if row[3] is not None else 0
        stock_status = row[4] or 'UNKNOWN'
        margin = row[5] if row[5] is not None else 0
        days_stockout = row[6] if row[6] is not None else 0
        prompt = (f"Retail category manager AI. SKU: {product_name}. "
                  f"Competitive status: {positioning}, price gap: {gap_pct:.1f}%, "
                  f"stock: {stock_status}, days until stockout: {days_stockout}, margin: {margin:.1f}%. "
                  f"Give one specific action in under 15 words. Start with a verb.")
        try:
            ai = session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', '{prompt.replace(chr(39), chr(39)+chr(39))}') AS rec").collect()
            rec = ai[0][0].strip().replace("'", "''") if ai and ai[0][0] else ''
            action = ('REPRICE' if any(w in rec.lower() for w in ['price', 'reduc', 'lower', 'increas', 'discount', 'match'])
                      else 'REPLENISH' if any(w in rec.lower() for w in ['replenish', 'restock', 'order', 'stock', 'supply'])
                      else 'PROMOTE' if any(w in rec.lower() for w in ['promot', 'market', 'campaign', 'bundle'])
                      else 'MONITOR')
            session.sql(f"""UPDATE {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
                SET cortex_ai_recommendation_summary = '{rec}',
                    cortex_ai_recommended_action_type = '{action}',
                    cortex_ai_recommendation_generated_at = CURRENT_TIMESTAMP()
                WHERE sku_id = '{sku_id}' AND feed_run_id = '{feed_run_id}'""").collect()
            ai_count += 1
        except:
            pass
    return ai_count


def refresh_weekly_sell_through(session):
    """Refresh GOLD_WEEKLY_BRAND_SELL_THROUGH from Silver."""
    session.sql(f"DELETE FROM {SCHEMA}.GOLD_WEEKLY_BRAND_SELL_THROUGH").collect()
    session.sql(f"""INSERT INTO {SCHEMA}.GOLD_WEEKLY_BRAND_SELL_THROUGH
        (week_start_date, week_number, brand, total_units_sold, total_revenue_usd, sku_count, avg_units_per_sku, fiscal_quarter)
        SELECT week_start_date, week_number, brand, SUM(units_sold), SUM(revenue_usd),
               COUNT(DISTINCT sku_id), ROUND(SUM(units_sold)::FLOAT / NULLIF(COUNT(DISTINCT sku_id), 0), 1), fiscal_quarter
        FROM {SCHEMA}.SILVER_WEEKLY_SALES_CLEANSED WHERE is_valid = TRUE
        GROUP BY week_start_date, week_number, brand, fiscal_quarter""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.GOLD_WEEKLY_BRAND_SELL_THROUGH").collect()[0][0]


def refresh_promotion_performance(session):
    """Refresh GOLD_PROMOTION_PERFORMANCE from Silver."""
    session.sql(f"DELETE FROM {SCHEMA}.GOLD_PROMOTION_PERFORMANCE").collect()
    session.sql(f"""INSERT INTO {SCHEMA}.GOLD_PROMOTION_PERFORMANCE
        (promotion_id, promotion_name, promotion_type, target_category, target_brand, channel,
         start_date, end_date, promo_duration_days, status, budget_usd, planned_unit_lift_pct,
         planned_revenue_target_usd, sku_count, total_units_during_promo, baseline_units_per_week,
         actual_unit_lift_pct, total_revenue_during_promo, baseline_revenue_per_week, revenue_lift_pct,
         estimated_roas, total_discount_given_usd, performance_status)
        WITH promo_sales AS (
            SELECT p.promotion_id, p.sku_id, SUM(ws.units_sold) AS units_during, SUM(ws.revenue_usd) AS revenue_during
            FROM {SCHEMA}.SILVER_PROMOTIONS_ENRICHED p
            INNER JOIN {SCHEMA}.SILVER_WEEKLY_SALES_CLEANSED ws
                ON p.sku_id = ws.sku_id AND ws.week_start_date BETWEEN p.start_date AND p.end_date AND ws.is_valid = TRUE
            GROUP BY p.promotion_id, p.sku_id),
        baseline AS (
            SELECT p.promotion_id, p.sku_id, AVG(ws.units_sold) AS baseline_units, AVG(ws.revenue_usd) AS baseline_revenue
            FROM {SCHEMA}.SILVER_PROMOTIONS_ENRICHED p
            INNER JOIN {SCHEMA}.SILVER_WEEKLY_SALES_CLEANSED ws
                ON p.sku_id = ws.sku_id AND ws.week_start_date < p.start_date AND ws.is_valid = TRUE
            GROUP BY p.promotion_id, p.sku_id),
        promo_agg AS (
            SELECT p.promotion_id, MAX(p.promotion_name) AS promotion_name, MAX(p.promotion_type) AS promotion_type,
                MAX(p.target_category) AS target_category, MAX(p.target_brand) AS target_brand, MAX(p.channel) AS channel,
                MAX(p.start_date) AS start_date, MAX(p.end_date) AS end_date, MAX(p.promo_duration_days) AS promo_duration_days,
                MAX(p.status) AS status, MAX(p.budget_usd) AS budget_usd, MAX(p.planned_unit_lift_pct) AS planned_unit_lift_pct,
                MAX(p.planned_revenue_target_usd) AS planned_revenue_target_usd, COUNT(DISTINCT p.sku_id) AS sku_count,
                COALESCE(SUM(ps.units_during), 0) AS total_units, COALESCE(AVG(bl.baseline_units), 0) AS baseline_units_per_week,
                COALESCE(SUM(ps.revenue_during), 0) AS total_revenue, COALESCE(AVG(bl.baseline_revenue), 0) AS baseline_revenue_per_week,
                SUM(p.discount_amount_usd) AS total_discount
            FROM {SCHEMA}.SILVER_PROMOTIONS_ENRICHED p
            LEFT JOIN promo_sales ps ON p.promotion_id = ps.promotion_id AND p.sku_id = ps.sku_id
            LEFT JOIN baseline bl ON p.promotion_id = bl.promotion_id AND p.sku_id = bl.sku_id
            GROUP BY p.promotion_id)
        SELECT promotion_id, promotion_name, promotion_type, target_category, target_brand, channel,
            start_date, end_date, promo_duration_days, status, budget_usd, planned_unit_lift_pct,
            planned_revenue_target_usd, sku_count, total_units, baseline_units_per_week,
            CASE WHEN baseline_units_per_week > 0 THEN ROUND((total_units - baseline_units_per_week * (promo_duration_days / 7.0)) / (baseline_units_per_week * (promo_duration_days / 7.0)) * 100, 1) ELSE 0 END,
            total_revenue, baseline_revenue_per_week,
            CASE WHEN baseline_revenue_per_week > 0 THEN ROUND((total_revenue - baseline_revenue_per_week * (promo_duration_days / 7.0)) / (baseline_revenue_per_week * (promo_duration_days / 7.0)) * 100, 1) ELSE 0 END,
            CASE WHEN budget_usd > 0 THEN ROUND(total_revenue / budget_usd, 2) ELSE 0 END, total_discount,
            CASE WHEN planned_unit_lift_pct > 0 AND baseline_units_per_week > 0 THEN
                CASE WHEN (total_units - baseline_units_per_week * (promo_duration_days / 7.0)) / (baseline_units_per_week * (promo_duration_days / 7.0)) * 100 >= planned_unit_lift_pct * 1.2 THEN 'OVER_PERFORMING'
                     WHEN (total_units - baseline_units_per_week * (promo_duration_days / 7.0)) / (baseline_units_per_week * (promo_duration_days / 7.0)) * 100 >= planned_unit_lift_pct * 0.8 THEN 'ON_TRACK'
                     ELSE 'UNDER_PERFORMING' END
            ELSE 'ON_TRACK' END
        FROM promo_agg""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.GOLD_PROMOTION_PERFORMANCE").collect()[0][0]


def refresh_returns_analysis(session):
    """Refresh GOLD_RETURNS_MARGIN_ANALYSIS from Silver."""
    session.sql(f"DELETE FROM {SCHEMA}.GOLD_RETURNS_MARGIN_ANALYSIS").collect()
    session.sql(f"""INSERT INTO {SCHEMA}.GOLD_RETURNS_MARGIN_ANALYSIS
        (sku_id, product_name, brand, category, total_returns, total_units_sold, return_rate_pct,
         total_refund_usd, total_margin_lost_usd, avg_days_to_return, top_return_reason,
         top_return_condition, online_return_pct, recommended_action, rationalization_flag)
        WITH return_agg AS (
            SELECT sku_id, MAX(product_name) AS product_name, MAX(brand) AS brand, MAX(category) AS category,
                SUM(units_returned) AS total_returns, SUM(refund_amount_usd) AS total_refund_usd,
                SUM(margin_lost_usd) AS total_margin_lost_usd, AVG(days_to_return) AS avg_days_to_return,
                ROUND(SUM(CASE WHEN channel = 'ONLINE' THEN units_returned ELSE 0 END)::FLOAT / NULLIF(SUM(units_returned), 0) * 100, 1) AS online_return_pct
            FROM {SCHEMA}.SILVER_RETURNS_ENRICHED GROUP BY sku_id),
        top_reasons AS (
            SELECT sku_id, return_reason, return_condition,
                ROW_NUMBER() OVER (PARTITION BY sku_id ORDER BY COUNT(*) DESC) AS rn
            FROM {SCHEMA}.SILVER_RETURNS_ENRICHED GROUP BY sku_id, return_reason, return_condition),
        sales_totals AS (
            SELECT sku_id, SUM(units_sold) AS total_units_sold
            FROM {SCHEMA}.SILVER_WEEKLY_SALES_CLEANSED WHERE is_valid = TRUE GROUP BY sku_id)
        SELECT ra.sku_id, ra.product_name, ra.brand, ra.category, ra.total_returns,
            COALESCE(st.total_units_sold, 0),
            CASE WHEN st.total_units_sold > 0 THEN ROUND(ra.total_returns::FLOAT / st.total_units_sold * 100, 2) ELSE 0 END,
            ra.total_refund_usd, ra.total_margin_lost_usd, ra.avg_days_to_return,
            tr.return_reason, tr.return_condition, ra.online_return_pct,
            CASE WHEN tr.return_reason = 'DEFECTIVE' THEN 'VENDOR_RMA'
                 WHEN tr.return_reason = 'NOT_AS_DESCRIBED' THEN 'IMPROVE_LISTING' ELSE 'MONITOR' END,
            CASE WHEN st.total_units_sold > 0 AND (ra.total_returns::FLOAT / st.total_units_sold * 100) > 1.0 THEN TRUE ELSE FALSE END
        FROM return_agg ra
        LEFT JOIN top_reasons tr ON ra.sku_id = tr.sku_id AND tr.rn = 1
        LEFT JOIN sales_totals st ON ra.sku_id = st.sku_id""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.GOLD_RETURNS_MARGIN_ANALYSIS").collect()[0][0]


def refresh_loyalty_insights(session):
    """Refresh GOLD_LOYALTY_CUSTOMER_INSIGHTS from Silver."""
    session.sql(f"DELETE FROM {SCHEMA}.GOLD_LOYALTY_CUSTOMER_INSIGHTS").collect()
    session.sql(f"""INSERT INTO {SCHEMA}.GOLD_LOYALTY_CUSTOMER_INSIGHTS
        (member_id, full_name, tier, status, preferred_category, top_category, top_brand,
         total_transactions, total_spend_usd, avg_order_value, loyalty_points_balance,
         points_redeemable_value_usd, tenure_days, days_since_last_purchase, estimated_ltv_usd,
         churn_risk_score, churn_risk_level, customer_segment, recommended_action)
        SELECT member_id, first_name || ' ' || last_name, tier, status, preferred_category,
            top_category, top_brand, total_transactions, total_spend_usd, avg_order_value,
            loyalty_points_balance, ROUND(loyalty_points_balance * 0.01, 2), tenure_days, days_since_last_purchase,
            ROUND(avg_order_value * (total_transactions::FLOAT / NULLIF(tenure_days, 0) * 365) * 3, 2),
            ROUND(LEAST(1.0, GREATEST(0.0,
                (COALESCE(days_since_last_purchase, 90)::FLOAT / 180.0) * 0.6 +
                (CASE WHEN total_transactions < 3 THEN 0.3 ELSE 0.0 END) +
                (CASE WHEN avg_order_value < 100 THEN 0.1 ELSE 0.0 END))), 3),
            CASE WHEN (COALESCE(days_since_last_purchase, 90)::FLOAT / 180.0) * 0.6 +
                      (CASE WHEN total_transactions < 3 THEN 0.3 ELSE 0.0 END) +
                      (CASE WHEN avg_order_value < 100 THEN 0.1 ELSE 0.0 END) > 0.7 THEN 'HIGH'
                 WHEN (COALESCE(days_since_last_purchase, 90)::FLOAT / 180.0) * 0.6 +
                      (CASE WHEN total_transactions < 3 THEN 0.3 ELSE 0.0 END) +
                      (CASE WHEN avg_order_value < 100 THEN 0.1 ELSE 0.0 END) > 0.4 THEN 'MEDIUM'
                 ELSE 'LOW' END,
            CASE WHEN tier IN ('PLATINUM', 'GOLD') AND total_spend_usd > 2000 THEN 'VIP'
                 WHEN total_transactions >= 5 AND days_since_last_purchase < 60 THEN 'LOYAL'
                 WHEN days_since_last_purchase > 90 THEN 'AT_RISK'
                 WHEN tenure_days < 90 THEN 'NEW' ELSE 'DORMANT' END,
            CASE WHEN days_since_last_purchase > 90 THEN 'RE_ENGAGE'
                 WHEN tenure_days < 90 THEN 'ONBOARD'
                 WHEN tier IN ('PLATINUM', 'GOLD') AND total_spend_usd > 2000 THEN 'UPSELL'
                 ELSE 'RETAIN' END
        FROM {SCHEMA}.SILVER_LOYALTY_MEMBERS_ENRICHED""").collect()
    return session.sql(f"SELECT COUNT(*) FROM {SCHEMA}.GOLD_LOYALTY_CUSTOMER_INSIGHTS").collect()[0][0]


def refresh_gold_layer_main(session, feed_run_id_param=None):
    """Handler for REFRESH_GOLD_LAYER_PIPELINE procedure."""
    start = datetime.now(timezone.utc)
    if not feed_run_id_param:
        result = session.sql(f"""SELECT feed_run_id FROM {SCHEMA}.BRONZE_SERPAPI_FEED_RUN_LOG
            WHERE run_status IN ('SUCCESS','PARTIAL_SUCCESS')
            ORDER BY run_triggered_at DESC LIMIT 1""").collect()
        feed_run_id = result[0][0] if result else 'NO_FEED_RUN_YET'
    else:
        feed_run_id = feed_run_id_param
    if feed_run_id == 'NO_FEED_RUN_YET':
        return "No successful feed run found. Run INGEST_COMPETITOR_PRICES_FROM_SERPAPI first."

    sku_count = refresh_sku_pricing(session, feed_run_id)
    ai_count = generate_ai_recommendations(session, feed_run_id)
    sell_through_count = refresh_weekly_sell_through(session)
    promo_count = refresh_promotion_performance(session)
    returns_count = refresh_returns_analysis(session)
    loyalty_count = refresh_loyalty_insights(session)

    duration = round((datetime.now(timezone.utc) - start).total_seconds(), 1)
    return (f"Gold refresh complete. SKU Pricing: {sku_count}, AI Recs: {ai_count}, "
            f"Sell-Through: {sell_through_count}, Promotions: {promo_count}, "
            f"Returns: {returns_count}, Loyalty: {loyalty_count}. "
            f"Category summary auto-refreshes via dynamic table. Duration: {duration}s")
