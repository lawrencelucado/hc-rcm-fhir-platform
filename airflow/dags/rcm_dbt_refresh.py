"""
DAG: rcm_dbt_refresh
Refreshes dbt mart models every 6 hours (no data regeneration)
Use this to keep Grafana dashboards current without a full ETL run
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "rcm-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}

# Credentials come from the Airflow container environment (docker-compose.yml + .env);
# BashOperator tasks inherit it, so nothing secret lives in the DAG.

with DAG(
    dag_id="rcm_dbt_refresh",
    default_args=default_args,
    description="Refresh dbt mart models every 6 hours",
    schedule="0 */6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["rcm", "dbt", "refresh"],
) as dag:

    dbt_run = BashOperator(
        task_id="dbt_run_marts",
        bash_command=(
            "cd /opt/rcm/dbt && "
            "dbt run --profiles-dir /opt/rcm/dbt/airflow_profiles --target docker "
            "--select mart.*"
        ),
    )

    dbt_audit = BashOperator(
        task_id="dbt_run_audit_summary",
        bash_command=(
            "cd /opt/rcm/dbt && "
            "dbt run --profiles-dir /opt/rcm/dbt/airflow_profiles --target docker "
            "--select audit_summary"
        ),
    )

    dbt_run >> dbt_audit
