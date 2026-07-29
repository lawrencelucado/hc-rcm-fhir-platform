# Test safety boundaries

## Safe automatic checks

These checks do not contact or change the homelab:

```text
python scripts/validate_repository.py
python -m unittest discover -s tests -p "test_safe_*.py" -v
docker compose --env-file .env.example config --quiet
```

The Compose command renders and validates configuration; it does not start
containers.

## Live Mirth/FHIR integration

`test_mirth_integration.py` sends synthetic HL7 messages and may create or
replace FHIR resources. It fails closed unless the operator deliberately sets:

```powershell
$env:RUN_LIVE_INTEGRATION_TESTS = "I_UNDERSTAND_THIS_CHANGES_LAB_STATE"
python tests\test_mirth_integration.py
Remove-Item Env:RUN_LIVE_INTEGRATION_TESTS
```

## Live SMART/OAuth integration

`test_smart_gateway.py` contacts live authentication services and requests an
OAuth token. It fails closed unless the operator deliberately sets:

```powershell
$env:RUN_LIVE_SMART_TESTS = "I_UNDERSTAND_THIS_CONTACTS_LIVE_AUTH"
$env:MIRTH_CLIENT_SECRET = "<retrieve securely for this test>"
python tests\test_smart_gateway.py
Remove-Item Env:RUN_LIVE_SMART_TESTS
Remove-Item Env:MIRTH_CLIENT_SECRET
```

Never commit the client secret or place either live acknowledgement variable in
routine CI. Live tests require an approved test window, synthetic data, known
recovery boundaries, and separate evidence from unit/static validation.
