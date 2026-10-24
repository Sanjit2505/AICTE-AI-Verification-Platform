-- AICTE Trust Layer Database Schema (MySQL 8.0+)
-- Designed for tamper-evident audit, real-time AI scrutiny, and verification adapters.

USE aicte_trust_layer;

-- 1. Users and RBAC
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('COLLEGE', 'SCRUTINY_OFFICER', 'SENIOR_OFFICER', 'ADMIN', 'AUDITOR') NOT NULL,
    institution_id BIGINT UNSIGNED NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Institutions
CREATE TABLE IF NOT EXISTS institutions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    aicte_id VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    trust_name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    lat DECIMAL(9, 6) DEFAULT 28.6139,
    lng DECIMAL(9, 6) DEFAULT 77.2090,
    trust_score INT DEFAULT 88,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Application Categories
CREATE TABLE IF NOT EXISTS application_categories (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    handbook_ref VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Applications
CREATE TABLE IF NOT EXISTS applications (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    institution_id BIGINT UNSIGNED NOT NULL,
    category_id BIGINT UNSIGNED NOT NULL,
    status ENUM('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'EVIDENCE_REQUESTED', 'ESCALATED', 'DECIDED') DEFAULT 'DRAFT',
    decision ENUM('PENDING', 'APPROVED', 'REJECTED') DEFAULT 'PENDING',
    decision_reason TEXT NULL,
    decided_by VARCHAR(255) NULL,
    readiness_score TINYINT DEFAULT 0,
    risk_score TINYINT DEFAULT 0,
    current_version INT DEFAULT 1,
    submitted_at DATETIME(6) NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES application_categories(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Application Versions
CREATE TABLE IF NOT EXISTS application_versions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    application_id BIGINT UNSIGNED NOT NULL,
    version_no INT NOT NULL,
    form_data JSON NOT NULL,
    submission_hash CHAR(64) NOT NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Documents
CREATE TABLE IF NOT EXISTS documents (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    application_id BIGINT UNSIGNED NOT NULL,
    version_id BIGINT UNSIGNED NULL,
    doc_type VARCHAR(100) NOT NULL,
    file_key VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    sha256 CHAR(64) NOT NULL,
    mime VARCHAR(100) DEFAULT 'application/pdf',
    page_count INT DEFAULT 1,
    uploaded_by BIGINT UNSIGNED NULL,
    uploaded_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Extractions
CREATE TABLE IF NOT EXISTS extractions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_id BIGINT UNSIGNED NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    confidence DECIMAL(4, 3) DEFAULT 0.950,
    page_no INT DEFAULT 1,
    bbox JSON NULL,
    method ENUM('ocr', 'llm', 'regex') DEFAULT 'ocr',
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Checklists & Items
CREATE TABLE IF NOT EXISTS checklists (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    category_id BIGINT UNSIGNED NOT NULL,
    version INT DEFAULT 1,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES application_categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS checklist_items (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    checklist_id BIGINT UNSIGNED NOT NULL,
    doc_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    required TINYINT(1) DEFAULT 1,
    validity_months INT DEFAULT 12,
    FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Rules (Configurable & Versioned)
CREATE TABLE IF NOT EXISTS rules (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(64) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL,
    handbook_ref VARCHAR(255) NOT NULL,
    expression JSON NOT NULL,
    version INT DEFAULT 1,
    status ENUM('DRAFT', 'APPROVED', 'RETIRED') DEFAULT 'APPROVED',
    approved_by VARCHAR(255) DEFAULT 'System Admin',
    effective_from DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Findings
CREATE TABLE IF NOT EXISTS findings (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    application_id BIGINT UNSIGNED NOT NULL,
    document_id BIGINT UNSIGNED NULL,
    source_type ENUM('RULE', 'ANOMALY', 'VERIFICATION', 'GRAPH', 'INFRA') NOT NULL,
    rule_id BIGINT UNSIGNED NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL,
    title VARCHAR(255) NOT NULL,
    reason TEXT NOT NULL,
    confidence DECIMAL(4, 3) DEFAULT 0.920,
    status ENUM('OPEN', 'ACCEPTED', 'DISMISSED', 'ESCALATED') DEFAULT 'OPEN',
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Evidence
CREATE TABLE IF NOT EXISTS evidence (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    finding_id BIGINT UNSIGNED NOT NULL,
    kind ENUM('CROP', 'HEATMAP', 'RECORD', 'METADATA') NOT NULL,
    document_id BIGINT UNSIGNED NULL,
    page_no INT DEFAULT 1,
    bbox JSON NULL,
    record_ref VARCHAR(255) NULL,
    snippet TEXT NULL,
    artifact_key VARCHAR(255) NULL,
    FOREIGN KEY (finding_id) REFERENCES findings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Officer Actions
CREATE TABLE IF NOT EXISTS officer_actions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    finding_id BIGINT UNSIGNED NOT NULL,
    officer_id BIGINT UNSIGNED NOT NULL,
    officer_name VARCHAR(255) NOT NULL,
    action ENUM('ACCEPT', 'DISMISS', 'ESCALATE') NOT NULL,
    reason TEXT NOT NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (finding_id) REFERENCES findings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Verification Sources & Verifications
CREATE TABLE IF NOT EXISTS verification_sources (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    is_simulated TINYINT(1) DEFAULT 1,
    is_active TINYINT(1) DEFAULT 1,
    status VARCHAR(50) DEFAULT 'ACTIVE'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS verifications (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_id BIGINT UNSIGNED NOT NULL,
    source_id BIGINT UNSIGNED NOT NULL,
    status ENUM('VERIFIED', 'MISMATCH_DETECTED', 'EXPIRED', 'VERIFICATION_PENDING', 'SOURCE_UNAVAILABLE', 'MANUAL_REVIEW_REQUIRED') NOT NULL,
    request_ref VARCHAR(255) NOT NULL,
    response_hash CHAR(64) NOT NULL,
    response_summary JSON NOT NULL,
    checked_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES verification_sources(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. Fingerprints (Cross-Institution Duplicate Detection)
CREATE TABLE IF NOT EXISTS fingerprints (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_id BIGINT UNSIGNED NOT NULL,
    phash CHAR(16) NOT NULL,
    text_simhash BIGINT UNSIGNED NOT NULL,
    normalized_id VARCHAR(128) NOT NULL,
    INDEX idx_phash (phash),
    INDEX idx_normalized_id (normalized_id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 15. Faculty Registry (Ghost / Shared Faculty Detection)
CREATE TABLE IF NOT EXISTS faculty_registry (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    faculty_uid VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    pan_masked VARCHAR(32) NOT NULL,
    institution_id BIGINT UNSIGNED NOT NULL,
    programme VARCHAR(100) NOT NULL,
    designation VARCHAR(100) NOT NULL,
    from_date DATE NOT NULL,
    to_date DATE NULL,
    INDEX idx_faculty_uid (faculty_uid),
    FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 16. Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    application_id BIGINT UNSIGNED NOT NULL,
    type VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    to_user_id BIGINT UNSIGNED NULL,
    is_read TINYINT(1) DEFAULT 0,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 17. Audit Log (Append-Only Hash Chain)
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    seq BIGINT NOT NULL UNIQUE,
    actor VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id BIGINT UNSIGNED NOT NULL,
    payload_hash CHAR(64) NOT NULL,
    prev_hash CHAR(64) NOT NULL,
    entry_hash CHAR(64) NOT NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 18. Anchors (Merkle Root Batch On-Chain Anchors)
CREATE TABLE IF NOT EXISTS anchors (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    from_seq BIGINT NOT NULL,
    to_seq BIGINT NOT NULL,
    merkle_root CHAR(64) NOT NULL,
    tx_hash VARCHAR(128) NOT NULL,
    chain VARCHAR(64) DEFAULT 'Polygon Amoy Testnet (Simulated)',
    anchored_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 19. Handbook Chunks (AICTE Handbook RAG Knowledge Base)
CREATE TABLE IF NOT EXISTS handbook_chunks (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source_doc VARCHAR(255) NOT NULL,
    clause_ref VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    text MEDIUMTEXT NOT NULL,
    vector_id VARCHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
