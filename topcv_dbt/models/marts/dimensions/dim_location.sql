{{ config(
    materialized='table',
    table_type='iceberg',
    format='parquet'
) }}

with locations as (
    select distinct
        province_city,
        location_detail
    from {{ ref('stg_topcv__job_locations') }}
    where province_city is not null
)

select
    to_hex(md5(to_utf8(
        concat(
            lower(trim(coalesce(province_city, ''))), '|',
            lower(trim(coalesce(location_detail, '')))
        )
    ))) as location_key,

    province_city,
    location_detail
from locations
