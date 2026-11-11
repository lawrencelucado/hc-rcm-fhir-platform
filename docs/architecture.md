# Architecture

## Objective

A local healthcare revenue cycle analytics platform that ingests synthetic claims and remittance data, models it for denial and A/R analysis, and applies HIPAA technical safeguards (access control and audit controls) to patient data.

## Data flow

```text
ingest/generate_data.py      synthetic patients, payers, providers, claims (837-style),
        |                    remittances (835-style) with CARC denial codes, encounters
        v
MinIO  rcm-raw/landing/      S3-compatible landing zone (raw files kept as delivered)
        |
        v
ingest/load.py               loads PostgreSQL raw schema; logs each load to audit.access_log
        |
        v
PostgreSQL 16 + pgaudit      raw.*  (PHI in raw.patients: RLS + triggers)
        |
        v
dbt                          curated_curated.*  dims + facts
                             curated_mart.*     denial_summary, ar_aging, payer_scorecard, audit_summary
        |
        +--> Grafana         RCM analytics dashboard (provisioned datasource + dashboard)
        |
audit.access_log --> forwarder --> Splunk HEC (index phi_audit) --> PHI audit dashboard

Airflow: rcm_full_pipeline (daily 02:00) and rcm_dbt_refresh (every 6 hours)
```

## HIPAA technical safeguards (45 CFR 164.312)

| Requirement | Implementation |
|---|---|
| (a)(1) Access control | Roles `rcm_analyst` (no PHI), `rcm_clinician` (own patients only), `rcm_admin`; schema-level grants; default privileges for dbt-built tables |
| (a)(1) Minimum necessary | Row-level security on `raw.patients`; clinicians filtered by `app.provider_id` |
| 164.514(b) Identifiers | Safe Harbor identifiers tagged per column (`PHI_TAG:DIRECT_IDENTIFIER` / `QUASI_IDENTIFIER`) |
| (b) Audit controls | `pgaudit` read/write logging; insert/update/delete triggers on PHI; ETL load events; forwarder to Splunk SIEM; `audit_summary` mart flags suspicious access |

## Design notes

- PostgreSQL is the system of record; MinIO keeps the raw files as delivered, for replay.
- dbt owns all transformations and data-quality tests; `dbt build` fails the pipeline on any violation.
- All credentials come from the environment (`.env`), never from code or config files.
- CI runs the full pipeline against a fresh PostgreSQL on every push (`LOAD_SOURCE=local` skips MinIO).

## Next milestones

1. FHIR R4 export for Patient, Coverage, Claim and ExplanationOfBenefit.
2. FastAPI metrics endpoints on top of the marts.
3. Denial prediction and appeal prioritization.
