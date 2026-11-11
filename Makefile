# Local workflow. Run `make env` once, edit .env, then `make up`.
include .env
export DB_HOST ?= localhost
export DB_PORT ?= 5432
export DB_NAME := $(POSTGRES_DB)
export DB_USER := $(POSTGRES_USER)
export DB_PASSWORD := $(POSTGRES_PASSWORD)
export MINIO_ACCESS_KEY := $(MINIO_ROOT_USER)
export MINIO_SECRET_KEY := $(MINIO_ROOT_PASSWORD)

.PHONY: env up down logs ps install seed etl dbt test pipeline

env:            ## create .env from the template (edit the passwords afterwards)
	@test -f .env || cp .env.example .env && echo ".env ready - change the passwords"

up:             ## start PostgreSQL, MinIO, Grafana, Splunk, forwarder, Airflow
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

install:        ## Python + dbt dependencies for running the pipeline from your machine
	pip install -r ingest/requirements.txt dbt-postgres==1.9.0

seed:           ## generate synthetic claims, remits, patients
	python ingest/generate_data.py

etl:            ## land files in MinIO and load the raw schema
	python ingest/load.py

dbt:            ## build curated and mart models
	cd dbt && dbt run --profiles-dir airflow_profiles --target docker

test:           ## dbt data-quality tests (fails on any violation)
	cd dbt && dbt test --profiles-dir airflow_profiles --target docker

pipeline:       ## everything end to end: schema, HIPAA controls, data, ETL, dbt build
	LOAD_SOURCE=local bash scripts/pipeline.sh
