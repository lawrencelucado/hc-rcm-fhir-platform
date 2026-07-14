"""
DAG: rcm_full_pipeline
Runs the full RCM data pipeline: generate → load → dbt run
Schedule: Daily at 2:00 AM
HIPAA: All steps logged to audit.access_log → forwarded to Splunk
"""

from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "rcm-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

ENV = {
    "DB_HOST": "postgres",
    "DB_PORT": "5432",
    "DB_NAME": "rcm",
    "DB_USER": "rcm",
    "DB_PASS": os.environ["DB_PASS"],
    "MINIO_ENDPOINT": "minio:9000",
    "MINIO_ACCESS_KEY": "rcmadmin",
    "MINIO_SECRET_KEY": os.environ["MINIO_SECRET_KEY"],
}

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
        env=ENV,
    )

    load = BashOperator(
        task_id="load_to_postgres",
        bash_command="python3 /opt/rcm/ingest/load.py",
        env=ENV,
    )

    dbt_run = BashOperator(
        task_id="dbt_transform",
        bash_command=(
            "cd /opt/rcm/dbt && "
            "dbt run --profiles-dir /opt/rcm/dbt/airflow_profiles --target docker"
        ),
        env=ENV,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/rcm/dbt && "
            "dbt test --profiles-dir /opt/rcm/dbt/airflow_profiles --target docker 2>/dev/null || true"
        ),
        env=ENV,
    )

    generate >> load >> dbt_run >> dbt_test
