# DFT to FHIR R4 mapping

This mapping is implemented by the `RCM DFT to FHIR Claim` Mirth channel. It accepts synthetic HL7 v2.5.1 DFT messages over MLLP on TCP 6662 and submits a FHIR transaction Bundle to HAPI FHIR.

| HL7 v2 source | FHIR target | Transformation rule |
|---|---|---|
| MSH-9.1 | Message routing | Require `DFT`. |
| MSH-7 | `Claim.created` fallback | Convert the first 8 characters from `YYYYMMDD...` to `YYYY-MM-DD`. |
| PID-3.1 | `Claim.patient.reference` | MRN is required and resolves to the same deterministic Patient id used by the ADT channel. |
| PV1-19.1 | `Claim.item[0].encounter[0].reference` | Encounter number is required and resolves to the ADT-created Encounter. |
| FT1-2 | `Claim.id`, `Claim.identifier.value` | Transaction/claim number; normalize and prefix the logical id with `claim-`. |
| FT1-4 | `Claim.created` | Preferred transaction date. |
| FT1-11 | `Claim.item[0].unitPrice` | Parse transaction amount as a USD decimal; reject nonnumeric values. |
| FT1-19.1 | `Claim.diagnosis[0]` | ICD-10-CM coding using `http://hl7.org/fhir/sid/icd-10-cm`; the synthetic fallback is I10. |
| FT1-25.1 | `Claim.item[0].productOrService` | CPT coding using `http://www.ama-assn.org/go/cpt`; the synthetic fallback is 99213. |
| Lab configuration | `Coverage`, `Claim.insurance`, `Claim.provider` | Create a synthetic active Coverage and reference seeded payer/provider records. Production use must source these fields from validated coverage and provider segments. |

The transaction contains Coverage followed by Claim, each written with an idempotent `PUT`. The Claim line links diagnosis sequence 1 to its ICD-10-CM diagnosis.

## Known scope boundaries

- This is an educational RCM mapping, not a complete institutional or professional billing specification.
- DFT alone does not contain every element needed for production adjudication or a Da Vinci PAS request.
- CPT content remains subject to AMA licensing; this repository stores only illustrative codes, not the CPT code set.
- Payer, subscriber, rendering provider, place of service, modifiers, authorization and coordination-of-benefits rules require an implementation-specific mapping profile.
