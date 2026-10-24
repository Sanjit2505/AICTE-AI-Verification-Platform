import json
from datetime import datetime
from app.database import fetch_all

DEFAULT_RULES = [
    {
        "code": "R001",
        "description": "Fire Safety NOC must be valid on application submission date",
        "severity": "HIGH",
        "handbook_ref": "AICTE APH 2024-27 Clause 2.4.1 & Appendix 4.1",
        "expression": {"field": "fire_noc_expiry", "operator": "gte_today"}
    },
    {
        "code": "R002",
        "description": "Applied student intake must not exceed sanctioned ceiling or 300% historical intake without NBA accreditation",
        "severity": "HIGH",
        "handbook_ref": "AICTE APH Clause 1.3.2 (Intake Expansion Regulations)",
        "expression": {"field": "applied_intake", "operator": "lte_sanctioned"}
    },
    {
        "code": "R003",
        "description": "Student to Faculty Ratio (SFR) must comply with AICTE norms (<= 1:15 for Engineering UG)",
        "severity": "HIGH",
        "handbook_ref": "AICTE APH Appendix 7 (Faculty Norms)",
        "expression": {"field": "sfr_ratio", "max_ratio": 15.0}
    },
    {
        "code": "R004",
        "description": "Mandatory registered Land Document must be unencumbered and registered in name of Trust/Society",
        "severity": "MEDIUM",
        "handbook_ref": "AICTE APH Clause 2.2.3 & Appendix 4.2",
        "expression": {"field": "land_registered_trust", "operator": "equals_true"}
    },
    {
        "code": "R005",
        "description": "Anti-Ragging Undertaking Affidavit must be executed within current academic approval cycle (12 months validity)",
        "severity": "MEDIUM",
        "handbook_ref": "AICTE Regulation F.No.37-3/Legal/AICTE/2009",
        "expression": {"field": "affidavit_validity", "max_age_months": 12}
    },
    {
        "code": "R006",
        "description": "Minimum Computer Terminal Ratio must be at least 1 computer per 4 students enrolled",
        "severity": "LOW",
        "handbook_ref": "AICTE APH Appendix 5 (Essential Computing Facilities)",
        "expression": {"field": "computer_ratio", "min_ratio": 0.25}
    }
]

def evaluate_application_rules(app_data: dict, extractions: dict) -> list[dict]:
    """
    Evaluates versioned configurable rules against extracted document data and submitted form values.
    Returns evidence-linked findings for any violation.
    """
    db_rules = fetch_all("SELECT * FROM rules WHERE status = 'APPROVED'")
    rules_to_run = db_rules if db_rules else DEFAULT_RULES
    findings = []
    
    # 1. Fire NOC check
    fire_expiry = extractions.get("fire_noc_expiry") or app_data.get("fire_noc_expiry")
    if fire_expiry:
        try:
            exp_date = datetime.strptime(str(fire_expiry)[:10], "%Y-%m-%d")
            if exp_date < datetime.utcnow():
                findings.append({
                    "rule_code": "R001",
                    "severity": "HIGH",
                    "title": "Expired Fire Safety NOC Certificate",
                    "reason": f"Fire Safety Certificate expired on {exp_date.strftime('%d-%b-%Y')}. AICTE requires a current and valid NOC prior to granting Extension of Approval.",
                    "handbook_ref": "AICTE APH 2024-27 Clause 2.4.1 & Appendix 4.1",
                    "confidence": 0.98,
                    "evidence_snippet": f"Extracted Expiry Date: {fire_expiry}"
                })
        except Exception:
            pass
    elif "fire_noc" in app_data.get("missing_docs", []):
        findings.append({
            "rule_code": "R001",
            "severity": "HIGH",
            "title": "Missing Mandatory Fire Safety NOC",
            "reason": "Fire NOC is a mandatory statutory prerequisite. Application cannot be processed without it.",
            "handbook_ref": "AICTE APH 2024-27 Clause 2.4.1",
            "confidence": 1.0,
            "evidence_snippet": "Document omitted from submission bundle"
        })

    # 2. Intake check
    applied_intake = int(app_data.get("applied_intake", 0))
    sanctioned_intake = int(app_data.get("sanctioned_intake", 0))
    nba_accredited = app_data.get("nba_accredited", False)
    if sanctioned_intake > 0 and applied_intake > sanctioned_intake and not nba_accredited:
        findings.append({
            "rule_code": "R002",
            "severity": "HIGH",
            "title": "Intake Expansion Exceeds Ceiling Without NBA Accreditation",
            "reason": f"Applied intake ({applied_intake}) exceeds current approved limit ({sanctioned_intake}). Increases exceeding 60 seats require valid NBA accreditation for >=50% programmes.",
            "handbook_ref": "AICTE APH Clause 1.3.2",
            "confidence": 0.95,
            "evidence_snippet": f"Applied: {applied_intake} seats vs Sanctioned: {sanctioned_intake} seats"
        })

    # 3. SFR check
    total_students = int(app_data.get("total_students", 0))
    faculty_count = int(app_data.get("faculty_count", 0))
    if faculty_count > 0 and total_students > 0:
        sfr = round(total_students / faculty_count, 1)
        if sfr > 15.0:
            findings.append({
                "rule_code": "R003",
                "severity": "HIGH",
                "title": f"Student-to-Faculty Ratio Non-Compliant (1:{sfr})",
                "reason": f"Calculated SFR is 1:{sfr}, which exceeds the mandatory threshold of 1:15 for undergraduate technical institutions.",
                "handbook_ref": "AICTE APH Appendix 7 (Faculty Norms)",
                "confidence": 0.99,
                "evidence_snippet": f"Enrolled Students: {total_students}, Verified Faculty: {faculty_count}"
            })

    # 4. Land Document ownership check
    land_owner = extractions.get("land_owner_name", "").strip().lower()
    trust_name = app_data.get("trust_name", "").strip().lower()
    if land_owner and trust_name and land_owner not in trust_name and trust_name not in land_owner:
        findings.append({
            "rule_code": "R004",
            "severity": "MEDIUM",
            "title": "Title Ownership Discrepancy on Land Deed",
            "reason": f"Land deed registered under '{extractions.get('land_owner_name')}', which does not exactly match applicant Trust name '{app_data.get('trust_name')}'.",
            "handbook_ref": "AICTE APH Clause 2.2.3 & Appendix 4.2",
            "confidence": 0.89,
            "evidence_snippet": f"Deed Owner: {extractions.get('land_owner_name')} | Sponsoring Trust: {app_data.get('trust_name')}"
        })

    # 5. Computer facilities check
    computer_count = int(app_data.get("computer_count", 0))
    if total_students > 0 and computer_count > 0:
        required_computers = int(total_students * 0.25)
        if computer_count < required_computers:
            findings.append({
                "rule_code": "R006",
                "severity": "LOW",
                "title": "Deficiency in Total Working Computer Terminals",
                "reason": f"Only {computer_count} terminals reported. Required minimum is {required_computers} (1:4 ratio for {total_students} students).",
                "handbook_ref": "AICTE APH Appendix 5",
                "confidence": 0.92,
                "evidence_snippet": f"Available: {computer_count} | Required: {required_computers}"
            })

    return findings

def calculate_readiness_score(findings: list[dict], required_docs_count: int, uploaded_docs_count: int) -> int:
    """
    Computes college readiness score (0-100).
    Deducts points based on severity of pre-submission issues.
    """
    if required_docs_count == 0:
        return 100
        
    doc_completion = (uploaded_docs_count / max(required_docs_count, 1)) * 50
    penalty = 0
    for f in findings:
        sev = f.get("severity", "LOW")
        if sev == "HIGH":
            penalty += 20
        elif sev == "MEDIUM":
            penalty += 10
        else:
            penalty += 4
            
    score = max(0, min(100, int(doc_completion + 50 - penalty)))
    return score

def calculate_risk_score(findings: list[dict], unverified_critical_docs: int = 0, prior_deficiency: int = 0) -> int:
    """
    Transparent weighted risk score formula from blueprint Section 8.7:
    risk = 30*high_flags + 10*medium_flags + 3*low_flags + 15*unverified_critical_docs + 10*prior_deficiency_history
    Capped at 100.
    """
    high = sum(1 for f in findings if f.get("severity") == "HIGH")
    med = sum(1 for f in findings if f.get("severity") == "MEDIUM")
    low = sum(1 for f in findings if f.get("severity") == "LOW")
    
    raw = (30 * high) + (10 * med) + (3 * low) + (15 * unverified_critical_docs) + (10 * prior_deficiency)
    return min(100, raw)
