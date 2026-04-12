{{ config(materialized='table') }}

select
    payer_name,
    payer_type,
    count(*)                                                           as claim_count,
    sum(billed_amount)                                                 as total_billed,
    sum(case when days_to_payment between 0  and 30  then billed_amount end) as bucket_0_30,
    sum(case when days_to_payment between 31 and 60  then billed_amount end) as bucket_31_60,
    sum(case when days_to_payment between 61 and 90  then billed_amount end) as bucket_61_90,
    sum(case when days_to_payment > 90               then billed_amount end) as bucket_90_plus,
    sum(case when is_denied                          then billed_amount end) as denied_amount,
    round(sum(case when is_denied then 1 else 0 end) * 100.0 / count(*), 2) as denial_rate_pct,
    round(avg(days_to_payment) filter (where not is_denied), 1)        as avg_days_to_payment
from {{ ref('fct_denials') }}
group by payer_name, payer_type
order by total_billed desc
