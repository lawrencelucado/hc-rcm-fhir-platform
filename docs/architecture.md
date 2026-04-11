# Architecture

## Objective

Build a local healthcare revenue cycle analytics platform that can ingest synthetic operational data, persist it in PostgreSQL, stage raw files in object storage, and expose a lightweight API for status and later metrics delivery.

## Initial Local Architecture

```text
sample CSV files
    |
    v
Python ETL (planned)
    |
    +--> PostgreSQL raw tables
    |
    +--> curated tables/views (planned)
    |
    +--> FHIR export files (planned)

FastAPI --> health + metrics endpoints
MinIO   --> raw object storage
Airflow --> orchestration (planned)
dbt     --> transformations and tests (planned)
```

## Design Notes

- PostgreSQL is the system of record for the MVP relational layer.
- MinIO provides S3-compatible local raw storage.
- FastAPI gives the platform a simple programmatic entry point.
- Docker Compose keeps local startup simple.

## Next Milestones

1. Add raw schema and loader script.
2. Add curated transforms and first denial analytics views.
3. Add FHIR export mappings for core entities.
4. Add orchestration and data quality checks.
