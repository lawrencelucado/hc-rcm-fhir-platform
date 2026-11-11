-- Business rule: a claim submitted after the payer's timely-filing limit is denied CO-29.
-- Returns late-filed claims that were not denied for timely filing.
select c.claim_id, c.days_to_submit, c.timely_filing_days, d.denial_code
from {{ ref('fct_claims') }} c
join {{ ref('fct_denials') }} d on d.claim_id = c.claim_id
where c.is_late_filing
  and coalesce(d.denial_code, '') <> 'CO-29'
