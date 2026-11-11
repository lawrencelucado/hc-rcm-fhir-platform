"""
DAG: rcm_full_pipeline
Runs the full RCM data pipeline: generate → load → dbt run
Schedule: Daily at 2:00 AM
HIPAA: All steps logged to audit.access_log → forwarded to Splunk
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "rcm-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

# Credentials come from the Airflow container environment (docker-compose.yml + .env);
# BashOperator tasks inherit it, so nothing secret lives in the DAG.

with DAG(
    dag_id="rcm_full_pipeline",
    default_args=default_args,
    description="Full RCM pipeline: generate → ETL load → dbt run",
    schedule="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["rcm", "etl", "hipaa"],
) as dag:

    generate = BashOperator(
        task_id="generate_synthetic_data",
        bash_command="python3 /opt/rcm/ingest/generate_data.py",
    )

    load = BashOperator(
        task_id="load_to_postgres",
        bash_command="python3 /opt/rcm/ingest/load.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_transform",
        bash_command=(
            "cd /opt/rcm/dbt && "
            "dbt run --profiles-dir /opt/rcm/dbt/airflow_profiles --target docker"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/rcm/dbt && "
            "dbt test --profiles-dir /opt/rcm/dbt/airflow_profiles --target docker"
        ),
    )

    generate >> load >> dbt_run >> dbt_test
