from app.services.document_classifier import classifier
from app.services.agents.forensic_agent import forensic_agent
from app.services.agents.regulatory_agent import regulatory_agent
from app.services.agents.graph_crosscheck_agent import graph_crosscheck_agent
from app.services.rules_engine import calculate_readiness_score, calculate_risk_score
from app.services.trust_ledger import record_audit
from app.database import execute, fetch_all

class MultiAgentScrutinyOrchestrator:
    """
    Coordinates specialized AI agents for holistic document scrutiny:
    1. Document Type Classifier
    2. Forensic & Metadata Agent
    3. Regulatory Compliance Agent
    4. Cross-Institution Graph Check Agent
    """
    def __init__(self):
        self.classifier = classifier
        self.forensic_agent = forensic_agent
        self.regulatory_agent = regulatory_agent
        self.graph_agent = graph_crosscheck_agent

    def scrutinize_upload(
        self,
        application_id: int,
        document_id: int,
        institution_id: int,
        institution_name: str,
        doc_type: str,
        file_path: str,
        file_sha256: str,
        extracted_data: dict,
        form_data: dict
    ) -> dict:
        raw_text = extracted_data.get("raw_text", "")
        metadata = extracted_data.get("metadata", {})
        extractions = extracted_data.get("extractions", {})
        artifact_base = f"doc_{document_id}_{file_sha256[:8]}"

        all_findings = []

        # 1. AI Document Classification Agent
        cls_result = self.classifier.classify(raw_text, doc_type)
        if cls_result.get("category_anomaly"):
            f_id = execute("""
                INSERT INTO findings (application_id, document_id, source_type, severity, title, reason, confidence, status, created_at)
                VALUES (%s, %s, 'ANOMALY', 'HIGH', %s, %s, %s, 'OPEN', NOW())
            """, (
                application_id, document_id,
                f"Document Type Mismatch: Appears to be {cls_result['predicted_category']}",
                f"Uploaded as '{doc_type}', but natural language classification identifies this document as '{cls_result['predicted_category']}' with {int(cls_result['confidence']*100)}% confidence.",
                cls_result["confidence"]
            ))
            all_findings.append("Category Mismatch")

        # 2. Forensic & Metadata Agent
        meta_anomalies = self.forensic_agent.analyze_metadata(metadata)
        for ma in meta_anomalies:
            f_id = execute("""
                INSERT INTO findings (application_id, document_id, source_type, severity, title, reason, confidence, status, created_at)
                VALUES (%s, %s, 'ANOMALY', %s, %s, %s, %s, 'OPEN', NOW())
            """, (application_id, document_id, ma["severity"], ma["title"], ma["reason"], ma["confidence"]))
            execute("""
                INSERT INTO evidence (finding_id, kind, document_id, page_no, snippet)
                VALUES (%s, 'METADATA', %s, 1, %s)
            """, (f_id, document_id, ma.get("evidence_snippet", "Metadata inspection")))
            all_findings.append(ma["title"])

        # ELA Heatmap
        ela_result = self.forensic_agent.generate_ela_heatmap(file_path, artifact_base)
        if ela_result.get("is_spliced"):
            f_id = execute("""
                INSERT INTO findings (application_id, document_id, source_type, severity, title, reason, confidence, status, created_at)
                VALUES (%s, %s, 'ANOMALY', 'HIGH', 'Error Level Analysis (ELA) Compression Inconsistency', 'Pixel-level compression discrepancy indicates potential image splicing or pasted elements.', %s, 'OPEN', NOW())
            """, (application_id, document_id, ela_result["score"]))
            execute("""
                INSERT INTO evidence (finding_id, kind, document_id, page_no, artifact_key)
                VALUES (%s, 'HEATMAP', %s, 1, %s)
            """, (f_id, document_id, ela_result["artifact_key"]))
            all_findings.append("ELA Compression Inconsistency")

        # Date Chronology
        date_flags = self.forensic_agent.check_dates(extractions.get("issue_date"), extractions.get("expiry_date"))
        for df in date_flags:
            execute("""
                INSERT INTO findings (application_id, document_id, source_type, severity, title, reason, confidence, status, created_at)
                VALUES (%s, %s, 'RULE', %s, %s, %s, %s, 'OPEN', NOW())
            """, (application_id, document_id, df["severity"], df["title"], df["reason"], df["confidence"]))
            all_findings.append(df["title"])

        # 3. Regulatory Compliance Agent (AICTE APH 2024-2027)
        reg_flags = self.regulatory_agent.evaluate_compliance(form_data, extractions)
        for rf in reg_flags:
            f_id = execute("""
                INSERT INTO findings (application_id, document_id, source_type, severity, title, reason, confidence, status, created_at)
                VALUES (%s, %s, 'RULE', %s, %s, %s, %s, 'OPEN', NOW())
            """, (application_id, document_id, rf["severity"], rf["title"], rf["reason"], rf["confidence"]))
            if rf.get("evidence_snippet"):
                execute("""
                    INSERT INTO evidence (finding_id, kind, document_id, page_no, snippet)
                    VALUES (%s, 'RECORD', %s, 1, %s)
                """, (f_id, document_id, rf["evidence_snippet"]))
            all_findings.append(rf["title"])

        # 4. Cross-Institution Graph Check Agent
        dup_flags = self.graph_agent.check_document_duplicates(file_sha256, document_id, institution_id)
        for df in dup_flags:
            execute("""
                INSERT INTO findings (application_id, document_id, source_type, severity, title, reason, confidence, status, created_at)
                VALUES (%s, %s, 'GRAPH', %s, %s, %s, %s, 'OPEN', NOW())
            """, (application_id, document_id, df["severity"], df["title"], df["reason"], df["confidence"]))
            all_findings.append(df["title"])

        # 5. Score Synthesizer
        db_findings = fetch_all("SELECT severity FROM findings WHERE application_id = %s", (application_id,))
        uploaded_doc_types = fetch_all("SELECT DISTINCT doc_type FROM documents WHERE application_id = %s", (application_id,))
        readiness = calculate_readiness_score(db_findings, 5, len(uploaded_doc_types))
        risk = calculate_risk_score(db_findings)

        execute("""
            UPDATE applications 
            SET readiness_score = %s, risk_score = %s, status = 'SUBMITTED', submitted_at = NOW()
            WHERE id = %s
        """, (readiness, risk, application_id))

        # 6. Record in Trust Ledger
        audit_entry = record_audit(
            actor=institution_name,
            action="MULTI_AGENT_DOCUMENT_SCRUTINY",
            entity_type="DOCUMENT",
            entity_id=document_id,
            payload={
                "doc_type": doc_type,
                "sha256": file_sha256,
                "classifier_predicted": cls_result.get("predicted_category"),
                "flags_raised": len(all_findings),
                "readiness_score": readiness,
                "risk_score": risk
            }
        )

        return {
            "readiness_score": readiness,
            "risk_score": risk,
            "classification": cls_result,
            "findings_count": len(all_findings),
            "findings": all_findings,
            "audit_receipt": audit_entry
        }

orchestrator = MultiAgentScrutinyOrchestrator()
