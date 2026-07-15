# ADT to FHIR R4 mapping

This mapping is implemented by the `RCM ADT to FHIR Patient Encounter` Mirth channel. It accepts synthetic HL7 v2.5.1 ADT messages over MLLP on TCP 6661 and submits a FHIR transaction Bundle to HAPI FHIR.

| HL7 v2 source | FHIR target | Transformation rule |
|---|---|---|
| MSH-9.1 / MSH-9.2 | Message routing / `Encounter.status` | Require `ADT`; A03 maps to `finished`, all other accepted ADT triggers map to `in-progress`. |
| MSH-7 | `Encounter.period.start` fallback | Convert the first 8 characters from `YYYYMMDD...` to `YYYY-MM-DD`. |
| PID-3.1 | `Patient.id`, `Patient.identifier.value` | MRN is required. Normalize to lowercase URL-safe text and prefix the logical id with `patient-`. |
| PID-5.1 | `Patient.name.family` | Copy family name. |
| PID-5.2 | `Patient.name.given[0]` | Copy given name. |
| PID-7 | `Patient.birthDate` | Convert `YYYYMMDD` to FHIR date. |
| PID-8 | `Patient.gender` | M = male, F = female, O = other, otherwise unknown. |
| PV1-2 | `Encounter.class` | I = IMP, E = EMER, otherwise AMB; system is `http://terminology.hl7.org/CodeSystem/v3-ActCode`. |
| PV1-19.1 | `Encounter.id`, `Encounter.identifier.value` | Encounter number is required. Normalize and prefix the logical id with `encounter-`. |
| PV1-44 | `Encounter.period.start` | Preferred admission/start date, using the same date conversion as MSH-7. |
| PID-3 / PV1-19 | `Encounter.subject.reference` | Reference the deterministic Patient logical id. |

Both resources use conditional-free, idempotent `PUT` requests inside one FHIR transaction. Replaying a message updates the same logical resources rather than creating duplicates.

## Validation and error behavior

- Missing PID-3 or PV1-19 causes a negative application acknowledgment (`AE`).
- Wrong message families are rejected by the channel filter.
- HAPI FHIR errors are retried three times at five-second intervals.
- The source waits for destination completion, so the sender receives `AA` only after the destination succeeds.
- This lab uses synthetic records only and is not approved for PHI.
