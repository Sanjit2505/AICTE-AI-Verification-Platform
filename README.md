# AICTE Trust Layer - Real-Time AI Document Verification & Tamper-Evident Audit Platform

AI-assisted pre-scrutiny, document verification, and tamper-evident audit platform for AICTE approval processing.

## Key Features

1. **Dual Role Access Control**:
   - **College / Institution Portal**: Real-time institution registration, submission of operational parameters, one-by-one PDF document uploads, and live AI Pre-Scrutiny Readiness Score.
   - **AICTE Administration Portal**: Risk-ranked Central Scrutiny Queue, split-screen PDF document inspection, OCR & parsed data extraction, and human-in-the-loop statutory approval/rejection decision gate with mandatory justification.
2. **Real Document Ingestion & Parsing**:
   - Page-by-page extraction using `pdfplumber` and `pypdf`.
   - Automated detection of validity dates, reference numbers, issuing authorities, land area metrics, and tables.
   - Forensic metadata inspection for editing software tampering.
3. **Deterministic Versioned Rules Engine**:
   - Evaluates mandatory clearances (Fire Safety NOC, Land Deeds, Anti-Ragging Undertakings, Student-to-Faculty Ratios, and Computer Terminal requirements) against AICTE Approval Process Handbook (APH 2024-2027) norms.
4. **Trust Ledger (Append-Only Hash Chain)**:
   - Every registration, update, file upload, and officer decision is cryptographically chained with SHA-256 (`entry_hash = SHA256(prev_hash + actor + action + payload_hash + timestamp)`).
   - Live on-demand integrity verification against database mutations.
5. **AICTE Handbook Copilot (RAG)**:
   - Interactive assistant providing grounded answers with specific handbook clause citations.

---

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, PyMySQL, pdfplumber, pypdf, reportlab, Pillow, cryptography
- **Database**: MySQL 8.0+ (InnoDB, UTF8mb4, Cryptographic SHA-256 Chaining)
- **Frontend**: Vanilla HTML5, Modern CSS Design System (Glassmorphism, Dark Mode), Vanilla JavaScript
- **API Architecture**: RESTful endpoints with CORS and static file mounting

---

## Database Configuration & MySQL Workbench

1. Ensure MySQL 8.0 is running on `127.0.0.1:3306`.
2. Connect with MySQL Workbench:
   - **Hostname**: `127.0.0.1`
   - **Port**: `3306`
   - **Username**: `root`
   - **Database**: `aicte_trust_layer`
3. Database schema: `backend/app/schema.sql`

---

## Running the Application

### 1. Install Dependencies
```bash
pip install fastapi uvicorn pymysql pdfplumber pypdf reportlab pyyaml rapidfuzz pillow cryptography requests
```

### 2. Start the Backend Server
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Access the Platform
- Web Application: `http://127.0.0.1:8000`
- API Documentation (Swagger): `http://127.0.0.1:8000/docs`
