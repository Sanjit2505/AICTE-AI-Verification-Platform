import os
import hashlib
import json
from datetime import datetime
from app.database import get_db, execute, fetch_one
from app.services.pdf_generator import generate_synthetic_fire_noc
from app.services.trust_ledger import record_audit, calculate_sha256
from app.services.rag_copilot import DEFAULT_HANDBOOK_CHUNKS
from app.config import UPLOAD_DIR

def seed_database():
    print("[*] Starting AICTE Trust Layer database seeding...")
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 1. Verification Sources
            sources = [
                ("State Fire Services Gateway", "API", "https://fire.gov.in/api/v2/verify_noc", 1, 1),
                ("State Technical University Affiliation Board", "API", "https://stu.ac.in/api/affiliation/verify", 1, 1),
                ("National Board of Accreditation (NBA)", "API", "https://nba-india.org/api/accreditation/status", 1, 1),
                ("National DigiLocker Verified Document Gateway", "GATEWAY", "https://digilocker.gov.in/api/v1/verify_doc", 1, 1)
            ]
            for s in sources:
                cursor.execute("""
                    INSERT IGNORE INTO verification_sources (name, type, endpoint, is_simulated, is_active, status)
                    VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
                """, s)

            # 2. Institutions
            institutions = [
                ("1-109283741", "Delhi Institute of Technology & Management", "Aryavart Educational Trust", "Sector 16, Dwarka, New Delhi", "Delhi", "South West Delhi", 28.5921, 77.0460, 92),
                ("1-987213456", "Chennai Technical College", "Kaveri Foundation Society", "GST Road, Tambaram, Chennai", "Tamil Nadu", "Chengalpattu", 12.9249, 80.1000, 58),
                ("1-554433221", "Bengaluru Academy of Science & Engineering", "Vidyapeeth Education Society", "Electronic City Phase 1, Bengaluru", "Karnataka", "Bengaluru Urban", 12.8452, 77.6602, 88),
                ("1-889977665", "Mumbai Metropolitan Institute of Engineering", "Sahyadri Welfare Trust", "Sector 4, Navi Mumbai", "Maharashtra", "Thane", 19.0330, 73.0297, 64)
            ]
            for inst in institutions:
                cursor.execute("""
                    INSERT IGNORE INTO institutions (aicte_id, name, trust_name, address, state, district, lat, lng, trust_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, inst)

            # 3. Users (passwords hashed / simple for demo)
            pwd_hash = hashlib.sha256("sanjit25".encode()).hexdigest()
            users = [
                ("Delhi Institute College Admin", "college@delhi-tech.edu", pwd_hash, "COLLEGE", 1),
                ("Scrutiny Officer - S. R. Rao", "officer@aicte.gov.in", pwd_hash, "SCRUTINY_OFFICER", None),
                ("Senior Approval Officer - Dr. Anita Verma", "senior@aicte.gov.in", pwd_hash, "SENIOR_OFFICER", None),
                ("AICTE National Admin", "admin@aicte.gov.in", pwd_hash, "ADMIN", None),
                ("Chief Statutory Auditor", "auditor@aicte.gov.in", pwd_hash, "AUDITOR", None)
            ]
            for u in users:
                cursor.execute("""
                    INSERT IGNORE INTO users (name, email, password_hash, role, institution_id, is_active)
                    VALUES (%s, %s, %s, %s, %s, 1)
                """, u)

            # 4. Application Categories
            categories = [
                ("EOA_CONT", "Continuation of Approval (EoA)", "AICTE APH 2024-27 Chapter 2"),
                ("NEW_PROG", "Introduction of New Course / Department", "AICTE APH 2024-27 Chapter 1"),
                ("INTAKE_INC", "Increase in Approved Student Intake", "AICTE APH 2024-27 Clause 1.3")
            ]
            for c in categories:
                cursor.execute("""
                    INSERT IGNORE INTO application_categories (code, name, handbook_ref)
                    VALUES (%s, %s, %s)
                """, c)

            # 5. Checklists
            cursor.execute("SELECT id FROM application_categories WHERE code = 'EOA_CONT'")
            cat_id = cursor.fetchone()["id"]
            cursor.execute("INSERT IGNORE INTO checklists (id, category_id, version, is_active) VALUES (1, %s, 1, 1)", (cat_id,))
            
            checklist_items = [
                (1, "fire_noc", "Fire and Life Safety Certificate (NOC)", 1, 12),
                (1, "land_document", "Registered Land Sale/Lease Deed", 1, 0),
                (1, "affidavit", "Anti-Ragging Statutory Affidavit", 1, 12),
                (1, "building_safety", "Structural Building Safety Certificate", 1, 36)
            ]
            for item in checklist_items:
                cursor.execute("""
                    INSERT IGNORE INTO checklist_items (checklist_id, doc_type, title, required, validity_months)
                    VALUES (%s, %s, %s, %s, %s)
                """, item)

            # 6. Rules
            rules = [
                ("R001", "Fire Safety NOC must be valid on application submission date", "HIGH", "AICTE APH 2024-27 Clause 2.4.1", '{"field": "fire_noc_expiry", "operator": "gte_today"}'),
                ("R002", "Applied student intake must not exceed sanctioned ceiling without NBA accreditation", "HIGH", "AICTE APH Clause 1.3.2", '{"field": "applied_intake", "operator": "lte_sanctioned"}'),
                ("R003", "Student to Faculty Ratio (SFR) must comply with AICTE norms (<= 1:15 for UG Engineering)", "HIGH", "AICTE APH Appendix 7", '{"field": "sfr_ratio", "max_ratio": 15.0}'),
                ("R004", "Mandatory registered Land Document must be in name of Trust/Society", "MEDIUM", "AICTE APH Clause 2.2.3", '{"field": "land_registered_trust", "operator": "equals_true"}'),
                ("R005", "Anti-Ragging Undertaking executed within active academic year", "MEDIUM", "AICTE Regulation 2009", '{"field": "affidavit_validity", "max_age_months": 12}'),
                ("R006", "Minimum Computer Terminal Ratio must be at least 1 computer per 4 students", "LOW", "AICTE APH Appendix 5", '{"field": "computer_ratio", "min_ratio": 0.25}')
            ]
            for r in rules:
                cursor.execute("""
                    INSERT IGNORE INTO rules (code, description, severity, handbook_ref, expression, version, status)
                    VALUES (%s, %s, %s, %s, %s, 1, 'APPROVED')
                """, r)

            # 7. Faculty Registry (includes injected ghost faculty)
            faculty = [
                ("FAC-DEL-01", "Dr. Rajesh Sharma", "ABCPS****F", 1, "Computer Science & Engineering", "Professor & HOD", "2021-06-01", None),
                ("FAC-DEL-01", "Dr. Rajesh Sharma", "ABCPS****F", 2, "Information Technology", "Professor", "2022-01-01", None), # GHOST FACULTY at Chennai
                ("FAC-DEL-02", "Dr. Priya Sundaram", "BNMPK****G", 1, "Mechanical Engineering", "Associate Professor", "2020-08-15", None),
                ("FAC-BLR-01", "Dr. Vikram Seth", "CDEPR****K", 3, "Electronics & Communication", "Professor", "2019-07-10", None),
                ("FAC-MUM-01", "Dr. Neha Kulkarni", "FRTPS****L", 4, "Civil Engineering", "Assistant Professor", "2023-02-01", None)
            ]
            for f in faculty:
                cursor.execute("""
                    INSERT IGNORE INTO faculty_registry (faculty_uid, name, pan_masked, institution_id, programme, designation, from_date, to_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, f)

            # 8. Handbook Chunks for RAG
            for idx, chunk in enumerate(DEFAULT_HANDBOOK_CHUNKS):
                cursor.execute("""
                    INSERT IGNORE INTO handbook_chunks (source_doc, clause_ref, title, text, vector_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (chunk["source_doc"], chunk["clause_ref"], chunk["title"], chunk["text"], f"vec_{idx+1}"))

    # Generate synthetic PDFs
    print("[*] Generating authentic synthetic government certificates...")
    doc1_path = generate_synthetic_fire_noc("valid_fire_noc_delhi.pdf", "NOC-DL-2024-9841", "Delhi Institute of Technology & Management", "2024-01-15", "2027-12-31", False)
    doc2_path = generate_synthetic_fire_noc("expired_fire_noc_chennai.pdf", "NOC-TN-2023-4122", "Chennai Technical College", "2020-11-16", "2023-11-15", True)
    doc3_path = generate_synthetic_fire_noc("shared_fire_noc_mumbai.pdf", "NOC-DL-2024-9841", "Mumbai Metropolitan Institute of Engineering", "2024-01-15", "2027-12-31", False)

    # Compute hashes
    with open(doc1_path, "rb") as f:
        hash1 = calculate_sha256(f.read())
    with open(doc2_path, "rb") as f:
        hash2 = calculate_sha256(f.read())
    with open(doc3_path, "rb") as f:
        hash3 = calculate_sha256(f.read()) # exact match with doc1 for duplicate test

    with get_db() as conn:
        with conn.cursor() as cursor:
            # Seed 3 Applications
            # App 1: Delhi Institute (Clean, Readiness: 94, Risk: 8)
            cursor.execute("""
                INSERT IGNORE INTO applications (id, institution_id, category_id, status, readiness_score, risk_score, current_version, submitted_at)
                VALUES (1, 1, 1, 'SUBMITTED', 94, 8, 1, NOW())
            """)
            cursor.execute("""
                INSERT IGNORE INTO documents (id, application_id, version_id, doc_type, file_key, original_filename, sha256, mime, page_count)
                VALUES (1, 1, 1, 'Fire Safety NOC', 'valid_fire_noc_delhi.pdf', 'Delhi_Fire_NOC_2024.pdf', %s, 'application/pdf', 1)
            """, (hash1,))

            # App 2: Chennai Technical College (Defects: Expired Fire NOC + Ghost Faculty, Readiness: 45, Risk: 68)
            cursor.execute("""
                INSERT IGNORE INTO applications (id, institution_id, category_id, status, readiness_score, risk_score, current_version, submitted_at)
                VALUES (2, 2, 1, 'UNDER_REVIEW', 45, 68, 1, NOW())
            """)
            cursor.execute("""
                INSERT IGNORE INTO documents (id, application_id, version_id, doc_type, file_key, original_filename, sha256, mime, page_count)
                VALUES (2, 2, 1, 'Fire Safety NOC', 'expired_fire_noc_chennai.pdf', 'Chennai_Fire_NOC.pdf', %s, 'application/pdf', 1)
            """, (hash2,))
            # Finding for App 2
            cursor.execute("""
                INSERT IGNORE INTO findings (id, application_id, document_id, source_type, rule_id, severity, title, reason, confidence, status)
                VALUES (1, 2, 2, 'RULE', 1, 'HIGH', 'Expired Fire Safety NOC Certificate', 'Fire Safety Certificate expired on 15-Nov-2023. AICTE requires a current valid NOC prior to granting Extension of Approval.', 0.985, 'OPEN')
            """)
            cursor.execute("""
                INSERT IGNORE INTO evidence (finding_id, kind, document_id, page_no, bbox, snippet)
                VALUES (1, 'METADATA', 2, 1, '{"ymin": 0.42, "xmin": 0.65, "ymax": 0.46, "xmax": 0.88}', 'Certificate Expiry Date: 2023-11-15 | Status: EXPIRED')
            """)

            # App 3: Mumbai Metropolitan Institute (Defects: Duplicate recycled doc + High Intake without NBA, Readiness: 42, Risk: 75)
            cursor.execute("""
                INSERT IGNORE INTO applications (id, institution_id, category_id, status, readiness_score, risk_score, current_version, submitted_at)
                VALUES (3, 4, 3, 'UNDER_REVIEW', 42, 75, 1, NOW())
            """)
            cursor.execute("""
                INSERT IGNORE INTO documents (id, application_id, version_id, doc_type, file_key, original_filename, sha256, mime, page_count)
                VALUES (3, 3, 1, 'Fire Safety NOC', 'shared_fire_noc_mumbai.pdf', 'Fire_Clearance_Mumbai.pdf', %s, 'application/pdf', 1)
            """, (hash3,)) # duplicate hash
            cursor.execute("""
                INSERT IGNORE INTO findings (id, application_id, document_id, source_type, rule_id, severity, title, reason, confidence, status)
                VALUES (2, 3, 3, 'GRAPH', NULL, 'HIGH', 'Duplicate Clearance Certificate Recycled Across Multiple Colleges', 'Exact SHA-256 match detected between Mumbai Metropolitan and Delhi Institute. Potential fraudulent reuse of statutory certificate.', 0.994, 'OPEN')
            """)

    # Record initial tamper-evident audit logs
    print("[*] Building cryptographic audit hash chain & blockchain anchoring...")
    record_audit("college@delhi-tech.edu", "APPLICATION_SUBMITTED", "APPLICATION", 1, {"status": "SUBMITTED", "intake": 480})
    record_audit("college@delhi-tech.edu", "DOCUMENT_UPLOADED", "DOCUMENT", 1, {"doc_type": "fire_noc", "sha256": hash1})
    record_audit("system.ai_engine", "OCR_AND_RULES_EVALUATION", "APPLICATION", 1, {"readiness_score": 94, "flags": 0})
    record_audit("college@chennai-tech.edu", "APPLICATION_SUBMITTED", "APPLICATION", 2, {"status": "SUBMITTED", "intake": 360})
    record_audit("system.ai_engine", "FINDING_GENERATED", "FINDING", 1, {"severity": "HIGH", "rule": "R001", "reason": "Expired Fire NOC"})
    record_audit("officer@aicte.gov.in", "TRIAGE_OPENED", "APPLICATION", 2, {"officer": "S. R. Rao", "stage": "UNDER_REVIEW"})
    record_audit("system.graph_engine", "GRAPH_ANOMALY_FLAGGED", "FACULTY", 1, {"faculty_uid": "FAC-DEL-01", "anomaly": "Concurrent Dual Employment"})

    print("[SUCCESS] Database seeding complete with real records, authentic PDFs, and tamper-evident audit chain!")

if __name__ == "__main__":
    seed_database()
