# Clinical and revenue-cycle terminology

The lab uses canonical coding-system URIs so downstream FHIR servers and validators can distinguish the vocabulary behind each code.

| Vocabulary | Canonical FHIR system | Lab use |
|---|---|---|
| ICD-10-CM | `http://hl7.org/fhir/sid/icd-10-cm` | DFT diagnosis to `Claim.diagnosis`. |
| CPT | `http://www.ama-assn.org/go/cpt` | DFT procedure/service to `Claim.item.productOrService`. |
| LOINC | `http://loinc.org` | Synthetic blood-pressure Observation example. |
| SNOMED CT | `http://snomed.info/sct` | Synthetic Condition example. |
| RxNorm | `http://www.nlm.nih.gov/research/umls/rxnorm` | Synthetic MedicationRequest example. |

The examples demonstrate correct system identification and resource placement; they are not a substitute for licensed terminology content, a terminology server, value-set expansion, or clinical coding review. Production work should add version-aware terminology services, `$validate-code`, value-set bindings, provenance, and governance for code updates.
