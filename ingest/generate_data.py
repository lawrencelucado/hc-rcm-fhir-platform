"""
RCM Sample Data Generator
Generates realistic 837/835-style claims and remittance data
"""
import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── Reference Data ───────────────────────────────────────────────────────────

PAYERS = [
    ("PAY001", "Blue Cross Blue Shield",  "commercial", 90),
    ("PAY002", "Aetna",                   "commercial", 90),
    ("PAY003", "Cigna",                   "commercial", 90),
    ("PAY004", "UnitedHealthcare",        "commercial", 90),
    ("PAY005", "Humana",                  "commercial", 90),
    ("PAY006", "Medicare Part B",         "medicare",   12),
    ("PAY007", "Medicare Part A",         "medicare",   12),
    ("PAY008", "Texas Medicaid",          "medicaid",   95),
]

PROVIDERS = [
    ("PRV001", "1234567890", "James",   "Carter",   "Internal Medicine",    "Houston Medical Group"),
    ("PRV002", "2345678901", "Maria",   "Santos",   "Emergency Medicine",   "Memorial Hermann"),
    ("PRV003", "3456789012", "David",   "Williams", "Cardiology",           "Texas Heart Institute"),
    ("PRV004", "4567890123", "Lisa",    "Johnson",  "Orthopedics",          "Houston Ortho Center"),
    ("PRV005", "5678901234", "Robert",  "Brown",    "General Surgery",      "St. Luke's Health"),
]

FIRST_NAMES = ["James","Maria","David","Lisa","Robert","Jennifer","Michael","Patricia","William","Linda",
               "Richard","Barbara","Joseph","Susan","Thomas","Jessica","Charles","Sarah","Christopher","Karen"]
LAST_NAMES  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
               "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"]

CPT_CODES = [
    ("99213", "Office visit, established, low"),
    ("99214", "Office visit, established, moderate"),
    ("99215", "Office visit, established, high"),
    ("99283", "ED visit, moderate severity"),
    ("99285", "ED visit, high severity"),
    ("93000", "Electrocardiogram"),
    ("71046", "Chest X-ray, 2 views"),
    ("80053", "Comprehensive metabolic panel"),
    ("36415", "Routine venipuncture"),
    ("27447", "Total knee arthroplasty"),
    ("33533", "Coronary artery bypass"),
    ("43239", "Upper GI endoscopy"),
    ("29881", "Knee arthroscopy"),
    ("47562", "Laparoscopic cholecystectomy"),
]

ICD10_CODES = [
    "I10",    # Essential hypertension
    "E11.9",  # Type 2 diabetes
    "J18.9",  # Pneumonia
    "M54.5",  # Low back pain
    "I25.10", # Coronary artery disease
    "F32.9",  # Major depressive disorder
    "K21.0",  # GERD with esophagitis
    "J44.1",  # COPD with exacerbation
    "N18.3",  # CKD stage 3
    "Z23",    # Encounter for immunization
]

DENIAL_RULES = [
    ("CO-29", "CO", "Timely filing limit exceeded",               0.08),
    ("CO-4",  "CO", "Procedure code inconsistent with modifier",  0.06),
    ("CO-97", "CO", "Payment included in another service",        0.05),
    ("CO-11", "CO", "Diagnosis inconsistent with procedure",      0.07),
    ("CO-16", "CO", "Claim lacks required information",           0.04),
    ("CO-50", "CO", "Non-covered service",                        0.03),
    ("PR-96", "PR", "Non-covered charge, patient responsibility", 0.04),
    ("CO-119","CO", "Benefit maximum for this time period reached",0.03),
    ("CO-18", "CO", "Duplicate claim",                            0.02),
    ("CO-45", "CO", "Charge exceeds fee schedule",                0.05),
]

MODIFIERS = ["", "", "", "25", "59", "GT", "26", "TC"]

# ─── Generators ───────────────────────────────────────────────────────────────

def rand_date(start_year=2024, end_year=2025):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def rand_dob():
    return date(random.randint(1940, 2005), random.randint(1,12), random.randint(1,28))

def generate_patients(n=500):
    rows = []
    states = ["TX","CA","FL","NY","PA","IL","OH","GA","NC","MI"]
    for i in range(n):
        pid = f"PAT{i+1:05d}"
        payer = random.choice(PAYERS)
        rows.append({
            "patient_id":   pid,
            "first_name":   random.choice(FIRST_NAMES),
            "last_name":    random.choice(LAST_NAMES),
            "dob":          rand_dob(),
            "gender":       random.choice(["M","F","M","F","M","F","U"]),
            "address_line1":f"{random.randint(100,9999)} {random.choice(LAST_NAMES)} St",
            "city":         random.choice(["Houston","Austin","Dallas","San Antonio","El Paso"]),
            "state":        random.choice(states),
            "zip":          f"{random.randint(10000,99999)}",
            "mrn":          f"MRN{random.randint(100000,999999)}",
            "insurance_id": f"INS{random.randint(1000000,9999999)}",
            "payer_id":     payer[0],
        })
    return rows

def generate_claims(patients, n=10000):
    rows = []
    patient_map = {p["patient_id"]: p for p in patients}
    for i in range(n):
        pid        = random.choice(list(patient_map.keys()))
        patient    = patient_map[pid]
        dos        = rand_date()
        submitted  = dos + timedelta(days=random.randint(1, 45))
        cpt, desc  = random.choice(CPT_CODES)
        modifier   = random.choice(MODIFIERS)
        billed     = round(random.uniform(75, 8500), 2)
        claim_type = "institutional" if cpt in ("27447","33533","43239","47562") else "professional"
        drg        = f"DRG{random.randint(100,999)}" if claim_type == "institutional" else ""
        rows.append({
            "claim_id":          f"CLM{i+1:07d}",
            "patient_id":        pid,
            "payer_id":          patient["payer_id"],
            "provider_id":       random.choice(PROVIDERS)[0],
            "date_of_service":   dos,
            "date_submitted":    submitted,
            "claim_type":        claim_type,
            "primary_diagnosis": random.choice(ICD10_CODES),
            "secondary_diagnosis": random.choice(ICD10_CODES + [""]),
            "procedure_code":    cpt,
            "modifier":          modifier,
            "drg_code":          drg,
            "units":             random.randint(1, 4),
            "billed_amount":     billed,
            "claim_status":      "submitted",
        })
    return rows

def generate_remittance(claims):
    rows = []
    payer_filing = {p[0]: p[3] for p in PAYERS}
    for claim in claims:
        billed     = claim["billed_amount"]
        dos        = claim["date_of_service"]
        submitted  = claim["date_submitted"]
        days_late  = (submitted - dos).days if isinstance(submitted, date) else 0
        filing_limit = payer_filing.get(claim["payer_id"], 90)
        is_late    = days_late > filing_limit

        # Determine denial
        denial_code = denial_cat = denial_reason = None
        is_denied   = False

        if is_late:
            denial_code, denial_cat, denial_reason, _ = DENIAL_RULES[0]  # CO-29
            is_denied = True
        else:
            roll = random.random()
            cumulative = 0
            for code, cat, reason, prob in DENIAL_RULES[1:]:
                cumulative += prob
                if roll < cumulative:
                    denial_code, denial_cat, denial_reason = code, cat, reason
                    is_denied = True
                    break

        if is_denied:
            paid   = 0.0
            adj    = billed
            pt_res = billed if denial_cat == "PR" else 0.0
        else:
            allowed  = round(billed * random.uniform(0.55, 0.85), 2)
            copay    = round(random.uniform(20, 150), 2)
            paid     = round(allowed - copay, 2)
            adj      = round(billed - allowed, 2)
            pt_res   = copay

        check_date = submitted + timedelta(days=random.randint(14, 45))

        rows.append({
            "remit_id":              f"REM{claim['claim_id'][3:]}",
            "claim_id":              claim["claim_id"],
            "patient_id":            claim["patient_id"],
            "payer_id":              claim["payer_id"],
            "check_date":            check_date,
            "check_number":          f"CHK{random.randint(1000000,9999999)}",
            "billed_amount":         billed,
            "paid_amount":           paid,
            "adjustment_amount":     adj,
            "patient_responsibility":pt_res,
            "denial_code":           denial_code or "",
            "denial_category":       denial_cat or "",
            "denial_reason":         denial_reason or "",
            "is_denied":             is_denied,
        })
    return rows

def generate_encounters(patients, n=3000):
    rows = []
    types = ["inpatient","outpatient","ED","outpatient","outpatient"]
    dispositions = ["Home","SNF","Expired","Home Health","Rehab Facility","Home","Home","Home"]
    for i in range(n):
        pid        = random.choice(patients)["patient_id"]
        admit      = rand_date()
        los        = random.randint(0, 12)
        discharge  = admit + timedelta(days=los)
        enc_type   = random.choice(types)
        rows.append({
            "encounter_id":          f"ENC{i+1:07d}",
            "patient_id":            pid,
            "provider_id":           random.choice(PROVIDERS)[0],
            "admit_date":            admit,
            "discharge_date":        discharge,
            "encounter_type":        enc_type,
            "primary_diagnosis":     random.choice(ICD10_CODES),
            "drg_code":              f"DRG{random.randint(100,999)}" if enc_type == "inpatient" else "",
            "length_of_stay":        los,
            "discharge_disposition": random.choice(dispositions) if enc_type == "inpatient" else "",
        })
    return rows

def write_csv(rows, filename):
    if not rows:
        return
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):,} rows → {filename}")

# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating sample data...")

    patients  = generate_patients(500)
    claims    = generate_claims(patients, 10000)
    remits    = generate_remittance(claims)
    encounters = generate_encounters(patients, 3000)

    write_csv(patients,   "patients.csv")
    write_csv(claims,     "claims.csv")
    write_csv(remits,     "remittance.csv")
    write_csv(encounters, "encounters.csv")

    # Write payers properly
    payer_rows = [{"payer_id":p[0],"payer_name":p[1],"payer_type":p[2],"timely_filing_days":p[3]} for p in PAYERS]
    write_csv(payer_rows, "payers.csv")

    provider_rows = [{"provider_id":p[0],"npi":p[1],"first_name":p[2],"last_name":p[3],"specialty":p[4],"facility_name":p[5]} for p in PROVIDERS]
    write_csv(provider_rows, "providers.csv")

    # Quick stats
    denied = sum(1 for r in remits if r["is_denied"])
    print(f"\nStats:")
    print(f"  Patients:   {len(patients):,}")
    print(f"  Claims:     {len(claims):,}")
    print(f"  Remits:     {len(remits):,}")
    print(f"  Denied:     {denied:,} ({denied/len(remits)*100:.1f}%)")
    print(f"  Encounters: {len(encounters):,}")
    print("\nDone.")
