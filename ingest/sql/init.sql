-- RCM Platform — Database Initialization
-- Creates raw, curated, mart, and audit schemas

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS curated;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS audit;

-- ─────────────────────────────────────────
-- RAW SCHEMA — exact shape of source files
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS raw.patients (
    patient_id          VARCHAR(20) PRIMARY KEY,
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    dob                 DATE,
    gender              VARCHAR(10),
    address_line1       VARCHAR(200),
    city                VARCHAR(100),
    state               CHAR(2),
    zip                 VARCHAR(10),
    mrn                 VARCHAR(20),
    insurance_id        VARCHAR(30),
    payer_id            VARCHAR(20),
    loaded_at           TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.payers (
    payer_id            VARCHAR(20) PRIMARY KEY,
    payer_name          VARCHAR(200),
    payer_type          VARCHAR(50),   -- commercial, medicare, medicaid
    timely_filing_days  INT,
    loaded_at           TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.providers (
    provider_id         VARCHAR(20) PRIMARY KEY,
    npi                 VARCHAR(10),
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    specialty           VARCHAR(100),
    facility_name       VARCHAR(200),
    loaded_at           TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.claims (
    claim_id            VARCHAR(30) PRIMARY KEY,
    patient_id          VARCHAR(20),
    payer_id            VARCHAR(20),
    provider_id         VARCHAR(20),
    date_of_service     DATE,
    date_submitted      DATE,
    claim_type          VARCHAR(20),   -- professional, institutional
    primary_diagnosis   VARCHAR(10),   -- ICD-10
    secondary_diagnosis VARCHAR(10),
    procedure_code      VARCHAR(10),   -- CPT
    modifier            VARCHAR(5),
    drg_code            VARCHAR(10),
    units               INT,
    billed_amount       NUMERIC(12,2),
    claim_status        VARCHAR(20),   -- submitted, paid, denied, appealed
    loaded_at           TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.remittance (
    remit_id            VARCHAR(30) PRIMARY KEY,
    claim_id            VARCHAR(30),
    patient_id          VARCHAR(20),
    payer_id            VARCHAR(20),
    check_date          DATE,
    check_number        VARCHAR(30),
    billed_amount       NUMERIC(12,2),
    paid_amount         NUMERIC(12,2),
    adjustment_amount   NUMERIC(12,2),
    patient_responsibility NUMERIC(12,2),
    denial_code         VARCHAR(10),   -- CO-29, PR-96, etc.
    denial_category     VARCHAR(5),    -- CO, PR, OA, PI
    denial_reason       TEXT,
    is_denied           BOOLEAN,
    loaded_at           TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.encounters (
    encounter_id        VARCHAR(30) PRIMARY KEY,
    patient_id          VARCHAR(20),
    provider_id         VARCHAR(20),
    admit_date          DATE,
    discharge_date      DATE,
    encounter_type      VARCHAR(50),   -- inpatient, outpatient, ED
    primary_diagnosis   VARCHAR(10),
    drg_code            VARCHAR(10),
    length_of_stay      INT,
    discharge_disposition VARCHAR(50),
    loaded_at           TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- AUDIT SCHEMA — HIPAA access logging
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit.access_log (
    log_id              BIGSERIAL PRIMARY KEY,
    accessed_at         TIMESTAMP DEFAULT NOW(),
    db_user             VARCHAR(100) DEFAULT CURRENT_USER,
    table_name          VARCHAR(100),
    operation           VARCHAR(10),   -- SELECT, INSERT, UPDATE, DELETE
    row_count           INT,
    application         VARCHAR(100)
);

-- ─────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_claims_patient    ON raw.claims(patient_id);
CREATE INDEX IF NOT EXISTS idx_claims_payer      ON raw.claims(payer_id);
CREATE INDEX IF NOT EXISTS idx_claims_dos        ON raw.claims(date_of_service);
CREATE INDEX IF NOT EXISTS idx_claims_status     ON raw.claims(claim_status);
CREATE INDEX IF NOT EXISTS idx_remit_claim       ON raw.remittance(claim_id);
CREATE INDEX IF NOT EXISTS idx_remit_denied      ON raw.remittance(is_denied);
CREATE INDEX IF NOT EXISTS idx_remit_denial_code ON raw.remittance(denial_code);
CREATE INDEX IF NOT EXISTS idx_encounters_patient ON raw.encounters(patient_id);
