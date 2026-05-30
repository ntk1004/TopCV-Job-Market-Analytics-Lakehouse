{{ config(
    materialized='table',
    table_type='iceberg',
    format='parquet'
) }}

with jobs as (
    select distinct
        title_clean,
        experience_type,
        experience_years_min
    from {{ ref('stg_topcv__job_postings') }}
    where is_valid_record = true
      and title_clean is not null
)

select
    to_hex(md5(to_utf8(
        concat(
            lower(trim(coalesce(title_clean, ''))), '|',
            lower(trim(coalesce(experience_type, ''))), '|',
            coalesce(cast(experience_years_min as varchar), '')
        )
    ))) as job_key,

    title_clean as job_title,
    experience_type,
    experience_years_min
from jobs
