import os
from pypdf import PdfReader
from app.database import get_db

from app.config import BASE_DIR

def ingest_aph_reference_doc():
    pdf_path = BASE_DIR.parent / "doc needed" / "AICTE Approval Requirements Reference (APH 2024-27).pdf"
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    print(f"[*] Reading and ingesting {pdf_path} into MySQL...")
    reader = PdfReader(pdf_path)

    with get_db() as conn:
        with conn.cursor() as cursor:
            # 1. Ingest all 12 Application Categories
            categories = [
                (1, "NEW_INST", "New Technical Institution (via NSWS)", "APH Chapter I / Annexure-1"),
                (2, "EOA_CONT", "Extension of Approval (EoA) based on self-disclosure", "APH Chapter II / Annexure-2"),
                (3, "EOA_NEW_PROG", "EoA with additional/new programme or level", "APH Chapter II / Annexure-2"),
                (4, "EOA_BREAK", "EoA after a break in earlier years", "APH Chapter II"),
                (5, "EOA_ZERO_INTAKE", "EoA with zero intake for current year", "APH Chapter II"),
                (6, "EOA_RESTORATION", "Approval after hibernation / restoration of intake", "APH Chapter II"),
                (7, "EOA_THREE_YEAR", "Three-year Extended EoA for outstanding institutions", "APH Chapter II / NIRF / NBA"),
                (8, "OFF_CAMPUS", "Off-campus centre approval", "APH Chapter I / Annexure-1"),
                (9, "CHANGE_SITE", "Change of site / location", "Council Approval & Advocate Cert"),
                (10, "CLOSURE", "Progressive or complete closure", "Affidavit 4"),
                (11, "ODL_ONLINE", "ODL / Online mode programmes (Management / MCA)", "APH ODL Chapter"),
                (12, "CHANGE_NAME", "Change in name, trust/society, or merger", "APH Relevant Chapter")
            ]
            for cat in categories:
                cursor.execute("""
                    INSERT INTO application_categories (id, code, name, handbook_ref)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name), handbook_ref=VALUES(handbook_ref)
                """, cat)

            # 2. Ingest Master Checklist Items (Category 2 - EoA)
            master_checklist = [
                ("trust_reg", "Trust / Society / Company registration certificate", 1, 0),
                ("managing_resolution", "Managing body resolution authorising the application", 1, 12),
                ("portal_affidavit", "Portal-generated Affidavit(s), digitally signed", 1, 12),
                ("shared_premises_affidavit", "Affidavit that no other programmes share the same land/building", 1, 12),
                ("land_documents", "Land ownership or registered lease documents in trust name", 1, 0),
                ("land_possession", "Documents showing possession of land in trust name", 1, 0),
                ("land_conversion", "Land Conversion Certificate issued by State competent authority", 1, 0),
                ("advocate_certificate", "Certificate issued by an Advocate regarding land documents", 1, 12),
                ("approved_building_plan", "Approved building plan & certificate by Architect", 1, 0),
                ("occupancy_certificate", "Occupancy / Completion / Building License / Form D valid", 1, 0),
                ("structural_stability", "Structural stability certificate from chartered engineer", 1, 36),
                ("fire_safety_noc", "Fire and Life Safety Certificate (NOC) from competent authority", 1, 12),
                ("university_affiliation_noc", "NOC / Affiliation receipt from Affiliating University & State Govt", 1, 12),
                ("financial_statements", "Audited financial statements for last three financial years", 1, 12),
                ("faculty_cadre_data", "Faculty list with designation, cadre, qualifications & SFR", 1, 12),
                ("essential_infra_data", "Department-wise laboratories, workshops, computer centre, library", 1, 12),
                ("anti_ragging_declaration", "Anti-Ragging statutory compliance (AICTE Regulation 1 July 2009)", 1, 12),
                ("internal_complaints_committee", "Internal Complaints Committee (ICC) constitution declaration", 1, 12),
                ("grievance_redressal", "Online student & faculty grievance redressal mechanism", 1, 12),
                ("barrier_free_environment", "Barrier-free built environment for disabled and elderly persons", 1, 12),
                ("mandatory_disclosure", "Mandatory Disclosure published on official website (Annexure-18)", 1, 12)
            ]
            for idx, item in enumerate(master_checklist, start=1):
                cursor.execute("""
                    INSERT INTO checklist_items (id, checklist_id, doc_type, title, required, validity_months)
                    VALUES (%s, 1, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE title=VALUES(title), doc_type=VALUES(doc_type), required=VALUES(required)
                """, (idx, item[0], item[1], item[2], item[3]))

            # 3. Ingest Detailed Versioned Rules from Section 4 & 5
            detailed_rules = [
                (1, "R001", "Fire Safety Certificate must be current, valid, and issued by state fire authority", "HIGH", "AICTE APH Section 3.4 & Clause 2.4.1", '{"field": "fire_noc_expiry", "operator": "gte_today"}'),
                (2, "R002", "Applied student intake expansion capped at 60 seats without NBA or Top 100 NIRF", "HIGH", "AICTE APH Chapter 1, Clause 1.3.2", '{"field": "applied_intake", "operator": "lte_sanctioned"}'),
                (3, "R003", "Faculty-student ratio must be maintained at 1:20 for UG Engineering and 1:12 for PG", "HIGH", "AICTE APH Annexure-5 / Section 4 Norms", '{"field": "sfr_ratio", "max_ratio": 20.0}'),
                (4, "R004", "Faculty Cadre Ratio must be 1:2:6 (Professor : Associate Professor : Assistant Professor)", "MEDIUM", "AICTE APH Annexure-5 / Section 4 Norms", '{"field": "cadre_ratio", "cadre": "1:2:6"}'),
                (5, "R005", "Land documents must be registered in the name of the applicant Trust/Society", "HIGH", "AICTE APH Section 3.2 / Clause 2.2.3", '{"field": "land_registered_trust", "operator": "equals_true"}'),
                (6, "R006", "Statutory Anti-Ragging Affidavit executed within current academic year (Regulation 1 July 2009)", "MEDIUM", "AICTE Regulation 2009 & Chapter-VI", '{"field": "affidavit_validity", "max_age_months": 12}'),
                (7, "R007", "Essential Computing Terminals ratio must be at least 1 computer per 4 students enrolled", "LOW", "AICTE APH Appendix 5", '{"field": "computer_ratio", "min_ratio": 0.25}'),
                (8, "R008", "Structural stability certificate must be valid and verified by licensed structural engineer", "MEDIUM", "AICTE APH Section 3.3 (Clause 7.17)", '{"field": "structural_stability", "valid": true}'),
                (9, "R009", "Shared premises violation: No other institution or programme permitted on same building/land", "HIGH", "AICTE APH Section 3.1 & Section 8", '{"field": "shared_premises", "allowed": false}'),
                (10, "R010", "Three-Year Extended EoA eligibility: Top 100 NIRF or >=30% NBA accredited + 80% enrolment", "LOW", "AICTE APH Section 11 / Chapter II", '{"field": "three_year_eligibility", "operator": "check_criteria"}')
            ]
            for r in detailed_rules:
                cursor.execute("""
                    INSERT INTO rules (id, code, description, severity, handbook_ref, expression, version, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 1, 'APPROVED')
                    ON DUPLICATE KEY UPDATE description=VALUES(description), severity=VALUES(severity), handbook_ref=VALUES(handbook_ref)
                """, r)

            # 4. Ingest All 17 Pages of Reference Document into Handbook Chunks for Officer Copilot RAG
            cursor.execute("TRUNCATE TABLE handbook_chunks")
            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                cursor.execute("""
                    INSERT INTO handbook_chunks (source_doc, clause_ref, title, text, vector_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    "AICTE Approval Requirements Reference (APH 2024-27)",
                    f"Page {page_idx + 1}",
                    f"APH 2024-27 Section Page {page_idx + 1}",
                    page_text.strip(),
                    f"aph_p_{page_idx + 1}"
                ))

    print("[SUCCESS] Fully ingested all 12 categories, 21 master checklist items, 10 statutory rules, and 17 reference handbook pages into MySQL!")

if __name__ == "__main__":
    ingest_aph_reference_doc()
