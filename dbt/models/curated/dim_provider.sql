{{ config(materialized='table') }}

select
    provider_id,
    npi,
    first_name || ' ' || last_name as full_name,
    specialty,
    facility_name,
    loaded_at
from raw.providers
