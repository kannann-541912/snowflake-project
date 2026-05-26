{% macro generate_schema_name(custom_schema_name, node) -%}

    {#
      Override dbt's default schema naming to avoid prefixing the target schema
      with the base schema name.

      Default dbt behaviour:  <target_schema>_<custom_schema>   (e.g. TPCH_staging)
      This override:           <custom_schema>                    (e.g. staging)

      In PROD the custom_schema is used as-is (STAGING, MARTS, SNAPSHOTS).
      In DEV, the target.schema is used to isolate developer sandboxes.
    #}

    {%- set default_schema = target.schema -%}

    {%- if custom_schema_name is none -%}

        {{ default_schema }}

    {%- elif target.name == 'prod' -%}

        {# In prod, use the exact custom schema name without any prefix #}
        {{ custom_schema_name | trim }}

    {%- else -%}

        {# In dev/ci, namespace schemas under the developer's target schema #}
        {{ default_schema }}_{{ custom_schema_name | trim }}

    {%- endif -%}

{%- endmacro %}
