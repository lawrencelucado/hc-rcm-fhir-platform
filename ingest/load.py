"""
RCM ETL — Load CSV files from MinIO into PostgreSQL raw schema
"""
import csv
import os
import io
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from minio import Minio

# ─── Config ───────────────────────────────────────────────────────────────────

# Credentials must come from the environment (see .env.example). No defaults for secrets.
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "rcm"),
    "user":     os.getenv("DB_USER", "rcm"),
    "password": os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD"),
}

MINIO_CONFIG = {
    "endpoint":   os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    "access_key": os.getenv("MINIO_ACCESS_KEY") or os.getenv("MINIO_ROOT_USER"),
    "secret_key": os.getenv("MINIO_SECRET_KEY") or os.getenv("MINIO_ROOT_PASSWORD"),
    "secure":     False,
    "bucket":     "rcm-raw",
}

# LOAD_SOURCE=minio (default): land files in MinIO, then load from there.
# LOAD_SOURCE=local: read the CSVs straight from data/ (used in CI, where MinIO isn't running).
LOAD_SOURCE = os.getenv("LOAD_SOURCE", "minio")

LOCAL_DATA_DIR = Path(__file__).parent.parent / "data"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def get_minio():
    client = Minio(
        MINIO_CONFIG["endpoint"],
        access_key=MINIO_CONFIG["access_key"],
        secret_key=MINIO_CONFIG["secret_key"],
        secure=MINIO_CONFIG["secure"],
    )
    if not client.bucket_exists(MINIO_CONFIG["bucket"]):
        client.make_bucket(MINIO_CONFIG["bucket"])
        print(f"  created bucket: {MINIO_CONFIG['bucket']}")
    return client

def upload_to_minio(client, local_path: Path):
    object_name = f"landing/{local_path.name}"
    client.fput_object(MINIO_CONFIG["bucket"], object_name, str(local_path))
    print(f"  uploaded → s3://{MINIO_CONFIG['bucket']}/{object_name}")
    return object_name

def read_csv_from_minio(client, object_name):
    response = client.get_object(MINIO_CONFIG["bucket"], object_name)
    content  = response.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(content)))

def coerce(row, field, cast):
    val = row.get(field, "")
    if val == "" or val is None:
        return None
    try:
        return cast(val)
    except (ValueError, TypeError):
        return None

# ─── Loaders ──────────────────────────────────────────────────────────────────

def load_payers(conn, rows):
    data = [(r["payer_id"], r["payer_name"], r["payer_type"], coerce(r,"timely_filing_days",int)) for r in rows]
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO raw.payers (payer_id, payer_name, payer_type, timely_filing_days)
            VALUES %s ON CONFLICT (payer_id) DO NOTHING
        """, data)
    conn.commit()

def load_providers(conn, rows):
    data = [(r["provider_id"], r["npi"], r["first_name"], r["last_name"], r["specialty"], r["facility_name"]) for r in rows]
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO raw.providers (provider_id, npi, first_name, last_name, specialty, facility_name)
            VALUES %s ON CONFLICT (provider_id) DO NOTHING
        """, data)
    conn.commit()

def load_patients(conn, rows):
    data = [(
        r["patient_id"], r["first_name"], r["last_name"],
        coerce(r,"dob",lambda x: x), r["gender"],
        r["address_line1"], r["city"], r["state"], r["zip"],
        r["mrn"], r["insurance_id"], r["payer_id"]
    ) for r in rows]
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO raw.patients (patient_id, first_name, last_name, dob, gender,
                address_line1, city, state, zip, mrn, insurance_id, payer_id)
            VALUES %s ON CONFLICT (patient_id) DO NOTHING
        """, data)
    conn.commit()

def load_claims(conn, rows):
    data = [(
        r["claim_id"], r["patient_id"], r["payer_id"], r["provider_id"],
        coerce(r,"date_of_service",lambda x: x),
        coerce(r,"date_submitted",lambda x: x),
        r["claim_type"], r["primary_diagnosis"], r.get("secondary_diagnosis",""),
        r["procedure_code"], r.get("modifier",""), r.get("drg_code",""),
        coerce(r,"units",int),
        coerce(r,"billed_amount",float),
        r["claim_status"]
    ) for r in rows]
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO raw.claims (
                claim_id, patient_id, payer_id, provider_id,
                date_of_service, date_submitted, claim_type,
                primary_diagnosis, secondary_diagnosis,
                procedure_code, modifier, drg_code,
                units, billed_amount, claim_status)
            VALUES %s ON CONFLICT (claim_id) DO NOTHING
        """, data)
    conn.commit()

def load_remittance(conn, rows):
    data = [(
        r["remit_id"], r["claim_id"], r["patient_id"], r["payer_id"],
        coerce(r,"check_date",lambda x: x), r.get("check_number",""),
        coerce(r,"billed_amount",float), coerce(r,"paid_amount",float),
        coerce(r,"adjustment_amount",float), coerce(r,"patient_responsibility",float),
        # Paid claims have no denial: store NULL, not empty strings
        r.get("denial_code") or None, r.get("denial_category") or None, r.get("denial_reason") or None,
        r["is_denied"] in ("True","true","1",True)
    ) for r in rows]
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO raw.remittance (
                remit_id, claim_id, patient_id, payer_id,
                check_date, check_number,
                billed_amount, paid_amount, adjustment_amount, patient_responsibility,
                denial_code, denial_category, denial_reason, is_denied)
            VALUES %s ON CONFLICT (remit_id) DO NOTHING
        """, data)
    conn.commit()

def load_encounters(conn, rows):
    data = [(
        r["encounter_id"], r["patient_id"], r["provider_id"],
        coerce(r,"admit_date",lambda x: x),
        coerce(r,"discharge_date",lambda x: x),
        r["encounter_type"], r["primary_diagnosis"], r.get("drg_code",""),
        coerce(r,"length_of_stay",int), r.get("discharge_disposition","")
    ) for r in rows]
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO raw.encounters (
                encounter_id, patient_id, provider_id,
                admit_date, discharge_date, encounter_type,
                primary_diagnosis, drg_code, length_of_stay, discharge_disposition)
            VALUES %s ON CONFLICT (encounter_id) DO NOTHING
        """, data)
    conn.commit()

# ─── Pipeline ─────────────────────────────────────────────────────────────────

LOADERS = {
    "payers.csv":      load_payers,
    "providers.csv":   load_providers,
    "patients.csv":    load_patients,
    "claims.csv":      load_claims,
    "remittance.csv":  load_remittance,
    "encounters.csv":  load_encounters,
}

def run():
    print(f"=== RCM ETL Pipeline (source: {LOAD_SOURCE}) ===")
    if not DB_CONFIG["password"]:
        raise SystemExit("DB_PASSWORD is not set. Copy .env.example to .env, or export DB_PASSWORD.")
    minio = get_minio() if LOAD_SOURCE == "minio" else None
    conn  = get_db()

    for filename, loader in LOADERS.items():
        local_path = LOCAL_DATA_DIR / filename
        if not local_path.exists():
            print(f"  SKIP {filename} (not found locally)")
            continue

        print(f"\n[{filename}]")
        if minio is not None:
            object_name = upload_to_minio(minio, local_path)
            rows = read_csv_from_minio(minio, object_name)
            print(f"  loaded {len(rows):,} rows from MinIO")
        else:
            with open(local_path, newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            print(f"  loaded {len(rows):,} rows from {local_path.name}")
        loader(conn, rows)
        print(f"  inserted into raw schema")

        # Audit log
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO audit.access_log (table_name, operation, row_count, application)
                VALUES (%s, %s, %s, %s)
            """, (f"raw.{filename.replace('.csv','')}", "INSERT", len(rows), "rcm-etl"))
        conn.commit()

    conn.close()
    print("\n=== Done ===")

if __name__ == "__main__":
    run()
