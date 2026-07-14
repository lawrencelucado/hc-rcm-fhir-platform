# HC RCM FHIR Platform

Healthcare Revenue Cycle + FHIR Data Platform
**Phase 2 — RCM + FHIR Integration Homelab**

## Stack
- PostgreSQL 16 (data warehouse)
- MinIO (raw file landing zone)
- Python ETL (CSV → raw schema)
- dbt (raw → curated → mart)
- FastAPI (coming in Phase 4)
- HAPI FHIR JPA Server 8.10 (FHIR R4)
- PostgreSQL 16 (isolated FHIR persistence)

## Quick Start

```bash
# 1. Create a local secrets file and replace every placeholder
cp .env.example .env

# 2. Start services
docker compose up -d

# 3. Install Python deps
cd ingest && pip install -r requirements.txt

# 4. Generate sample data
python generate_data.py

# 5. Run ETL
python load.py

# 6. Run dbt transforms
cd ../dbt
pip install dbt-postgres
dbt run
dbt test

# 7. Verify the FHIR transaction, read, and search workflow
python scripts/fhir_smoke_test.py
```

FHIR base URL: `http://localhost:8090/fhir`

All included data is synthetic. This lab is for learning and demonstration, not
for production clinical use or protected health information.

## Project Structure

```
hc-rcm-fhir-platform/
├── docker-compose.yml      PostgreSQL + MinIO
├── data/                   generated CSV files (gitignored)
├── ingest/
│   ├── sql/init.sql        schema definitions
│   ├── generate_data.py    sample data generator
│   ├── load.py             ETL pipeline
│   └── requirements.txt
├── dbt/
│   ├── models/curated/     dim_patient, dim_payer, fct_claims, fct_denials
│   └── models/mart/        denial_summary, ar_aging, payer_scorecard
├── fhir/                  HAPI configuration + synthetic RCM bundle
├── scripts/               repeatable validation tools
└── api/                   FastAPI (Phase 4)
```

## Data Model

### Raw Schema
Source-aligned tables: `patients`, `payers`, `providers`, `claims`, `remittance`, `encounters`

### Curated Schema (dbt)
- `dim_patient` — patient demographics
- `dim_payer` — payer reference
- `dim_provider` — provider reference
- `fct_claims` — claim facts with late filing flag
- `fct_denials` — remittance with recovery categorization

### Mart Schema (dbt)
- `denial_summary` — denials by payer + code
- `ar_aging` — AR aging buckets by payer
- `payer_scorecard` — payer grades (A-D)
