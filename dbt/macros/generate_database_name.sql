{% macro generate_database_name(custom_database_name, node) -%}

    {#
      Override dbt's default database naming to support environment-aware
      database resolution.

      Usage in models: {{ config(database=generate_database_name('SANDBOX')) }}

      Behaviour:
        - In prod: returns the database name as-is (e.g. SANDBOX)
        - In dev:  appends _DEV suffix (e.g. SANDBOX_DEV)
        - In ci:   returns whatever target.database is set to (the clone DB)

      For most models this macro is NOT needed because dbt inherits the
      target database. It exists for cross-database references where the
      source database differs from the target database.
    #}

    {%- if custom_database_name is none -%}

        {{ target.database }}

    {%- elif target.name == 'prod' -%}

        {{ custom_database_name | trim }}

    {%- elif target.name == 'ci' -%}

        {{ target.database }}

    {%- else -%}

        {{ custom_database_name | trim }}{{ var('env_suffix', '_DEV') }}

    {%- endif -%}

{%- endmacro %}
