# dbt project

- `models/curated/`: `dim_patient`, `dim_payer`, `dim_provider`, `fct_claims`, `fct_denials`
- `models/mart/`: `denial_summary`, `ar_aging`, `payer_scorecard`, `audit_summary`
- `models/schema.yml`: key, relationship and accepted-value tests
- `tests/`: business-rule tests (remit amounts reconcile; late filing is denied CO-29)

Run from the repo root with `make dbt` and `make test`, or everything at once with `make pipeline`.
The profile in `airflow_profiles/` reads connection settings from environment variables (`DB_HOST`, `DB_PASSWORD`, ...).
