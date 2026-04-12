{{ config(materialized='table') }}

select
    payer_name,
    payer_type,
    count(distinct claim_id)                                            as total_claims,
    sum(billed_amount)                                                  as total_billed,
    sum(paid_amount)                                                    as total_paid,
    sum(denied_amount)                                                  as total_denied,
    round(sum(paid_amount) / nullif(sum(billed_amount),0) * 100, 2)    as payment_rate_pct,
    round(sum(denied_amount) / nullif(sum(billed_amount),0) * 100, 2)  as denial_rate_pct,
    round(avg(days_to_payment) filter (where not is_denied), 1)        as avg_days_to_payment,
    -- Grade: A=<10% denial, B=10-20%, C=20-30%, D=>30%
    case
        when sum(denied_amount) / nullif(sum(billed_amount),0) < 0.10 then 'A'
        when sum(denied_amount) / nullif(sum(billed_amount),0) < 0.20 then 'B'
        when sum(denied_amount) / nullif(sum(billed_amount),0) < 0.30 then 'C'
        else 'D'
    end as payer_grade
from (
    select
        payer_name, payer_type, claim_id,
        billed_amount,
        paid_amount,
        case when is_denied then billed_amount else 0 end as denied_amount,
        days_to_payment,
        is_denied
    from {{ ref('fct_denials') }}
) sub
group by payer_name, payer_type
order by denial_rate_pct desc
