{{ config(materialized='table') }}

select
    payer_id,
    payer_name,
    payer_type,
    timely_filing_days,
    loaded_at
from raw.payers
