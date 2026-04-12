-- dbt model: mart.audit_summary
-- HIPAA Audit Controls §164.312(b) — PHI access summary for reporting

{{ config(schema='mart', materialized='table') }}

WITH base AS (
    SELECT
        DATE_TRUNC('hour', accessed_at) AS access_hour,
        db_user,
        role_name,
        table_name,
        operation,
        severity,
        client_ip,
        application,
        COUNT(*)                                                      AS event_count,
        SUM(row_count)                                                AS total_rows_accessed,
        SUM(CASE WHEN severity = 'WARNING' THEN 1 ELSE 0 END)        AS warning_count,
        SUM(CASE WHEN table_name = 'raw.patients' THEN 1 ELSE 0 END) AS phi_access_count
    FROM {{ source('audit', 'access_log') }}
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
)

SELECT
    access_hour,
    db_user,
    COALESCE(role_name, 'unknown')    AS role_name,
    table_name,
    operation,
    severity,
    client_ip,
    application,
    event_count,
    total_rows_accessed,
    warning_count,
    phi_access_count,
    CASE
        WHEN severity = 'WARNING'
          OR db_user NOT IN ('rcm_admin', 'rcm_analyst', 'rcm_clinician', 'rcm')
        THEN TRUE
        ELSE FALSE
    END                               AS is_suspicious
FROM base
ORDER BY access_hour DESC
