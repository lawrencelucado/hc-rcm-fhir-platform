-- ============================================================
-- Phase 2: HIPAA Technical Safeguards
-- Access Control (§164.312a) + Audit Controls (§164.312b)
-- ============================================================

-- ── 1. Extend audit.access_log for richer HIPAA logging ──
ALTER TABLE audit.access_log
  ADD COLUMN IF NOT EXISTS client_ip   VARCHAR(50),
  ADD COLUMN IF NOT EXISTS role_name   VARCHAR(100),
  ADD COLUMN IF NOT EXISTS severity    VARCHAR(20) DEFAULT 'INFO',
  ADD COLUMN IF NOT EXISTS splunk_sent BOOLEAN DEFAULT FALSE;

-- ── 2. Create RBAC roles ──
DO $$ BEGIN CREATE ROLE rcm_analyst;    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE rcm_clinician;  EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE rcm_admin;      EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ── 3. Schema permissions ──
-- dbt creates these schemas on first run; create them here so the grants work in any order.
CREATE SCHEMA IF NOT EXISTS curated_curated;
CREATE SCHEMA IF NOT EXISTS curated_mart;
GRANT USAGE ON SCHEMA raw            TO rcm_analyst, rcm_clinician, rcm_admin;
GRANT USAGE ON SCHEMA curated_curated TO rcm_analyst, rcm_admin;
GRANT USAGE ON SCHEMA curated_mart    TO rcm_analyst, rcm_admin;
GRANT USAGE ON SCHEMA audit           TO rcm_admin;

-- Non-PHI tables: analysts and clinicians can read
GRANT SELECT ON raw.payers, raw.providers, raw.claims, raw.remittance, raw.encounters
  TO rcm_analyst, rcm_admin;
GRANT SELECT ON raw.payers, raw.providers
  TO rcm_clinician;

-- Curated and mart: analysts and admins
GRANT SELECT ON ALL TABLES IN SCHEMA curated_curated TO rcm_analyst, rcm_admin;
GRANT SELECT ON ALL TABLES IN SCHEMA curated_mart    TO rcm_analyst, rcm_admin;
-- Tables dbt builds later inherit the same read access
ALTER DEFAULT PRIVILEGES IN SCHEMA curated_curated GRANT SELECT ON TABLES TO rcm_analyst, rcm_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA curated_mart    GRANT SELECT ON TABLES TO rcm_analyst, rcm_admin;

-- Audit log: admin only
GRANT SELECT ON audit.access_log TO rcm_admin;

-- PHI table (raw.patients): clinicians and admins only (controlled by RLS)
GRANT SELECT ON raw.patients TO rcm_clinician, rcm_admin;

-- ── 4. Row-Level Security on raw.patients (PHI) ──
ALTER TABLE raw.patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw.patients FORCE ROW LEVEL SECURITY;

-- Drop existing policies if re-running
DROP POLICY IF EXISTS patients_admin_policy     ON raw.patients;
DROP POLICY IF EXISTS patients_clinician_policy ON raw.patients;

-- Admin: full access
CREATE POLICY patients_admin_policy ON raw.patients
  AS PERMISSIVE FOR ALL
  TO rcm_admin
  USING (true);

-- Clinician: only their patients (provider set via SET LOCAL app.provider_id)
CREATE POLICY patients_clinician_policy ON raw.patients
  AS PERMISSIVE FOR SELECT
  TO rcm_clinician
  USING (
    patient_id IN (
      SELECT DISTINCT patient_id FROM raw.claims
      WHERE provider_id = current_setting('app.provider_id', true)
    )
  );

-- ── 5. PHI column tagging (§164.514(b) Safe Harbor identifiers) ──
COMMENT ON COLUMN raw.patients.patient_id    IS 'PHI_TAG:DIRECT_IDENTIFIER';
COMMENT ON COLUMN raw.patients.first_name    IS 'PHI_TAG:DIRECT_IDENTIFIER';
COMMENT ON COLUMN raw.patients.last_name     IS 'PHI_TAG:DIRECT_IDENTIFIER';
COMMENT ON COLUMN raw.patients.dob           IS 'PHI_TAG:DIRECT_IDENTIFIER';
COMMENT ON COLUMN raw.patients.address_line1 IS 'PHI_TAG:DIRECT_IDENTIFIER';
COMMENT ON COLUMN raw.patients.city          IS 'PHI_TAG:DIRECT_IDENTIFIER';
COMMENT ON COLUMN raw.patients.zip           IS 'PHI_TAG:DIRECT_IDENTIFIER';
COMMENT ON COLUMN raw.patients.mrn           IS 'PHI_TAG:DIRECT_IDENTIFIER';
COMMENT ON COLUMN raw.patients.insurance_id  IS 'PHI_TAG:DIRECT_IDENTIFIER';
COMMENT ON COLUMN raw.patients.gender        IS 'PHI_TAG:QUASI_IDENTIFIER';
COMMENT ON COLUMN raw.patients.state         IS 'PHI_TAG:QUASI_IDENTIFIER';

-- ── 6. PHI access logging function ──
CREATE OR REPLACE FUNCTION audit.log_phi_access()
RETURNS TRIGGER AS $$
DECLARE
  v_record_id VARCHAR(50);
  v_severity  VARCHAR(20);
BEGIN
  -- Determine record id
  IF TG_OP = 'DELETE' THEN
    v_record_id := OLD.patient_id;
  ELSE
    v_record_id := NEW.patient_id;
  END IF;

  -- Escalate severity for DELETE/UPDATE on PHI
  IF TG_OP IN ('DELETE', 'UPDATE') THEN
    v_severity := 'WARNING';
  ELSE
    v_severity := 'INFO';
  END IF;

  INSERT INTO audit.access_log (
    accessed_at, db_user, table_name, operation,
    row_count, application, client_ip, role_name, severity, splunk_sent
  ) VALUES (
    NOW(), CURRENT_USER, TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME, TG_OP,
    1, 'db-trigger',
    inet_client_addr()::text,
    current_setting('role', true),
    v_severity,
    FALSE
  );

  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ── 7. Attach trigger to PHI tables ──
DROP TRIGGER IF EXISTS phi_audit_insert ON raw.patients;
DROP TRIGGER IF EXISTS phi_audit_update ON raw.patients;
DROP TRIGGER IF EXISTS phi_audit_delete ON raw.patients;

CREATE TRIGGER phi_audit_insert
  AFTER INSERT ON raw.patients
  FOR EACH ROW EXECUTE FUNCTION audit.log_phi_access();

CREATE TRIGGER phi_audit_update
  AFTER UPDATE ON raw.patients
  FOR EACH ROW EXECUTE FUNCTION audit.log_phi_access();

CREATE TRIGGER phi_audit_delete
  AFTER DELETE ON raw.patients
  FOR EACH ROW EXECUTE FUNCTION audit.log_phi_access();

-- ── 8. Seed demo audit events (simulates PHI access activity) ──
INSERT INTO audit.access_log (accessed_at, db_user, table_name, operation, row_count, application, client_ip, role_name, severity, splunk_sent)
VALUES
  (NOW() - INTERVAL '2 hours',  'rcm_admin',     'raw.patients', 'SELECT', 500, 'grafana',     '192.0.2.10',  'rcm_admin',     'INFO',    FALSE),
  (NOW() - INTERVAL '90 min',   'rcm_clinician', 'raw.patients', 'SELECT', 12,  'emr-app',     '192.0.2.50',  'rcm_clinician', 'INFO',    FALSE),
  (NOW() - INTERVAL '60 min',   'rcm_analyst',   'raw.patients', 'SELECT', 500, 'bi-tool',     '192.0.2.75',  'rcm_analyst',   'WARNING', FALSE),
  (NOW() - INTERVAL '45 min',   'rcm_admin',     'raw.patients', 'UPDATE', 3,   'admin-panel',  '192.0.2.10',  'rcm_admin',     'WARNING', FALSE),
  (NOW() - INTERVAL '30 min',   'rcm_clinician', 'raw.patients', 'SELECT', 8,   'emr-app',     '192.0.2.51',  'rcm_clinician', 'INFO',    FALSE),
  (NOW() - INTERVAL '15 min',   'unknown_user',  'raw.patients', 'SELECT', 500, 'unknown',     '192.168.1.99','',              'WARNING', FALSE),
  (NOW() - INTERVAL '5 min',    'rcm_admin',     'raw.patients', 'DELETE', 1,   'admin-panel', '192.0.2.10',  'rcm_admin',     'WARNING', FALSE),
  (NOW() - INTERVAL '2 min',    'rcm_analyst',   'raw.claims',   'SELECT', 10000,'bi-tool',    '192.0.2.75',  'rcm_analyst',   'INFO',    FALSE),
  (NOW(),                        'rcm_clinician', 'raw.patients', 'SELECT', 5,   'emr-app',     '192.0.2.50',  'rcm_clinician', 'INFO',    FALSE);

SELECT 'HIPAA Phase 2 controls applied' AS status;
