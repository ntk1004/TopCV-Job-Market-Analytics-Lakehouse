{{ config(
    materialized='table',
    table_type='iceberg',
    format='parquet'
) }}

with postings as (
    select *
    from {{ ref('stg_topcv__job_postings') }}
    where is_valid_record = true
),

company as (
    select *
    from {{ ref('dim_company') }}
),

job_dim as (
    select *
    from {{ ref('dim_job') }}
),

date_dim as (
    select *
    from {{ ref('dim_date') }}
)

select
    to_hex(md5(to_utf8(p.job_id))) as posting_key,
    p.job_id,

    c.company_key,
    j.job_key,
    d.date_key,

    p.job_url_clean,

    p.salary_currency,
    p.salary_type,
    p.salary_unit,
    p.salary_min_vnd,
    p.salary_max_vnd,
    p.salary_avg_vnd,
    p.is_salary_parsed,

    p.primary_province_city,
    p.location_count,
    p.is_multi_location,

    p.source_page,
    p.crawl_time,
    p.ingestion_time,
    p.dt,
    p.record_hash

from postings p
left join company c
    on p.company_clean = c.company_name
left join job_dim j
    on p.title_clean = j.job_title
    and coalesce(p.experience_type, '') = coalesce(j.experience_type, '')
    and coalesce(p.experience_years_min, -1) = coalesce(j.experience_years_min, -1)
left join date_dim d
    on p.dt = d.full_date
