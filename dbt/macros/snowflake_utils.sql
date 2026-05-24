{% macro get_max_updated_at(model, column='dbt_updated_at') %}
    {#
      Returns the maximum value of a timestamp column from an existing table.
      Used in incremental models to determine the lookback window.
      Returns '1900-01-01' if the table doesn't exist yet (first run).
    #}
    {% if is_incremental() %}
        (select coalesce(max({{ column }}), '1900-01-01'::timestamp_ntz) from {{ model }})
    {% else %}
        '1900-01-01'::timestamp_ntz
    {% endif %}
{% endmacro %}


{% macro not_empty_string(column_name) %}
    {# Generic test: column must not be an empty string after trimming #}
    trim({{ column_name }}) != ''
{% endmacro %}


{% macro is_valid_email(column_name) %}
    {# Generic test: validates email format using Snowflake RLIKE #}
    {{ column_name }} rlike '^[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}$'
{% endmacro %}


{% macro current_timestamp_ntz() %}
    {# Wrapper for Snowflake CURRENT_TIMESTAMP() with explicit NTZ cast #}
    convert_timezone('UTC', current_timestamp())::timestamp_ntz
{% endmacro %}
