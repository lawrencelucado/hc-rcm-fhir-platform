# HC RCM FHIR Platform

[![ci](https://github.com/lawrencelucado/hc-rcm-fhir-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/lawrencelucado/hc-rcm-fhir-platform/actions/workflows/ci.yml)

A healthcare **revenue cycle (RCM) data platform** with **HIPAA technical safeguards built in**: synthetic 837/835-style claims and remittances flow through an ETL into PostgreSQL, dbt builds denial, A/R aging and payer analytics, Airflow orchestrates it, Grafana shows it, and every access to patient data is audited and shipped to Splunk.

Everything runs locally with Docker Compose. All data is synthetic, with no real PHI.

## What it does

| Area | Details |
|---|---|
| **Ingest** | Generates 10,000 claims, 10,000 remittances, 500 patients and 3,000 encounters with realistic denial patterns (CARC codes CO-4, CO-11, CO-16, CO-29, CO-45, CO-97, PR-96 and more; ~14% initial denial rate, varying by payer). The ETL lands files in MinIO (S3-compatible), then loads the `raw` schema. |
| **Transform (dbt)** | Curated: `dim_patient`, `dim_payer`, `dim_provider`, `fct_claims` (timely-filing flag), `fct_denials` (recovery category: Appealable / Patient Responsible / Write-off / Paid). Marts: `denial_summary`, `ar_aging`, `payer_scorecard` (A–D grade by denial rate), `audit_summary`. |
| **Data quality** | 38 dbt checks: keys, relationships, accepted values, plus business rules (paid never negative or above billed; denied claims pay $0 with a denial code; late-filed claims are denied CO-29). `dbt build` fails on any violation. |
| **HIPAA safeguards** | **Access control §164.312(a):** RBAC roles (`rcm_analyst`, `rcm_clinician`, `rcm_admin`), row-level security on the PHI table (clinicians see only their own patients), Safe Harbor identifiers tagged per column. **Audit controls §164.312(b):** `pgaudit` statement logging, triggers that log every insert/update/delete on patient data, and a forwarder that ships the audit log to a Splunk `phi_audit` index with a PHI-access dashboard. |
| **Orchestration** | Airflow: `rcm_full_pipeline` (daily: generate → load → dbt run → dbt test) and `rcm_dbt_refresh` (marts every 6 hours). |
| **Dashboards** | Grafana: totals, denial rate by payer, top denial codes, payer scorecard, A/R aging, recovery breakdown. Splunk: PHI audit events, warnings, access by role. |
| **CI** | GitHub Actions spins up PostgreSQL and runs the whole pipeline (schema → HIPAA controls → data → ETL → `dbt build`) on every push, plus a gitleaks secrets scan. |

## Architecture

```
generate_data.py ──► MinIO (rcm-raw/landing) ──► load.py ──► PostgreSQL raw ──► dbt ──► curated / mart
                                                                  │                         │
                                     RLS + RBAC + PHI triggers ───┤                         ├──► Grafana
                                     pgaudit statement logging ───┤                         │
                                                                  ▼                         │
                                                         audit.access_log ──► forwarder ──► Splunk (phi_audit)
                         Airflow schedules generate → load → dbt run → dbt test
```

More detail: [docs/architecture.md](docs/architecture.md) · [docs/data_model.md](docs/data_model.md)

## Quick start

```bash
cp .env.example .env          # then change every password in .env
make up                       # PostgreSQL, MinIO, Grafana, Splunk, forwarder, Airflow
make install                  # Python + dbt on your machine
make pipeline                 # schema, HIPAA controls, data, ETL, dbt build (with tests)
```

| Service | URL |
|---|---|
| Grafana | http://localhost:3000 |
| Airflow | http://localhost:8080 |
| MinIO console | http://localhost:9001 |
| Splunk | http://localhost:8000 (import `hipaa_dashboard.xml`) |

Individual steps: `make seed`, `make etl`, `make dbt`, `make test`.

## Security notes

- **No credentials in the repo.** Everything comes from `.env` (git-ignored); `.env.example` documents the variables. CI runs gitleaks on every push.
- Local Splunk uses a self-signed certificate, so TLS verification is off by default (`SPLUNK_VERIFY_TLS=false`). Set it to `true` or a CA bundle path anywhere real.
- Synthetic data only. Never load real PHI into a development environment.

## Project layout

```
ingest/      generate_data.py, load.py, sql/init.sql (schemas), sql/hipaa_phase2.sql (RBAC, RLS, audit)
dbt/         models/curated, models/mart, models/schema.yml (tests), tests/ (business rules)
airflow/     dags/rcm_full_pipeline.py, dags/rcm_dbt_refresh.py
forwarder/   audit log → Splunk HEC
grafana/     provisioning + RCM dashboard
postgres/    PostgreSQL 16 image with pgaudit
scripts/     pipeline.sh (end-to-end run used by make and CI)
api/         FastAPI service (health endpoint; metrics API planned)
```

## Roadmap

- [x] Phase 1: RCM data platform (ETL, dbt models, Grafana)
- [x] Phase 2: HIPAA technical safeguards (RBAC, RLS, pgaudit, PHI audit triggers, Splunk SIEM)
- [x] Data quality tests and CI for the full pipeline
- [ ] Phase 3: FHIR R4 export (Patient, Coverage, Claim, ClaimResponse/ExplanationOfBenefit)
- [ ] Phase 4: FastAPI metrics endpoints (denials, A/R, payer scorecard)
- [ ] Denial prediction model and appeal prioritization
