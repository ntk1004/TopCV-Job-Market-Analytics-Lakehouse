{{ config(
    materialized='table',
    table_type='iceberg',
    format='parquet'
) }}

with companies as (
    select distinct
        company_clean
    from {{ ref('stg_topcv__job_postings') }}
    where is_valid_record = true
      and company_clean is not null
)

select
    to_hex(md5(to_utf8(lower(trim(company_clean))))) as company_key,
    company_clean as company_name
from companies
