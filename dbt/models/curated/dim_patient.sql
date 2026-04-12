{{ config(materialized='table') }}

select
    patient_id,
    first_name,
    last_name,
    first_name || ' ' || last_name   as full_name,
    dob,
    date_part('year', age(dob::date)) as age,
    gender,
    city,
    state,
    zip,
    mrn,
    insurance_id,
    payer_id,
    loaded_at
from raw.patients
