# Airflow DAGs

- `rcm_full_pipeline`: daily at 02:00 - generate synthetic data, load raw, `dbt run`, `dbt test` (a failed test fails the run)
- `rcm_dbt_refresh`: every 6 hours - rebuild marts and `audit_summary` for Grafana

Credentials are not in the DAGs: tasks inherit them from the Airflow container environment, which `docker-compose.yml` fills from `.env`.
