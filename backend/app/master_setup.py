import os
import hashlib
from datetime import datetime
from app.database import get_db

def ensure_master_setup():
    """
    Sets up master categories, required document checklists, versioned AICTE rules,
    and simulated verification authority gateways.
    No dummy institutions, no dummy applications, no dummy documents.
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 1. Verification Authority Gateways
            sources = [
                ("State Fire Services Portal", "API", "https://fire.gov.in/api/v2/verify_noc", 1, 1),
                ("State Technical University Affiliation Board", "API", "https://stu.ac.in/api/affiliation/verify", 1, 1),
                ("National Board of Accreditation (NBA)", "API", "https://nba-india.org/api/accreditation/status", 1, 1),
                ("National DigiLocker Verification Gateway", "GATEWAY", "https://digilocker.gov.in/api/v1/verify_doc", 1, 1)
            ]
            for s in sources:
                cursor.execute("""
                    INSERT IGNORE INTO verification_sources (name, type, endpoint, is_simulated, is_active, status)
                    VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
                """, s)

            # 2. Application Categories
            categories = [
                (1, "EOA_CONT", "Continuation of Approval (EoA)", "AICTE APH 2024-27 Chapter 2"),
                (2, "NEW_PROG", "Introduction of New Technical Course / Division", "AICTE APH 2024-27 Chapter 1"),
                (3, "INTAKE_INC", "Increase in Approved Student Intake", "AICTE APH 2024-27 Clause 1.3")
            ]
            for c in categories:
                cursor.execute("""
                    INSERT INTO application_categories (id, code, name, handbook_ref)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name), handbook_ref=VALUES(handbook_ref)
                """, c)

            # 3. Checklists for EoA
            cursor.execute("INSERT IGNORE INTO checklists (id, category_id, version, is_active) VALUES (1, 1, 1, 1)")
            
            checklist_items = [
                (1, 1, "fire_noc", "Fire and Life Safety Certificate (NOC)", 1, 12),
                (2, 1, "land_document", "Registered Land Sale/Lease Deed & Title Ownership", 1, 0),
                (3, 1, "building_safety", "Structural Building Safety / Stability Certificate", 1, 36),
                (4, 1, "affidavit", "Anti-Ragging Undertaking & Non-Commercial Affidavit", 1, 12),
                (5, 1, "occupancy_cert", "Municipal Occupancy / Completion Certificate", 1, 0)
            ]
            for item in checklist_items:
                cursor.execute("""
                    INSERT INTO checklist_items (id, checklist_id, doc_type, title, required, validity_months)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE title=VALUES(title), required=VALUES(required)
                """, item)

            # 4. Versioned Regulatory Rules
            rules = [
                (1, "R001", "Fire Safety NOC must be valid and non-expired on application date", "HIGH", "AICTE APH 2024-27 Clause 2.4.1", '{"field": "fire_noc_expiry", "operator": "gte_today"}'),
                (2, "R002", "Applied student intake must not exceed sanctioned ceiling without NBA accreditation", "HIGH", "AICTE APH Clause 1.3.2", '{"field": "applied_intake", "operator": "lte_sanctioned"}'),
                (3, "R003", "Student to Faculty Ratio (SFR) must comply with AICTE norms (<= 1:15 for UG Engineering)", "HIGH", "AICTE APH Appendix 7", '{"field": "sfr_ratio", "max_ratio": 15.0}'),
                (4, "R004", "Registered Land Deed must be strictly in name of the applicant Trust/Society", "MEDIUM", "AICTE APH Clause 2.2.3", '{"field": "land_registered_trust", "operator": "equals_true"}'),
                (5, "R005", "Anti-Ragging Affidavit executed within current academic approval cycle (12 months)", "MEDIUM", "AICTE Regulation 2009", '{"field": "affidavit_validity", "max_age_months": 12}'),
                (6, "R006", "Computer Terminal Ratio must be at least 1 computer per 4 students enrolled", "LOW", "AICTE APH Appendix 5", '{"field": "computer_ratio", "min_ratio": 0.25}')
            ]
            for r in rules:
                cursor.execute("""
                    INSERT INTO rules (id, code, description, severity, handbook_ref, expression, version, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 1, 'APPROVED')
                    ON DUPLICATE KEY UPDATE description=VALUES(description), severity=VALUES(severity)
                """, r)

            # 5. Default Officer Admin account if not existing
            pwd_hash = hashlib.sha256("sanjit25".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (id, name, email, password_hash, role, institution_id, is_active)
                VALUES (1, 'Central Scrutiny Officer', 'officer@aicte.gov.in', %s, 'SCRUTINY_OFFICER', NULL, 1)
                ON DUPLICATE KEY UPDATE password_hash=VALUES(password_hash)
            """, (pwd_hash,))
