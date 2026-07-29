#!/usr/bin/env python3
"""End-to-end synthetic HL7 v2 MLLP to FHIR tests for the homelab."""

import json
import os
import socket
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MIRTH_HOST = os.getenv("MIRTH_HOST", "10.20.1.157")
FHIR_BASE_URL = os.getenv("FHIR_BASE_URL", "http://10.20.1.207:8090/fhir").rstrip("/")
LIVE_TEST_ACKNOWLEDGEMENT = "I_UNDERSTAND_THIS_CHANGES_LAB_STATE"


def require_live_test_acknowledgement() -> None:
    """Fail closed unless the operator explicitly authorizes live lab writes."""
    if os.getenv("RUN_LIVE_INTEGRATION_TESTS") != LIVE_TEST_ACKNOWLEDGEMENT:
        raise SystemExit(
            "BLOCKED: this script sends HL7 messages and may create FHIR "
            "resources. Set RUN_LIVE_INTEGRATION_TESTS to the documented "
            "acknowledgement value only when a live test is intentional."
        )


def hl7(*segments: str) -> str:
    return "\r".join(segments) + "\r"


ADT = hl7(
    "MSH|^~\\&|SYNTH_EHR|SYNTH_CLINIC|MIRTH|RCM_LAB|20260713194500||ADT^A01|ADT0001|P|2.5.1",
    "EVN|A01|20260713194500",
    "PID|1||SYNTH-0002^^^SYNTH^MR||Example^Jordan||19900115|O|||100 Test Lane^^Houston^TX^77001",
    "PV1|1|O|CLINIC^01^A||||1999999999^Clinician^Synthetic||||||||||||ENC-0002|||||||||||||||||||||||||20260713194500",
)

DFT = hl7(
    "MSH|^~\\&|SYNTH_BILLING|SYNTH_CLINIC|MIRTH|RCM_LAB|20260713194600||DFT^P03|DFT0001|P|2.5.1",
    "EVN|P03|20260713194600",
    "PID|1||SYNTH-0002^^^SYNTH^MR||Example^Jordan||19900115|O",
    "PV1|1|O|||||||||||||||||ENC-0002",
    "FT1|1|CLM-0002||20260713|20260713|CG|99213^Office visit^CPT|||1|125.00||||||||I10^Essential hypertension^ICD-10-CM||||||99213^Office visit^CPT",
)

MALFORMED_ADT = hl7(
    "MSH|^~\\&|SYNTH_EHR|SYNTH_CLINIC|MIRTH|RCM_LAB|20260713194700||ADT^A01|ADT-BAD-1|P|2.5.1",
    "PID|1||||Example^MissingMRN",
    "PV1|1|O||||||||||||||||ENC-BAD-1",
)


def send_mllp(port: int, message: str) -> str:
    payload = b"\x0b" + message.encode("utf-8") + b"\x1c\x0d"
    with socket.create_connection((MIRTH_HOST, port), timeout=10) as conn:
        conn.sendall(payload)
        conn.settimeout(30)
        response = b""
        while b"\x1c\x0d" not in response:
            chunk = conn.recv(4096)
            if not chunk:
                break
            response += chunk
    return response.strip(b"\x0b\x1c\x0d").decode("utf-8", errors="replace")


def ack_code(response: str) -> str:
    for segment in response.replace("\n", "\r").split("\r"):
        if segment.startswith("MSA|"):
            return segment.split("|")[1]
    raise AssertionError(f"No MSA segment in response: {response!r}")


def fhir_get(path: str) -> dict:
    req = Request(f"{FHIR_BASE_URL}/{path}", headers={"Accept": "application/fhir+json"})
    with urlopen(req, timeout=20) as response:
        return json.load(response)


def wait_for(path: str, resource_type: str, timeout: int = 30) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resource = fhir_get(path)
            if resource.get("resourceType") == resource_type:
                return resource
        except HTTPError as exc:
            if exc.code != 404:
                raise
        time.sleep(1)
    raise AssertionError(f"Timed out waiting for {resource_type} at {path}")


def main() -> None:
    require_live_test_acknowledgement()
    print("TEST: sending ADT", flush=True)
    adt_ack = send_mllp(6661, ADT)
    print(f"TEST: ADT ACK {ack_code(adt_ack)}", flush=True)
    assert ack_code(adt_ack) == "AA", adt_ack
    patient = wait_for("Patient/patient-synth-0002", "Patient")
    encounter = wait_for("Encounter/encounter-enc-0002", "Encounter")
    assert patient["identifier"][0]["value"] == "SYNTH-0002"
    assert encounter["subject"]["reference"] == "Patient/patient-synth-0002"

    print("TEST: sending DFT", flush=True)
    dft_ack = send_mllp(6662, DFT)
    print(f"TEST: DFT ACK {ack_code(dft_ack)}", flush=True)
    assert ack_code(dft_ack) == "AA", dft_ack
    claim = wait_for("Claim/claim-clm-0002", "Claim")
    assert claim["item"][0]["productOrService"]["coding"][0]["code"] == "99213"
    assert claim["diagnosis"][0]["diagnosisCodeableConcept"]["coding"][0]["system"] == "http://hl7.org/fhir/sid/icd-10-cm"
    assert claim["item"][0]["unitPrice"]["value"] == 125.0

    print("TEST: sending malformed ADT", flush=True)
    bad_ack = send_mllp(6661, MALFORMED_ADT)
    print(f"TEST: malformed ACK {ack_code(bad_ack)}", flush=True)
    assert ack_code(bad_ack) in {"AE", "AR"}, bad_ack

    recovery_ack = send_mllp(6661, ADT.replace("ADT0001", "ADT0002"))
    assert ack_code(recovery_ack) == "AA", recovery_ack
    print("PASS: ADT, DFT, malformed-message rejection, and recovery")


if __name__ == "__main__":
    main()
