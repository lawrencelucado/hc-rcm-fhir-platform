#!/usr/bin/env bash
# End-to-end pipeline against a running PostgreSQL:
#   schema -> HIPAA controls -> synthetic data -> ETL -> dbt build (models + tests)
# Used by `make pipeline` and by CI. Requires DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD.
set -euo pipefail
cd "$(dirname "$0")/.."

export PGHOST="${DB_HOST:-localhost}" PGPORT="${DB_PORT:-5432}" PGDATABASE="${DB_NAME:-rcm}" \
       PGUSER="${DB_USER:-rcm}" PGPASSWORD="${DB_PASSWORD:?DB_PASSWORD is required}"

echo "== 1/5 schema";          psql -v ON_ERROR_STOP=1 -q -f ingest/sql/init.sql
echo "== 2/5 HIPAA controls";  psql -v ON_ERROR_STOP=1 -q -f ingest/sql/hipaa_phase2.sql
echo "== 3/5 synthetic data";  python ingest/generate_data.py
echo "== 4/5 ETL";             python ingest/load.py
echo "== 5/5 dbt build";       (cd dbt && dbt build --profiles-dir airflow_profiles --target docker)
