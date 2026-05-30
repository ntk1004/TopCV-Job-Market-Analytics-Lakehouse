{{ config(
    materialized='table',
    table_type='iceberg',
    format='parquet'
) }}

with job_locations as (
    select *
    from {{ ref('stg_topcv__job_locations') }}
),

fact_posting as (
    select
        posting_key,
        job_id
    from {{ ref('fact_job_posting') }}
),

location_dim as (
    select *
    from {{ ref('dim_location') }}
)

select
    f.posting_key,
    l.location_key,
    jl.job_id,
    jl.location_order
from job_locations jl
join fact_posting f
    on jl.job_id = f.job_id
join location_dim l
    on jl.province_city = l.province_city
   and coalesce(jl.location_detail, '') = coalesce(l.location_detail, '')
