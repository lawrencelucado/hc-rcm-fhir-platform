# hc-rcm-fhir-platform

Healthcare revenue cycle analytics and FHIR data platform built with Python, PostgreSQL, dbt, Airflow, FastAPI, and Docker.

## MVP Scope

This repository starts with a local, Docker Compose based MVP for a healthcare revenue cycle analytics platform. The first milestone is a runnable foundation, not a full production-grade data platform.

Included in this phase:

- PostgreSQL for operational and analytics storage
- MinIO for S3-compatible raw object storage
- FastAPI for health and future metrics endpoints
- Starter project structure for ETL, dbt, Airflow, and infrastructure docs
- Synthetic sample CSV data for core revenue cycle entities

Deferred to later phases:

- Full ETL implementation
- dbt models and tests
- Airflow DAG orchestration
- FHIR export pipeline
- Dashboards and screenshots

## Repository Layout

```text
.
|-- api/
|-- airflow/
|-- data/
|   |-- raw/
|   `-- sample/
|-- dbt/
|-- docs/
|-- etl/
`-- infra/
```

## Quick Start

Prerequisites:

- Docker
- Docker Compose v2
- GNU Make

Run the local stack:

```bash
make up
```

Validate the API:

```bash
curl http://localhost:8000/health
```

Stop the stack:

```bash
make down
```

## Services

- FastAPI: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`

## TODO

- Implement Python ETL from sample CSVs into raw tables
- Add `audit_log` and first raw schema
- Add curated models and denial marts
- Add first FHIR export slice
- Add Airflow DAG and dbt build flow

## AWS Mapping

This local MVP maps cleanly to a future AWS deployment:

- MinIO -> Amazon S3
- PostgreSQL -> Amazon RDS for PostgreSQL
- Docker Compose services -> ECS/Fargate or EKS
- FastAPI -> ECS/Fargate, App Runner, or EKS
- Airflow -> MWAA
- Batch ETL -> ECS tasks, Lambda, or Glue depending on workload
