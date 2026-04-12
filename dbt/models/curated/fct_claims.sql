{{ config(materialized='table') }}

select
    c.claim_id,
    c.patient_id,
    c.payer_id,
    c.provider_id,
    c.date_of_service,
    c.date_submitted,
    c.date_submitted - c.date_of_service   as days_to_submit,
    c.claim_type,
    c.primary_diagnosis,
    c.secondary_diagnosis,
    c.procedure_code,
    c.modifier,
    c.drg_code,
    c.units,
    c.billed_amount,
    c.claim_status,
    -- Payer info
    p.payer_name,
    p.payer_type,
    p.timely_filing_days,
    -- Late filing flag
    case
        when c.date_submitted - c.date_of_service > p.timely_filing_days
        then true else false
    end as is_late_filing,
    c.loaded_at
from raw.claims c
left join raw.payers p on c.payer_id = p.payer_id
