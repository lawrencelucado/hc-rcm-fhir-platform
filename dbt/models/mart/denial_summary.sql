{{ config(materialized='table') }}

select
    payer_name,
    payer_type,
    denial_code,
    denial_category,
    denial_reason,
    count(*)                                       as denial_count,
    sum(billed_amount)                             as total_billed,
    sum(case when recovery_category = 'Appealable'
             then billed_amount else 0 end)        as appealable_amount,
    round(count(*) * 100.0 /
          sum(count(*)) over (partition by payer_name), 2) as pct_of_payer_denials
from {{ ref('fct_denials') }}
where is_denied = true
group by payer_name, payer_type, denial_code, denial_category, denial_reason
order by denial_count desc
