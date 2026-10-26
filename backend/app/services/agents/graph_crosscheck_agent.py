from app.database import fetch_all, fetch_one

class GraphCrossCheckAgent:
    """
    Graph Cross-Check Agent: Cross-examines all colleges in the database to detect
    shared ghost faculty, recycled certificates, and duplicate land title deeds.
    """
    def __init__(self):
        self.name = "Cross-Institution Graph Check Agent"

    def check_document_duplicates(self, doc_sha256: str, current_doc_id: int, current_inst_id: int) -> list[dict]:
        anomalies = []
        query = """
            SELECT d.id, d.original_filename, i.name as institution_name, i.aicte_id
            FROM documents d
            JOIN applications a ON d.application_id = a.id
            JOIN institutions i ON a.institution_id = i.id
            WHERE d.sha256 = %s AND d.id != %s AND a.institution_id != %s
        """
        duplicates = fetch_all(query, (doc_sha256, current_doc_id, current_inst_id))
        for dup in duplicates:
            anomalies.append({
                "type": "DUPLICATE_DOCUMENT",
                "severity": "HIGH",
                "title": "Recycled Certificate Detected Across Multiple Institutions",
                "reason": f"Exact binary SHA-256 match found with certificate '{dup['original_filename']}' previously uploaded by '{dup['institution_name']}' ({dup['aicte_id']}). Potential document recycling.",
                "confidence": 0.99,
                "evidence_snippet": f"Matching Institution: {dup['institution_name']} ({dup['aicte_id']}) | SHA-256: {doc_sha256}"
            })
        return anomalies

    def check_shared_faculty(self, current_inst_id: int) -> list[dict]:
        anomalies = []
        query = """
            SELECT f1.faculty_uid, f1.name as faculty_name, f1.pan_masked,
                   i1.name as inst1_name, i2.name as inst2_name, i2.aicte_id as inst2_code,
                   f1.designation as desig1, f2.designation as desig2
            FROM faculty_registry f1
            JOIN institutions i1 ON f1.institution_id = i1.id
            JOIN faculty_registry f2 ON f1.faculty_uid = f2.faculty_uid AND f1.id < f2.id
            JOIN institutions i2 ON f2.institution_id = i2.id
            WHERE f1.institution_id = %s OR f2.institution_id = %s
        """
        shared = fetch_all(query, (current_inst_id, current_inst_id))
        for s in shared:
            anomalies.append({
                "type": "SHARED_FACULTY",
                "severity": "HIGH",
                "title": f"Concurrent Dual Employment: {s['faculty_name']}",
                "reason": f"Faculty '{s['faculty_name']}' (PAN {s['pan_masked']}) is concurrently registered as full-time at both '{s['inst1_name']}' and '{s['inst2_name']}'. Direct violation of AICTE Approval Handbook Annexure-5.",
                "confidence": 0.99,
                "evidence_snippet": f"Faculty: {s['faculty_name']} | Dual Colleges: {s['inst1_name']} & {s['inst2_name']}"
            })
        return anomalies

graph_crosscheck_agent = GraphCrossCheckAgent()
