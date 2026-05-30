{{ config(
    materialized='table',
    table_type='iceberg',
    format='parquet'
) }}

with dates as (
    select distinct
        dt
    from {{ ref('stg_topcv__job_postings') }}
    where dt is not null
)

select
    cast(replace(cast(dt as varchar), '-', '') as integer) as date_key,
    dt as full_date,
    year(dt) as year,
    quarter(dt) as quarter,
    month(dt) as month,
    day(dt) as day
from dates
