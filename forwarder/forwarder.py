"""
Splunk PHI Audit Forwarder
Polls audit.access_log for unforwarded entries and ships them to Splunk HEC.
Implements HIPAA Audit Controls §164.312(b)
"""

import time
import json
import os
import logging
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("splunk-forwarder")

# Config from environment
# Secrets are required from the environment (docker-compose.yml + .env); there are no defaults.
PG_DSN = os.environ["PG_DSN"]
SPLUNK_HEC_URL = os.getenv("SPLUNK_HEC_URL", "https://rcm-splunk:8088/services/collector/event")
SPLUNK_HEC_TOKEN = os.environ["SPLUNK_HEC_TOKEN"]
SPLUNK_INDEX = os.getenv("SPLUNK_INDEX", "phi_audit")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))
SPLUNK_API_URL = os.getenv("SPLUNK_API_URL", "https://rcm-splunk:8089")
SPLUNK_ADMIN_PASS = os.environ["SPLUNK_ADMIN_PASS"]
# The local Splunk container uses a self-signed certificate, so TLS verification is off by
# default for development only. Set SPLUNK_VERIFY_TLS=true (or a CA bundle path) in production.
_verify = os.getenv("SPLUNK_VERIFY_TLS", "false")
VERIFY_TLS = {"true": True, "false": False}.get(_verify.lower(), _verify)


def wait_for_splunk(max_wait=300):
    """Wait for Splunk HEC to become available."""
    log.info("Waiting for Splunk HEC to be ready...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            r = requests.get(
                f"{SPLUNK_HEC_URL.replace('/services/collector/event', '/services/collector/health')}",
                headers={"Authorization": f"Splunk {SPLUNK_HEC_TOKEN}"},
                timeout=5, verify=VERIFY_TLS
            )
            if r.status_code in (200, 400):  # 400 means HEC is up but token might not match yet
                log.info("Splunk HEC is ready")
                return True
        except Exception:
            pass
        log.info("Splunk not ready yet, retrying in 15s...")
        time.sleep(15)
    return False


def ensure_index():
    """Create the phi_audit index in Splunk if it doesn't exist."""
    try:
        r = requests.post(
            f"{SPLUNK_API_URL}/services/data/indexes",
            auth=("admin", SPLUNK_ADMIN_PASS),
            data={"name": SPLUNK_INDEX, "maxTotalDataSizeMB": 1024},
            verify=VERIFY_TLS, timeout=10
        )
        if r.status_code in (200, 201, 409):  # 409 = already exists
            log.info(f"Splunk index '{SPLUNK_INDEX}' ready")
        else:
            log.warning(f"Index creation response: {r.status_code} {r.text[:100]}")
    except Exception as e:
        log.warning(f"Could not create index: {e}")


def fetch_unforwarded(conn):
    """Fetch audit log entries not yet sent to Splunk."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT log_id, accessed_at, db_user, table_name, operation,
                   row_count, application, client_ip, role_name, severity
            FROM audit.access_log
            WHERE splunk_sent = FALSE
            ORDER BY accessed_at ASC
            LIMIT 100
        """)
        return cur.fetchall()


def mark_forwarded(conn, log_ids):
    """Mark entries as forwarded."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE audit.access_log SET splunk_sent = TRUE WHERE log_id = ANY(%s)",
            (log_ids,)
        )
    conn.commit()


def send_to_splunk(events):
    """Send batch of events to Splunk HEC."""
    headers = {
        "Authorization": f"Splunk {SPLUNK_HEC_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = ""
    for event in events:
        # Determine if this is a PHI access that needs flagging
        is_phi = event["table_name"] in ("raw.patients",)
        is_suspicious = (
            event["severity"] == "WARNING" or
            event["db_user"] in ("unknown_user", "") or
            event["operation"] == "DELETE"
        )
        splunk_event = {
            "time": event["accessed_at"].timestamp(),
            "index": SPLUNK_INDEX,
            "sourcetype": "rcm:phi_audit",
            "source": "rcm-platform",
            "event": {
                "log_id": event["log_id"],
                "db_user": event["db_user"] or "unknown",
                "role": event["role_name"] or "unknown",
                "table": event["table_name"],
                "operation": event["operation"],
                "row_count": event["row_count"],
                "application": event["application"] or "unknown",
                "client_ip": event["client_ip"] or "unknown",
                "severity": event["severity"] or "INFO",
                "is_phi_access": is_phi,
                "is_suspicious": is_suspicious,
                "hipaa_control": "164.312(b) Audit Controls"
            }
        }
        payload += json.dumps(splunk_event) + "\n"

    try:
        r = requests.post(
            SPLUNK_HEC_URL, headers=headers, data=payload,
            timeout=10, verify=VERIFY_TLS
        )
        if r.status_code == 200:
            log.info(f"Forwarded {len(events)} events to Splunk")
            return True
        else:
            log.error(f"Splunk HEC error: {r.status_code} {r.text}")
            return False
    except Exception as e:
        log.error(f"Failed to send to Splunk: {e}")
        return False


def main():
    log.info("RCM Splunk PHI Audit Forwarder starting...")
    log.info(f"HEC URL: {SPLUNK_HEC_URL}")
    log.info(f"Poll interval: {POLL_INTERVAL}s")

    # Wait for Splunk
    if not wait_for_splunk():
        log.error("Splunk did not become ready in time. Exiting.")
        return

    time.sleep(10)  # Extra buffer for Splunk to fully initialize
    ensure_index()

    # Connect to PostgreSQL
    while True:
        try:
            conn = psycopg2.connect(PG_DSN)
            log.info("Connected to PostgreSQL")
            break
        except Exception as e:
            log.warning(f"PG not ready: {e}, retrying in 10s...")
            time.sleep(10)

    log.info("Forwarder running. Polling every %ds...", POLL_INTERVAL)

    while True:
        try:
            events = fetch_unforwarded(conn)
            if events:
                success = send_to_splunk(events)
                if success:
                    mark_forwarded(conn, [e["log_id"] for e in events])
                    phi_count = sum(1 for e in events if "patients" in (e["table_name"] or ""))
                    log.info(f"Processed {len(events)} events ({phi_count} PHI)")
            else:
                log.debug("No new audit events")
        except psycopg2.OperationalError:
            log.warning("PG connection lost, reconnecting...")
            try:
                conn = psycopg2.connect(PG_DSN)
            except Exception as e:
                log.error(f"Reconnect failed: {e}")
        except Exception as e:
            log.error(f"Forwarder error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
