from datetime import datetime

class RegulatoryComplianceAgent:
    """
    Regulatory Rules Agent: Evaluates application parameters and extracted certificate fields
    strictly against AICTE Approval Process Handbook (APH 2024–2027) statutory norms.
    """
    def __init__(self):
        self.name = "AICTE Regulatory Rules Agent"

    def evaluate_compliance(self, form_data: dict, extractions: dict) -> list[dict]:
        findings = []

        # 1. Fire Safety NOC Expiry
        expiry = extractions.get("expiry_date")
        if expiry:
            try:
                exp_dt = datetime.strptime(expiry[:10], "%Y-%m-%d")
                if exp_dt < datetime.utcnow():
                    findings.append({
                        "rule_code": "R001",
                        "severity": "HIGH",
                        "title": "Expired Fire Safety NOC Certificate",
                        "reason": f"Fire Safety Certificate expired on {exp_dt.strftime('%d-%b-%Y')}. AICTE requires a current and valid NOC prior to granting Extension of Approval.",
                        "handbook_ref": "AICTE APH 2024-27 Clause 2.4.1 & Appendix 4.1",
                        "confidence": 0.99,
                        "evidence_snippet": f"Stated Expiry Date: {expiry}"
                    })
            except Exception:
                pass

        # 2. Intake Expansion Norms (Chapter 1, Clause 1.3.2)
        applied_intake = int(form_data.get("applied_intake", 0))
        sanctioned_intake = int(form_data.get("sanctioned_intake", 0))
        intake_increase = applied_intake - sanctioned_intake
        if intake_increase > 60:
            findings.append({
                "rule_code": "R002",
                "severity": "HIGH",
                "title": "Intake Expansion Exceeds Permissible Ceiling (+60 Seats)",
                "reason": f"Requested intake increase (+{intake_increase} seats) exceeds the standard ceiling of 60 seats per approval cycle. Increases above 60 require valid NBA accreditation for >=50% programmes or Top 100 NIRF ranking.",
                "handbook_ref": "AICTE APH 2024-27 Chapter 1, Clause 1.3.2",
                "confidence": 0.96,
                "evidence_snippet": f"Applied: {applied_intake} | Previous Approved: {sanctioned_intake}"
            })

        # 3. Faculty-Student Ratio (Annexure-5: 1:20 for UG Engineering, 1:12 for PG)
        total_students = int(form_data.get("total_students", 0))
        faculty_count = int(form_data.get("faculty_count", 0))
        if faculty_count > 0 and total_students > 0:
            sfr = round(total_students / faculty_count, 1)
            # Under APH 2024-27 Annexure 5, mandatory ratio is 1:20
            if sfr > 20.0:
                findings.append({
                    "rule_code": "R003",
                    "severity": "HIGH",
                    "title": f"Student-to-Faculty Ratio Non-Compliant (1:{sfr})",
                    "reason": f"Calculated SFR of 1:{sfr} violates AICTE APH 2024-27 Annexure-5 norms (mandatory minimum 1:20 for UG Engineering across all active operational years).",
                    "handbook_ref": "AICTE APH 2024-27 Annexure-5 (Faculty Requirements & Cadre)",
                    "confidence": 0.99,
                    "evidence_snippet": f"Enrolled Students: {total_students} | Full-Time Faculty: {faculty_count}"
                })

        # 4. Land Deed Ownership & Encumbrance (Appendix 4)
        land_area_extracted = extractions.get("land_area", "")
        doc_owner = extractions.get("entity_name_in_doc", "").lower()
        declared_trust = str(form_data.get("trust_name", "")).lower()

        if doc_owner and declared_trust:
            # Check for major trust mismatch
            words_owner = set(doc_owner.split())
            words_trust = set(declared_trust.split())
            overlap = words_owner.intersection(words_trust)
            if len(overlap) == 0:
                findings.append({
                    "rule_code": "R004",
                    "severity": "MEDIUM",
                    "title": "Title Ownership Discrepancy on Land Deed",
                    "reason": f"Land deed mentions entity '{extractions.get('entity_name_in_doc')}', which does not match applicant Trust name '{form_data.get('trust_name')}'. Land must be unencumbered in the Trust name.",
                    "handbook_ref": "AICTE APH 2024-27 Clause 2.2.3 & Appendix 4.2",
                    "confidence": 0.91,
                    "evidence_snippet": f"Deed Entity: {extractions.get('entity_name_in_doc')} vs Trust: {form_data.get('trust_name')}"
                })

        # 5. Essential Computing Terminals (Appendix 5: 1 per 4 students)
        computer_count = int(form_data.get("computer_count", 0))
        if total_students > 0:
            min_computers = int(total_students * 0.25)
            if computer_count < min_computers:
                findings.append({
                    "rule_code": "R006",
                    "severity": "LOW",
                    "title": "Deficiency in Total Working Computer Terminals",
                    "reason": f"Institution reports {computer_count} terminals. AICTE APH 2024-27 Appendix 5 mandates minimum {min_computers} terminals (1:4 ratio for {total_students} students).",
                    "handbook_ref": "AICTE APH 2024-27 Appendix 5 (Essential Computing Facilities)",
                    "confidence": 0.95,
                    "evidence_snippet": f"Available: {computer_count} | Mandated: {min_computers}"
                })

        return findings

regulatory_agent = RegulatoryComplianceAgent()
