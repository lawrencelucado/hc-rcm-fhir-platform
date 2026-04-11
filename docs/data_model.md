# Data Model

## Planned Core Entities

### patients

- `patient_id`
- `first_name`
- `last_name`
- `date_of_birth`
- `gender`
- `payer_id`

### encounters

- `encounter_id`
- `patient_id`
- `encounter_date`
- `facility_name`
- `provider_id`
- `encounter_type`

### claims

- `claim_id`
- `patient_id`
- `encounter_id`
- `payer_id`
- `claim_status`
- `total_charge_amount`
- `total_allowed_amount`
- `total_paid_amount`

### claim_lines

- `claim_line_id`
- `claim_id`
- `procedure_code`
- `revenue_code`
- `units`
- `charge_amount`
- `paid_amount`

### denials

- `denial_id`
- `claim_id`
- `claim_line_id`
- `payer_id`
- `denial_code`
- `denial_reason`
- `denial_status`
- `denial_amount`

### remits

- `remit_id`
- `claim_id`
- `payer_id`
- `remit_date`
- `allowed_amount`
- `paid_amount`
- `patient_responsibility_amount`

## Planned Schemas

- `raw`: landing tables loaded directly from sample files
- `curated`: cleaned and analytics-ready relational models
- `mart`: business-facing reporting outputs

## TODO

- finalize SQL types
- define keys and constraints
- add `audit_log`
- define FHIR resource mappings for Patient, Encounter, Coverage, and Claim
