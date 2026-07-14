#!/usr/bin/env python3
"""Load and verify the synthetic RCM FHIR transaction using only stdlib."""

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

BASE_URL = os.getenv("FHIR_BASE_URL", "http://localhost:8090/fhir").rstrip("/")
ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "fhir" / "examples" / "rcm-claim-bundle.json"
FHIR_JSON = "application/fhir+json"


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(
        f"{BASE_URL}/{path.lstrip('/')}",
        data=data,
        method=method,
        headers={"Accept": FHIR_JSON, "Content-Type": FHIR_JSON},
    )
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def main() -> None:
    capability = request("GET", "metadata")
    assert capability["resourceType"] == "CapabilityStatement"
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    transaction = request("POST", "", bundle)
    assert transaction["resourceType"] == "Bundle"
    assert transaction["type"] == "transaction-response"
    assert len(transaction.get("entry", [])) == len(bundle["entry"])

    claim = request("GET", "Claim/claim-demo")
    assert claim["patient"]["reference"] == "Patient/patient-demo"
    results = request("GET", "Claim?identifier=https://example.org/claim-id|SYNTH-CLM-0001")
    assert results["resourceType"] == "Bundle" and results["total"] == 1
    print("PASS: FHIR capability, transaction, read, and identifier search")


if __name__ == "__main__":
    main()
