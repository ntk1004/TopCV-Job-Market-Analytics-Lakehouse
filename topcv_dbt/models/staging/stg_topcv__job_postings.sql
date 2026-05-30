with source as (
    select *
    from {{ source('topcv_silver', 'jobs_postings') }}
),

cleaned as (
    select
        cast(job_id as varchar) as job_id,

        company as company_raw,
        regexp_replace(lower(trim(company)), '\\s+', ' ') as company_clean,

        title as title_raw,
        regexp_replace(lower(trim(title)), '\\s+', ' ') as title_clean,

        experience as experience_raw,
        case
            when regexp_like(lower(trim(experience)), 'không yêu cầu|khong yeu cau') then 'no_required'
            when regexp_like(lower(trim(experience)), 'thoả thuận|thỏa thuận|thoa thuan') then 'negotiable'
            when regexp_like(lower(trim(experience)), '\\d+') then 'required'
            else 'unknown'
        end as experience_type,

        case
            when regexp_like(lower(trim(experience)), 'không yêu cầu|khong yeu cau') then 0
            when regexp_like(lower(trim(experience)), '\\d+') then cast(regexp_extract(lower(trim(experience)), '(\\d+)', 1) as integer)
            else null
        end as experience_years_min,

        job_description as job_description_raw,
        regexp_replace(lower(trim(regexp_replace(job_description, '[\\r\\n\\t]+', ' '))), '\\s+', ' ') as job_description_clean,

        skills as requirements_raw,
        regexp_replace(lower(trim(regexp_replace(skills, '[\\r\\n\\t]+', ' '))), '\\s+', ' ') as requirements_clean,

        job_url as job_url_raw,
        regexp_replace(job_url, '\\?.*$', '') as job_url_clean,

        salary_raw,
        salary_currency,
        salary_type,

        case
            when salary_type = 'negotiable' then null
            when salary_currency = 'USD' then 'usd'
            when regexp_like(lower(salary_raw), 'triệu|trieu') then 'million_vnd'
            when regexp_like(lower(salary_raw), 'vnd|vnđ|đồng|dong') then 'vnd'
            else 'unknown'
        end as salary_unit,

        cast(salary_min_vnd as double) as salary_min_vnd,
        cast(salary_max_vnd as double) as salary_max_vnd,
        cast(salary_avg_vnd as double) as salary_avg_vnd,
        cast(is_salary_parsed as boolean) as is_salary_parsed,

        primary_province_city,
        cast(location_count as integer) as location_count,
        cast(is_multi_location as boolean) as is_multi_location,

        cast(source_page as integer) as source_page,
        cast(crawl_time as timestamp) as crawl_time,
        cast(ingestion_time as timestamp) as ingestion_time,
        cast(dt as date) as dt,

        to_hex(md5(to_utf8(
            concat(
                coalesce(cast(job_id as varchar), ''), '|',
                coalesce(company, ''), '|',
                coalesce(title, ''), '|',
                coalesce(salary_raw, ''), '|',
                coalesce(primary_province_city, ''), '|',
                coalesce(job_description, ''), '|',
                coalesce(skills, '')
            )
        ))) as record_hash

    from source
),

validated as (
    select
        *,
        job_id is not null as is_valid_job_id,
        title_clean is not null and length(title_clean) > 0 as is_valid_title,
        company_clean is not null and length(company_clean) > 0 as is_valid_company,
        primary_province_city is not null and length(primary_province_city) > 0 as is_valid_location,
        case
            when salary_type = 'negotiable' then true
            when salary_min_vnd is not null or salary_max_vnd is not null then true
            else false
        end as is_valid_salary
    from cleaned
)

select
    *,
    (
        is_valid_job_id
        and is_valid_title
        and is_valid_company
        and is_valid_location
        and is_valid_salary
    ) as is_valid_record
from validated
