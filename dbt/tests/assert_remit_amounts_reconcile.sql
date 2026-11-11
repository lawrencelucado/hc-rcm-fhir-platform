-- Remittance amounts must make financial sense. Returns the rows that break a rule;
-- dbt fails the test if any row comes back.
--   1. Paid is never negative and never exceeds billed
--   2. Denied claims pay nothing and carry a denial code
--   3. Paid claims carry no denial code
select remit_id, billed_amount, paid_amount, is_denied, denial_code
from {{ ref('fct_denials') }}
where paid_amount < 0
   or paid_amount > billed_amount
   or (is_denied and (paid_amount <> 0 or denial_code is null))
   or (not is_denied and denial_code is not null)
