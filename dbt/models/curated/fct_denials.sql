{{ config(materialized='table') }}

select
    r.remit_id,
    r.claim_id,
    r.patient_id,
    r.payer_id,
    r.check_date,
    r.billed_amount,
    r.paid_amount,
    r.adjustment_amount,
    r.patient_responsibility,
    r.denial_code,
    r.denial_category,
    r.denial_reason,
    r.is_denied,
    -- Claim context
    c.date_of_service,
    c.date_submitted,
    c.claim_type,
    c.primary_diagnosis,
    c.procedure_code,
    c.modifier,
    c.provider_id,
    -- Payer
    p.payer_name,
    p.payer_type,
    -- Days to payment
    r.check_date - c.date_of_service as days_to_payment,
    -- Recovery potential
    case
        when r.is_denied and r.denial_category = 'CO'
             and r.denial_code not in ('CO-45','CO-119') then 'Appealable'
        when r.is_denied and r.denial_category = 'PR' then 'Patient Responsible'
        when r.is_denied then 'Write-off'
        else 'Paid'
    end as recovery_category
from raw.remittance r
left join raw.claims  c on r.claim_id  = c.claim_id
left join raw.payers  p on r.payer_id  = p.payer_id
