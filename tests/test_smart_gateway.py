"""Live OAuth2/SMART gateway smoke test using synthetic lab credentials."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

BASE = os.getenv("SMART_BASE", "http://10.20.1.157:8091")
TOKEN_URL = os.getenv("SMART_TOKEN_URL", "http://10.20.1.157:8180/realms/healthcare/protocol/openid-connect/token")
LIVE_TEST_ACKNOWLEDGEMENT = "I_UNDERSTAND_THIS_CONTACTS_LIVE_AUTH"


def require_live_test_acknowledgement() -> None:
    """Fail closed unless the operator explicitly authorizes live auth use."""
    if os.getenv("RUN_LIVE_SMART_TESTS") != LIVE_TEST_ACKNOWLEDGEMENT:
        raise SystemExit(
            "BLOCKED: this script contacts live SMART and OAuth endpoints. "
            "Set RUN_LIVE_SMART_TESTS to the documented acknowledgement "
            "value only when a live test is intentional."
        )


def request(url, *, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status, response.read(), response.headers
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers


def main():
    require_live_test_acknowledgement()
    status, body, _ = request(f"{BASE}/.well-known/smart-configuration")
    assert status == 200
    smart = json.loads(body)
    assert smart["code_challenge_methods_supported"] == ["S256"]

    status, _, _ = request(f"{BASE}/fhir/metadata")
    assert status in (302, 401, 403), status

    client_secret = os.environ["MIRTH_CLIENT_SECRET"]
    form = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": "mirth-service",
        "client_secret": client_secret,
        "scope": "system/*.read system/*.write",
    }).encode()
    status, body, _ = request(TOKEN_URL, data=form, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert status == 200, body.decode(errors="replace")
    token = json.loads(body)["access_token"]

    status, body, _ = request(f"{BASE}/fhir/metadata", headers={"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"})
    assert status == 200, body.decode(errors="replace")
    assert json.loads(body)["resourceType"] == "CapabilityStatement"
    print("PASS: SMART discovery, unauthenticated rejection, OAuth token, protected FHIR access")


if __name__ == "__main__":
    main()
