select
    cast(job_id as varchar) as job_id,
    cast(location_order as integer) as location_order,
    regexp_replace(trim(location_raw_item), '\\s+', ' ') as location_raw_item,
    regexp_replace(trim(province_city), '\\s+', ' ') as province_city,
    regexp_replace(trim(location_detail), '\\s+', ' ') as location_detail
from {{ source('topcv_silver', 'jobs_locations') }}
where province_city is not null
  and length(trim(province_city)) > 0
