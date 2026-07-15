# Validation evidence

Run date: 2026-07-14. All records were synthetic.

## Mirth integration test

```text
TEST: sending ADT
TEST: ADT ACK AA
TEST: sending DFT
TEST: DFT ACK AA
TEST: sending malformed ADT
TEST: malformed ACK AE
PASS: ADT, DFT, malformed-message rejection, and recovery
```

Verified outputs included Patient, Encounter, Coverage and Claim resources in HAPI FHIR. The Claim line carried CPT, the Claim diagnosis carried ICD-10-CM, and replay used deterministic logical ids.

The Mirth container was then restarted. Both versioned channels returned automatically from the durable database and the complete integration test passed again, demonstrating service-restart recovery as well as message-level recovery.

## Terminology transaction

The synthetic transaction created a Condition using SNOMED CT, an Observation using LOINC and UCUM, and a MedicationRequest using RxNorm.

## US Core

HL7 Validator CLI 6.9.11 validated `us-core-patient-synth-0002.json` against FHIR R4 and `hl7.fhir.us.core#9.0.0`.

```text
Success: 0 errors, 5 warnings, 4 notes
```

The warnings were caused by unavailable external terminology/value-set content while the validator ran with `-tx n/a`; they were not structural profile errors. The lab does not claim full terminology conformance without a terminology server.

## OAuth2 and SMART discovery

```text
PASS: SMART discovery, unauthenticated rejection, OAuth token, protected FHIR access
```

The test verified SMART metadata with S256 PKCE, denial/redirect without authentication, Keycloak client-credentials token issuance, JWT audience validation and successful access to the protected FHIR CapabilityStatement.
