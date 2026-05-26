{% test is_valid_email(model, column_name) %}

{#
  Generic dbt test: validates that a column contains a valid email format.
  Apply in YAML as:
    tests:
      - is_valid_email

  Fails if any row does NOT match the email regex.
#}

select {{ column_name }}
from {{ model }}
where {{ column_name }} is not null
  and not (
    {{ column_name }} rlike '^[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}$'
  )

{% endtest %}
