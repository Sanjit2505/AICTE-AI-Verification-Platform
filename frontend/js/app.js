// Real-Time AICTE Trust Layer Frontend Controller
const API_BASE = window.location.origin;

// State Management
let currentUser = null;
let currentActiveApp = null;
let selectedOfficerApp = null;

document.addEventListener("DOMContentLoaded", () => {
  initAuthEvents();
  initCollegePortalEvents();
  initOfficerPortalEvents();
  initLedgerEvents();
  initCopilotEvents();

  // Check session storage
  const savedUser = sessionStorage.getItem("aicte_user");
  if (savedUser) {
    currentUser = JSON.parse(savedUser);
    onUserLoggedIn();
  } else {
    showView("view-auth");
  }
});

// View Navigation Router
function showView(viewId) {
  document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));
  const target = document.getElementById(viewId);
  if (target) target.classList.add("active");

  document.querySelectorAll(".nav-tab-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.view === viewId);
  });
}

// ==================== AUTHENTICATION & ROLE MANAGEMENT ====================
function initAuthEvents() {
  // Toggle between College Login and Register
  document.getElementById("linkShowColRegister").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("collegeLoginBox").style.display = "none";
    document.getElementById("collegeRegisterBox").style.display = "block";
  });

  document.getElementById("linkBackToColLogin").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("collegeRegisterBox").style.display = "none";
    document.getElementById("collegeLoginBox").style.display = "block";
  });

  // College Register Form
  document.getElementById("formCollegeRegister").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById("regColName").value,
      aicte_id: document.getElementById("regAicteId").value,
      trust_name: document.getElementById("regTrustName").value,
      state: document.getElementById("regState").value,
      district: document.getElementById("regDistrict").value,
      address: document.getElementById("regAddress").value,
      email: document.getElementById("regEmail").value,
      password: document.getElementById("regPassword").value
    };

    try {
      const res = await fetch(`${API_BASE}/api/auth/register-college`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");

      alert("Institution registered successfully in MySQL! Please log in with your credentials.");
      document.getElementById("collegeRegisterBox").style.display = "none";
      document.getElementById("collegeLoginBox").style.display = "block";
      document.getElementById("colLoginEmail").value = payload.email;
    } catch (err) {
      alert("Registration Error: " + err.message);
    }
  });

  // College Login Form
  document.getElementById("formCollegeLogin").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("colLoginEmail").value;
    const password = document.getElementById("colLoginPass").value;
    await performLogin(email, password, "COLLEGE");
  });

  // Officer Login Form
  document.getElementById("formOfficerLogin").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("officerLoginEmail").value;
    const password = document.getElementById("officerLoginPass").value;
    await performLogin(email, password, "OFFICER");
  });

  // Logout
  document.getElementById("btnLogout").addEventListener("click", () => {
    sessionStorage.removeItem("aicte_user");
    currentUser = null;
    document.getElementById("userProfileBadge").style.display = "none";
    document.getElementById("appNavTabsContainer").style.display = "none";
    showView("view-auth");
  });
}

async function performLogin(email, password, roleType) {
  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role_type: roleType })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Invalid credentials");

    currentUser = data.user;
    sessionStorage.setItem("aicte_user", JSON.stringify(currentUser));
    onUserLoggedIn();
  } catch (err) {
    alert("Login Error: " + err.message);
  }
}

function onUserLoggedIn() {
  document.getElementById("userProfileBadge").style.display = "flex";
  document.getElementById("headerUserName").innerText = currentUser.name;
  document.getElementById("headerUserRole").innerText = currentUser.role;

  const navContainer = document.getElementById("appNavTabsContainer");
  const navTabs = document.getElementById("appNavTabs");
  navContainer.style.display = "block";

  if (currentUser.role === "COLLEGE") {
    // College Tabs
    navTabs.innerHTML = `
      <button class="nav-tab-btn active" data-view="view-college-portal">🏛️ College Approval Portal</button>
      <button class="nav-tab-btn" data-view="view-ledger">🔗 Trust Ledger</button>
      <button class="nav-tab-btn" data-view="view-copilot">🤖 Handbook Copilot</button>
    `;
    setupNavTabListeners();
    showView("view-college-portal");
    loadCollegeApplicationData();
  } else {
    // Officer Tabs
    navTabs.innerHTML = `
      <button class="nav-tab-btn active" data-view="view-officer-portal">🛡️ Scrutiny Queue & Triage</button>
      <button class="nav-tab-btn" data-view="view-ledger">🔗 Trust Ledger</button>
      <button class="nav-tab-btn" data-view="view-copilot">🤖 Officer Copilot</button>
    `;
    setupNavTabListeners();
    showView("view-officer-portal");
    loadOfficerQueue();
  }
}

function setupNavTabListeners() {
  document.querySelectorAll(".nav-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      showView(btn.dataset.view);
      if (btn.dataset.view === "view-ledger") loadLedgerEntries();
      if (btn.dataset.view === "view-officer-portal") loadOfficerQueue();
    });
  });
}

// ==================== COLLEGE PORTAL LOGIC ====================
function initCollegePortalEvents() {
  // Save Parameters
  document.getElementById("formCollegeParams").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentUser || !currentUser.institution_id) return;

    const formParams = new URLSearchParams();
    formParams.append("institution_id", currentUser.institution_id);
    formParams.append("applied_intake", document.getElementById("inpAppliedIntake").value);
    formParams.append("sanctioned_intake", document.getElementById("inpSanctionedIntake").value);
    formParams.append("faculty_count", document.getElementById("inpFacultyCount").value);
    formParams.append("total_students", document.getElementById("inpTotalStudents").value);
    formParams.append("computer_count", document.getElementById("inpComputerCount").value);

    try {
      const res = await fetch(`${API_BASE}/api/college/submit-details`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formParams
      });
      const data = await res.json();
      alert("Institutional parameters saved. Now please upload the required documents.");
      loadCollegeApplicationData();
    } catch (err) {
      alert("Error saving details: " + err.message);
    }
  });

  // Upload Document One by One
  document.getElementById("formDocUpload").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentActiveApp) {
      alert("Please submit the institutional parameters first to initialize your application draft.");
      return;
    }

    const docType = document.getElementById("selectDocType").value;
    const fileInput = document.getElementById("fileInputUpload");
    if (!fileInput.files || fileInput.files.length === 0) {
      alert("Please select a PDF file.");
      return;
    }

    const btn = document.getElementById("btnUploadDocSubmit");
    btn.innerText = "⏳ Extracting Text, Tables & Scanning PDF...";
    btn.disabled = true;

    try {
      const formData = new FormData();
      formData.append("application_id", currentActiveApp.id);
      formData.append("doc_type", docType);
      formData.append("file", fileInput.files[0]);

      const res = await fetch(`${API_BASE}/api/college/upload-checklist-doc`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");

      let alertMsg = `✓ Document '${docType}' scanned successfully!\n`;
      if (data.classification) {
        alertMsg += `🤖 AI Classifier: ${data.classification.predicted_category} (${Math.round(data.classification.confidence * 100)}% confidence)\n`;
        if (data.classification.category_anomaly) {
          alertMsg += `⚠️ WARNING: Content appears to be '${data.classification.predicted_category}', not '${docType}'!\n`;
        }
      }
      alertMsg += `Readiness Score: ${data.readiness_score}/100`;
      alert(alertMsg);

      fileInput.value = "";
      loadCollegeApplicationData();
    } catch (err) {
      alert("Upload & Scan Error: " + err.message);
    } finally {
      btn.innerText = "🚀 Upload, Scan & Analyze Real PDF";
      btn.disabled = false;
    }
  });

  // Upload Infrastructure Photo (YOLOv8 + GPS)
  const infraForm = document.getElementById("formInfraUpload");
  if (infraForm) {
    infraForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!currentActiveApp) {
        alert("Please submit parameters first.");
        return;
      }
      const photoType = document.getElementById("selectInfraType").value;
      const photoInput = document.getElementById("infraPhotoInput");
      if (!photoInput.files || photoInput.files.length === 0) {
        alert("Please select a photo.");
        return;
      }

      const btn = document.getElementById("btnUploadInfraSubmit");
      btn.innerText = "⏳ Running YOLOv8 Indicator Detection...";
      btn.disabled = true;

      try {
        const formData = new FormData();
        formData.append("application_id", currentActiveApp.id);
        formData.append("photo_type", photoType);
        formData.append("file", photoInput.files[0]);

        const res = await fetch(`${API_BASE}/api/college/upload-infra-photo`, {
          method: "POST",
          body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Analysis failed");

        const resBox = document.getElementById("infraAnalysisResult");
        resBox.style.display = "block";
        const ind = data.analysis.detected_indicators;
        resBox.innerHTML = `
          <div style="font-weight:700; color:var(--accent-purple); margin-bottom:4px;">👁️ YOLOv8 Pretrained Detections:</div>
          <div>💻 Computers / Laptops: <b>${ind.computers}</b> | 🖥️ Monitors: <b>${ind.monitors}</b> | 🪑 Chairs: <b>${ind.chairs}</b> | 🪑 Benches: <b>${ind.benches}</b></div>
          <div style="margin-top:6px; color:${data.analysis.gps_match ? 'var(--accent-emerald)' : 'var(--accent-rose)'};">
            ${data.analysis.gps_match ? '✓ Geotag GPS verified within campus radius' : '⚠️ Geotag GPS discrepancy with campus registration'}
          </div>
          <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">${data.analysis.advisory}</div>
        `;

        alert("Infrastructure photo analyzed with YOLOv8 indicators!");
        photoInput.value = "";
        loadCollegeApplicationData();
      } catch (err) {
        alert("Infra CV Error: " + err.message);
      } finally {
        btn.innerText = "👁️ Run YOLOv8 Object Detection & Geotag Verification";
        btn.disabled = false;
      }
    });
  }
}

async function loadCollegeApplicationData() {
  if (!currentUser || !currentUser.institution_id) return;
  document.getElementById("colDashboardTitle").innerText = `${currentUser.institution_name} (${currentUser.aicte_id})`;

  try {
    const res = await fetch(`${API_BASE}/api/college/active-application?institution_id=${currentUser.institution_id}`);
    const data = await res.json();

    if (!data.has_application) {
      document.getElementById("colReadinessNum").innerText = "0/100";
      document.getElementById("readinessScoreBadge").innerText = "No Submission";
      document.getElementById("colUploadedDocsList").innerHTML = `<div style="color:var(--text-dim); font-size:12px; padding:10px; text-align:center;">Submit parameters to begin application.</div>`;
      return;
    }

    currentActiveApp = data.application;
    const docs = data.documents;
    const findings = data.findings;

    // Scores
    document.getElementById("appStatusBadge").innerText = currentActiveApp.status;
    document.getElementById("colReadinessNum").innerText = `${currentActiveApp.readiness_score}/100`;
    document.getElementById("readinessScoreBadge").innerText = `Readiness: ${currentActiveApp.readiness_score}/100`;

    // Render Uploaded Documents
    const docsList = document.getElementById("colUploadedDocsList");
    if (docs.length === 0) {
      docsList.innerHTML = `<div style="color:var(--text-dim); font-size:12px; padding:10px; text-align:center;">No documents uploaded yet.</div>`;
    } else {
      docsList.innerHTML = docs.map(d => `
        <div style="background:rgba(2, 6, 23, 0.6); padding:10px; border-radius:6px; border:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-weight:600; font-size:12px; color:#fff;">${d.doc_type}</div>
            <div style="font-size:10px; color:var(--text-dim); font-family:'JetBrains Mono';">${d.original_filename} &bull; SHA256: ${d.sha256.substring(0, 16)}...</div>
          </div>
          <a href="${API_BASE}/uploads/${d.file_key}" target="_blank" class="btn btn-secondary" style="padding:2px 8px; font-size:10px;">View PDF</a>
        </div>
      `).join("");
    }

    // Render Findings
    const findList = document.getElementById("colFindingsList");
    if (findings.length === 0) {
      findList.innerHTML = `<div style="background:rgba(16, 185, 129, 0.1); color:#6ee7b7; border-radius:6px; padding:8px; font-size:12px;">✓ No regulatory violations or discrepancies detected.</div>`;
    } else {
      findList.innerHTML = findings.map(f => `
        <div style="background:rgba(2, 6, 23, 0.6); border:1px solid ${f.severity === 'HIGH' ? 'rgba(244, 63, 94, 0.3)' : 'rgba(245, 158, 11, 0.3)'}; border-radius:6px; padding:8px;">
          <div style="font-weight:600; font-size:12px; color:${f.severity === 'HIGH' ? '#fda4af' : '#fcd34d'};">${f.title}</div>
          <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">${f.reason}</div>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Failed to load application data", err);
  }
}

// ==================== OFFICER PORTAL LOGIC ====================
function initOfficerPortalEvents() {
  document.getElementById("btnOfficerApprove").addEventListener("click", () => handleOfficerDecision("APPROVED"));
  document.getElementById("btnOfficerReject").addEventListener("click", () => handleOfficerDecision("REJECTED"));
}

async function loadOfficerQueue() {
  try {
    const res = await fetch(`${API_BASE}/api/officer/applications`);
    const apps = await res.json();
    const tbody = document.getElementById("officerQueueTableBody");

    if (apps.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:var(--text-dim); padding:20px;">No applications in queue. Once a college registers and submits documents, it will appear here.</td></tr>`;
      return;
    }

    tbody.innerHTML = apps.map(app => {
      let riskBadge = `<span class="badge-pill badge-low">${app.risk_score} (Low)</span>`;
      if (app.risk_score > 60) riskBadge = `<span class="badge-pill badge-high">${app.risk_score} (High)</span>`;
      else if (app.risk_score > 30) riskBadge = `<span class="badge-pill badge-medium">${app.risk_score} (Med)</span>`;

      let decisionBadge = `<span class="badge-pill badge-low">Pending</span>`;
      if (app.decision === "APPROVED") decisionBadge = `<span class="badge-pill badge-success">APPROVED</span>`;
      if (app.decision === "REJECTED") decisionBadge = `<span class="badge-pill badge-high">REJECTED</span>`;

      return `
        <tr>
          <td style="font-family:'JetBrains Mono'; font-weight:700;">#APP-${app.id}</td>
          <td><b>${app.institution_name}</b></td>
          <td>${app.aicte_id}</td>
          <td>${app.state}</td>
          <td><b>${app.readiness_score}/100</b></td>
          <td>${riskBadge}</td>
          <td><span class="badge-pill badge-medium">${app.status}</span></td>
          <td>${decisionBadge}</td>
          <td>
            <button class="btn btn-primary" style="padding:4px 10px; font-size:11px;" onclick="openOfficerScrutiny(${app.id})">
              Inspect & Scrutinize
            </button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Failed to load queue", err);
  }
}

async function openOfficerScrutiny(appId) {
  try {
    const res = await fetch(`${API_BASE}/api/officer/application/${appId}`);
    const data = await res.json();
    selectedOfficerApp = data;

    const split = document.getElementById("officerDetailSplit");
    split.style.display = "grid";
    split.scrollIntoView({ behavior: "smooth" });

    const app = data.application;
    const docs = data.documents;
    const findings = data.findings;

    document.getElementById("officerRiskBadge").innerText = `Risk Score: ${app.risk_score}/100`;

    // Load First Document
    if (docs.length > 0) {
      const doc = docs[0];
      document.getElementById("officerDocTitle").innerText = `${doc.doc_type} (${doc.original_filename})`;
      document.getElementById("officerDocHash").innerText = `SHA-256: ${doc.sha256}`;
      document.getElementById("btnOfficerDownloadPdf").href = `${API_BASE}/uploads/${doc.file_key}`;
      document.getElementById("officerDocIframe").src = `${API_BASE}/uploads/${doc.file_key}#toolbar=0`;

      // Extractions
      const extBox = document.getElementById("officerExtractionsBox");
      if (doc.extractions && doc.extractions.length > 0) {
        extBox.innerHTML = doc.extractions.map(e => `
          <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding:4px 0;">
            <span style="color:var(--text-muted); font-weight:600;">${e.field_name}:</span>
            <span style="color:var(--accent-cyan); font-family:'JetBrains Mono';">${e.value}</span>
          </div>
        `).join("");
      } else {
        extBox.innerHTML = `<span style="color:var(--text-dim);">No specific fields extracted.</span>`;
      }
    }

    // Render Findings List
    const fList = document.getElementById("officerFindingsList");
    if (findings.length === 0) {
      fList.innerHTML = `<div style="color:var(--accent-emerald); padding:16px;">✓ Zero regulatory flags or forensic anomalies detected. Ready for approval.</div>`;
    } else {
      fList.innerHTML = findings.map(f => `
        <div style="background:rgba(2, 6, 23, 0.6); border:1px solid ${f.severity === 'HIGH' ? 'rgba(244, 63, 94, 0.3)' : 'rgba(245, 158, 11, 0.3)'}; border-radius:8px; padding:12px;">
          <div style="display:flex; justify-content:space-between;">
            <span style="font-weight:600; color:#fff; font-size:13px;">${f.title}</span>
            <span class="badge-pill ${f.severity === 'HIGH' ? 'badge-high' : 'badge-medium'}">${f.severity}</span>
          </div>
          <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">${f.reason}</div>
          <div style="display:flex; gap:8px; margin-top:8px;">
            <button class="btn btn-success" style="padding:2px 8px; font-size:10px;" onclick="takeFindingAction(${f.id}, 'ACCEPT')">✓ Accept Flag</button>
            <button class="btn btn-secondary" style="padding:2px 8px; font-size:10px;" onclick="takeFindingAction(${f.id}, 'DISMISS')">✕ Dismiss</button>
            <button class="btn btn-danger" style="padding:2px 8px; font-size:10px;" onclick="takeFindingAction(${f.id}, 'ESCALATE')">🔺 Escalate</button>
          </div>
        </div>
      `).join("");
    }
  } catch (err) {
    alert("Error loading application: " + err.message);
  }
}

async function takeFindingAction(findingId, action) {
  let reason = prompt(`Enter justification for ${action}:`) || "Officer verification";
  try {
    const res = await fetch(`${API_BASE}/api/findings/${findingId}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: action,
        reason: reason,
        officer_id: currentUser ? currentUser.id : 1,
        officer_name: currentUser ? currentUser.name : "Central Scrutiny Officer"
      })
    });
    alert(`Action '${action}' recorded in tamper-evident ledger.`);
    openOfficerScrutiny(selectedOfficerApp.application.id);
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function handleOfficerDecision(decision) {
  if (!selectedOfficerApp) return;
  const reason = document.getElementById("inpOfficerDecisionReason").value.trim();
  if (!reason) {
    alert("Mandatory statutory rule: An officer cannot record a final decision without entering a written justification.");
    return;
  }

  try {
    const appId = selectedOfficerApp.application.id;
    const res = await fetch(`${API_BASE}/api/officer/decide-application/${appId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        decision: decision,
        reason: reason,
        officer_name: currentUser ? currentUser.name : "Central Scrutiny Officer"
      })
    });
    const data = await res.json();
    alert(`Application #${appId} officially marked ${decision} by officer.`);
    loadOfficerQueue();
    openOfficerScrutiny(appId);
  } catch (err) {
    alert("Error recording decision: " + err.message);
  }
}

// ==================== TRUST LEDGER LOGIC ====================
function initLedgerEvents() {
  document.getElementById("btnVerifyChain").addEventListener("click", async () => {
    const banner = document.getElementById("chainStatusBanner");
    try {
      const res = await fetch(`${API_BASE}/api/trust-ledger/verify`);
      const data = await res.json();

      banner.style.display = "block";
      if (data.valid) {
        banner.style.background = "rgba(16, 185, 129, 0.15)";
        banner.style.border = "1px solid rgba(16, 185, 129, 0.5)";
        banner.style.color = "#6ee7b7";
        banner.innerHTML = `
          <div style="font-weight:700; font-size:15px;">✓ Cryptographic Hash Chain Verified Intact</div>
          <div style="font-size:12px; margin-top:4px;">All ${data.total_entries} transaction entries verified against Merkle Root in MySQL. Zero tampering detected.</div>
        `;
      } else {
        banner.style.background = "rgba(244, 63, 94, 0.2)";
        banner.style.border = "1px solid rgba(244, 63, 94, 0.6)";
        banner.style.color = "#fda4af";
        banner.innerHTML = `
          <div style="font-weight:700; font-size:15px;">🚨 Cryptographic Integrity Violation!</div>
          <div style="font-size:12px; margin-top:4px;">${data.error}</div>
        `;
      }
    } catch (err) {
      alert("Verification error: " + err.message);
    }
  });
}

async function loadLedgerEntries() {
  try {
    const res = await fetch(`${API_BASE}/api/trust-ledger/entries`);
    const data = await res.json();
    const tbody = document.getElementById("trustLedgerTableBody");

    if (data.entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-dim); padding:20px;">No audit records in ledger yet. Perform an action to see cryptographic entries.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.entries.map(e => `
      <tr>
        <td style="font-family:'JetBrains Mono'; font-weight:700;">#${e.seq}</td>
        <td>${e.actor}</td>
        <td><span class="badge-pill badge-low">${e.action}</span></td>
        <td>${e.entity_type} #${e.entity_id}</td>
        <td style="font-family:'JetBrains Mono'; font-size:11px; color:var(--text-dim);">${e.prev_hash.substring(0, 16)}...</td>
        <td style="font-family:'JetBrains Mono'; font-size:11px; color:var(--accent-cyan);">${e.entry_hash.substring(0, 16)}...</td>
        <td style="font-size:11px; color:var(--text-muted);">${new Date(e.created_at).toLocaleTimeString()}</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Failed to load ledger", err);
  }
}

// ==================== OFFICER COPILOT LOGIC ====================
function initCopilotEvents() {
  const input = document.getElementById("copilotTextInput");
  const btn = document.getElementById("btnCopilotSend");
  const container = document.getElementById("chatMsgContainer");

  const sendQuery = async (queryText) => {
    if (!queryText.trim()) return;

    const uMsg = document.createElement("div");
    uMsg.className = "chat-msg user";
    uMsg.innerText = queryText;
    container.appendChild(uMsg);
    input.value = "";
    container.scrollTop = container.scrollHeight;

    const loadingMsg = document.createElement("div");
    loadingMsg.className = "chat-msg copilot";
    loadingMsg.innerText = "Searching AICTE Approval Handbook...";
    container.appendChild(loadingMsg);
    container.scrollTop = container.scrollHeight;

    try {
      const res = await fetch(`${API_BASE}/api/copilot/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryText })
      });
      const data = await res.json();

      let citationHtml = "";
      if (data.citations && data.citations.length > 0) {
        citationHtml = data.citations.map(c => `
          <div class="citation-chip">📖 ${c.clause}: ${c.title}</div>
        `).join("");
      }

      loadingMsg.innerHTML = `
        <div>${data.answer.replace(/\n/g, '<br>')}</div>
        ${citationHtml}
      `;
      container.scrollTop = container.scrollHeight;
    } catch (err) {
      loadingMsg.innerText = "Error: " + err.message;
    }
  };

  btn.addEventListener("click", () => sendQuery(input.value));
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendQuery(input.value);
  });

  document.querySelectorAll(".preset-btn").forEach(b => {
    b.addEventListener("click", () => sendQuery(b.innerText));
  });
}
