// State Management
const state = {
  emails: [],
  page: 1,
  limit: 10,
  total: 0,
  filterCategory: "",
  filterStatus: "",
  searchQuery: "",
  activeEmail: null,
  activeAiResult: null,
};

// DOM Elements
const elements = {
  dbStatusPill: document.getElementById("db-status-pill"),
  dbStatusText: document.getElementById("db-status-text"),
  llmModelText: document.getElementById("llm-model-text"),
  
  // Stats
  statTotal: document.getElementById("stat-total"),
  statPayroll: document.getElementById("stat-payroll"),
  statBenefits: document.getElementById("stat-benefits"),
  statTax: document.getElementById("stat-tax"),
  statPending: document.getElementById("stat-pending"),
  statVerified: document.getElementById("stat-verified"),
  statApproved: document.getElementById("stat-approved"),
  statCorrected: document.getElementById("stat-corrected"),

  // Table
  tableBody: document.getElementById("email-table-body"),
  paginationInfo: document.getElementById("pagination-info"),
  btnPrevPage: document.getElementById("btn-prev-page"),
  btnNextPage: document.getElementById("btn-next-page"),
  pageIndicator: document.getElementById("page-indicator"),

  // Filters & Search
  inputSearch: document.getElementById("input-search"),
  statusFilters: document.getElementById("status-filters"),
  categoryFilters: document.getElementById("category-filters"),
  btnRefresh: document.getElementById("btn-refresh"),

  // HITL Modal
  hitlModal: document.getElementById("hitl-modal"),
  btnCloseModal: document.getElementById("btn-close-modal"),
  modalSender: document.getElementById("modal-email-sender"),
  modalSubject: document.getElementById("modal-email-subject"),
  modalBody: document.getElementById("modal-email-body"),
  modalAiCat: document.getElementById("modal-ai-category"),
  modalAiConf: document.getElementById("modal-ai-confidence"),
  modalConfBar: document.getElementById("modal-conf-bar"),
  modalAiReason: document.getElementById("modal-ai-reasoning"),
  btnHitlYes: document.getElementById("btn-hitl-yes"),
  btnHitlNo: document.getElementById("btn-hitl-no"),
  correctionPanel: document.getElementById("hitl-correction-panel"),
  inputFeedback: document.getElementById("input-feedback"),
  btnSubmitCorrection: document.getElementById("btn-submit-correction"),

  // Evaluation Modal
  btnOpenEval: document.getElementById("btn-open-eval"),
  evalModal: document.getElementById("eval-modal"),
  btnCloseEval: document.getElementById("btn-close-eval"),
  evalAccuracy: document.getElementById("eval-accuracy"),
  evalVerifiedCount: document.getElementById("eval-verified-count"),
  evalPayrollPrec: document.getElementById("eval-payroll-prec"),
  evalPayrollRec: document.getElementById("eval-payroll-rec"),
  evalPayrollF1: document.getElementById("eval-payroll-f1"),
  evalPayrollSup: document.getElementById("eval-payroll-sup"),
  evalBenefitsPrec: document.getElementById("eval-benefits-prec"),
  evalBenefitsRec: document.getElementById("eval-benefits-rec"),
  evalBenefitsF1: document.getElementById("eval-benefits-f1"),
  evalBenefitsSup: document.getElementById("eval-benefits-sup"),
  evalTaxPrec: document.getElementById("eval-tax-prec"),
  evalTaxRec: document.getElementById("eval-tax-rec"),
  evalTaxF1: document.getElementById("eval-tax-f1"),
  evalTaxSup: document.getElementById("eval-tax-sup"),

  // Toast
  toast: document.getElementById("toast"),
};

// Toast helper
function showToast(message, duration = 3500) {
  elements.toast.textContent = message;
  elements.toast.classList.remove("hidden");
  setTimeout(() => {
    elements.toast.classList.add("hidden");
  }, duration);
}

// 1. Health & Status
async function checkHealth() {
  try {
    const res = await fetch("/health");
    if (!res.ok) throw new Error("Health check failed");
    const data = await res.json();
    if (data.database && data.database.status === "connected") {
      elements.dbStatusText.textContent = `NeonDB: ${data.database.database}`;
    } else {
      elements.dbStatusText.textContent = "NeonDB Disconnected";
    }
    if (data.model_name) {
      elements.llmModelText.textContent = `${data.llm_provider.toUpperCase()} (${data.model_name})`;
    }
  } catch (err) {
    elements.dbStatusText.textContent = "Offline / Connection Error";
  }
}

// 2. Statistics
async function loadStatistics() {
  try {
    const res = await fetch("/statistics");
    if (!res.ok) throw new Error("Failed to load statistics");
    const data = await res.json();

    elements.statTotal.textContent = data.total_emails ?? 0;
    elements.statPayroll.textContent = data.payroll_emails ?? 0;
    elements.statBenefits.textContent = data.benefits_emails ?? 0;
    elements.statTax.textContent = data.tax_emails ?? 0;
    elements.statPending.textContent = data.pending_verification ?? 0;
    elements.statVerified.textContent = (data.approved || 0) + (data.corrected || 0);
    elements.statApproved.textContent = data.approved ?? 0;
    elements.statCorrected.textContent = data.corrected ?? 0;
  } catch (err) {
    console.error("Error loading statistics:", err);
  }
}

// 3. Emails Listing
async function loadEmails() {
  elements.tableBody.innerHTML = `
    <tr>
      <td colspan="8" class="text-center loading-cell">
        <div class="spinner"></div> Loading emails from NeonDB...
      </td>
    </tr>
  `;

  try {
    const params = new URLSearchParams({
      page: state.page,
      limit: state.limit,
    });
    if (state.filterCategory) params.append("category", state.filterCategory);
    if (state.filterStatus) params.append("status", state.filterStatus);
    if (state.searchQuery) params.append("search", state.searchQuery);

    const res = await fetch(`/emails?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch emails");
    const data = await res.json();

    state.emails = data.emails;
    state.total = data.total;

    renderEmailsTable();
    updatePagination();
  } catch (err) {
    elements.tableBody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center" style="color: #ef4444; padding: 24px;">
          Failed to load emails: ${err.message}
        </td>
      </tr>
    `;
  }
}

function renderEmailsTable() {
  if (state.emails.length === 0) {
    elements.tableBody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center" style="padding: 32px; color: var(--text-muted);">
          No emails match the selected filters.
        </td>
      </tr>
    `;
    return;
  }

  elements.tableBody.innerHTML = state.emails.map(email => {
    const aiCategory = email.ai_category || "--";
    const verifiedCat = email.verified_category || "--";
    const status = email.verification_status || "pending";
    const confVal = email.ai_confidence != null ? Math.round(email.ai_confidence * 100) : null;

    let aiCatPill = `<span class="category-pill pill-${aiCategory.toLowerCase()}">${aiCategory}</span>`;
    if (aiCategory === "--") aiCatPill = `<span style="color: var(--text-subtle);">Unclassified</span>`;

    let verifiedCatPill = `<span class="category-pill pill-${verifiedCat.toLowerCase()}">${verifiedCat}</span>`;
    if (verifiedCat === "--") verifiedCatPill = `<span style="color: var(--text-subtle);">None</span>`;

    let confHtml = `<span style="color: var(--text-subtle);">--</span>`;
    if (confVal != null) {
      confHtml = `
        <div class="mini-conf">
          <div class="mini-conf-bar-bg">
            <div class="mini-conf-bar-fill" style="width: ${confVal}%"></div>
          </div>
          <span class="mini-conf-text">${confVal}%</span>
        </div>
      `;
    }

    let actionBtn = "";
    if (status === "pending") {
      actionBtn = `
        <button class="btn btn-sm btn-action-classify" onclick="triggerClassification(${email.id})">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          Classify
        </button>
      `;
    } else {
      actionBtn = `
        <button class="btn btn-sm btn-action-verify" onclick="triggerReview(${email.id})">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          Re-verify
        </button>
      `;
    }

    return `
      <tr>
        <td style="font-family: 'JetBrains Mono', monospace; color: var(--text-subtle);">${email.id}</td>
        <td>
          <div class="email-sender" title="${escapeHtml(email.sender)}">${escapeHtml(email.sender)}</div>
        </td>
        <td>
          <div class="email-subject-wrapper">
            <div class="email-subject" title="${escapeHtml(email.subject)}">${escapeHtml(email.subject)}</div>
            <div class="email-body-snippet">${escapeHtml(email.body.substring(0, 95))}...</div>
          </div>
        </td>
        <td>${aiCatPill}</td>
        <td>${confHtml}</td>
        <td>${verifiedCatPill}</td>
        <td>
          <span class="status-badge ${status}">${status}</span>
        </td>
        <td style="text-align: right;">${actionBtn}</td>
      </tr>
    `;
  }).join("");
}

function updatePagination() {
  const totalPages = Math.ceil(state.total / state.limit) || 1;
  const startIdx = state.total === 0 ? 0 : (state.page - 1) * state.limit + 1;
  const endIdx = Math.min(state.page * state.limit, state.total);

  elements.paginationInfo.textContent = `Showing ${startIdx}-${endIdx} of ${state.total} emails`;
  elements.pageIndicator.textContent = `Page ${state.page} of ${totalPages}`;

  elements.btnPrevPage.disabled = state.page <= 1;
  elements.btnNextPage.disabled = state.page >= totalPages;
}

// 4. HITL Classification & Verification
async function triggerClassification(emailId) {
  const email = state.emails.find(e => e.id === emailId);
  if (!email) return;

  state.activeEmail = email;

  // Open modal in loading state
  openHitlModal(email, {
    category: "Classifying...",
    confidence: null,
    reasoning: "AI agent is analyzing email subject and body...",
    loading: true,
  });

  try {
    const res = await fetch(`/emails/${emailId}/classify`, {
      method: "POST"
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Classification failed");
    }

    const aiResult = await res.json();
    state.activeAiResult = aiResult;

    // Update modal with actual prediction
    populateModalWithPrediction(aiResult);
  } catch (err) {
    showToast(`Error: ${err.message}`);
    closeHitlModal();
  }
}

async function triggerReview(emailId) {
  const email = state.emails.find(e => e.id === emailId);
  if (!email) return;

  state.activeEmail = email;
  state.activeAiResult = {
    email_id: email.id,
    category: email.ai_category || "Payroll",
    confidence: email.ai_confidence || 0.9,
    reasoning: email.classification_reason || "Previously classified by AI agent.",
  };

  openHitlModal(email, state.activeAiResult);
  populateModalWithPrediction(state.activeAiResult);
}

function openHitlModal(email, prediction) {
  elements.modalSender.textContent = email.sender;
  elements.modalSubject.textContent = email.subject;
  elements.modalBody.textContent = email.body;

  elements.correctionPanel.classList.add("hidden");
  elements.inputFeedback.value = "";
  // Uncheck radios
  document.querySelectorAll('input[name="correct_category"]').forEach(r => r.checked = false);

  elements.hitlModal.classList.remove("hidden");
}

function populateModalWithPrediction(prediction) {
  elements.modalAiCat.textContent = prediction.category;
  elements.modalAiCat.className = `category-pill pill-large pill-${prediction.category.toLowerCase()}`;

  const confVal = Math.round((prediction.confidence ?? 0.95) * 100);
  elements.modalAiConf.textContent = `${confVal}%`;
  elements.modalConfBar.style.width = `${confVal}%`;

  elements.modalAiReason.textContent = prediction.reasoning || "Classified based on contextual analysis.";

  elements.btnHitlYes.disabled = false;
  elements.btnHitlNo.disabled = false;
}

function closeHitlModal() {
  elements.hitlModal.classList.add("hidden");
  state.activeEmail = null;
  state.activeAiResult = null;
}

// 5. Submit Human Verification
async function submitVerification(decision, correctCategory = null, feedback = null) {
  if (!state.activeEmail) return;

  const emailId = state.activeEmail.id;
  const payload = {
    decision: decision,
    correct_category: correctCategory,
    feedback: feedback,
    verified_by: "human_supervisor",
  };

  try {
    const res = await fetch(`/emails/${emailId}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Verification failed");
    }

    const updated = await res.json();
    closeHitlModal();

    showToast(`✓ Verification recorded in NeonDB! (Status: ${updated.verification_status.toUpperCase()})`);

    // Reload data to reflect immediate DB updates
    loadStatistics();
    loadEmails();
  } catch (err) {
    showToast(`Verification error: ${err.message}`);
  }
}

// 6. Evaluation Modal
async function openEvaluationModal() {
  elements.evalModal.classList.remove("hidden");
  elements.evalAccuracy.textContent = "Calculating...";

  try {
    const res = await fetch("/evaluation");
    if (!res.ok) throw new Error("Failed to fetch evaluation metrics");
    const data = await res.json();

    elements.evalAccuracy.textContent = `${Math.round(data.accuracy * 100)}%`;
    elements.evalVerifiedCount.textContent = data.verified_count;

    // Payroll
    elements.evalPayrollPrec.textContent = (data.payroll.precision * 100).toFixed(1) + "%";
    elements.evalPayrollRec.textContent = (data.payroll.recall * 100).toFixed(1) + "%";
    elements.evalPayrollF1.textContent = (data.payroll.f1 * 100).toFixed(1) + "%";
    elements.evalPayrollSup.textContent = data.payroll.support;

    // Benefits
    elements.evalBenefitsPrec.textContent = (data.benefits.precision * 100).toFixed(1) + "%";
    elements.evalBenefitsRec.textContent = (data.benefits.recall * 100).toFixed(1) + "%";
    elements.evalBenefitsF1.textContent = (data.benefits.f1 * 100).toFixed(1) + "%";
    elements.evalBenefitsSup.textContent = data.benefits.support;

    // Tax
    elements.evalTaxPrec.textContent = (data.tax.precision * 100).toFixed(1) + "%";
    elements.evalTaxRec.textContent = (data.tax.recall * 100).toFixed(1) + "%";
    elements.evalTaxF1.textContent = (data.tax.f1 * 100).toFixed(1) + "%";
    elements.evalTaxSup.textContent = data.tax.support;
  } catch (err) {
    showToast(`Evaluation error: ${err.message}`);
  }
}

function closeEvaluationModal() {
  elements.evalModal.classList.add("hidden");
}

// Event Listeners
function setupEventListeners() {
  // Search input debounce
  let searchTimeout = null;
  elements.inputSearch.addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      state.searchQuery = e.target.value.trim();
      state.page = 1;
      loadEmails();
    }, 300);
  });

  // Status Filter Pills
  elements.statusFilters.addEventListener("click", (e) => {
    if (!e.target.classList.contains("pill")) return;
    elements.statusFilters.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
    e.target.classList.add("active");
    state.filterStatus = e.target.dataset.status;
    state.page = 1;
    loadEmails();
  });

  // Category Filter Pills
  elements.categoryFilters.addEventListener("click", (e) => {
    if (!e.target.classList.contains("pill")) return;
    elements.categoryFilters.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
    e.target.classList.add("active");
    state.filterCategory = e.target.dataset.category;
    state.page = 1;
    loadEmails();
  });

  // Refresh Button
  elements.btnRefresh.addEventListener("click", () => {
    loadStatistics();
    loadEmails();
    showToast("Data refreshed from NeonDB.");
  });

  // Pagination
  elements.btnPrevPage.addEventListener("click", () => {
    if (state.page > 1) {
      state.page--;
      loadEmails();
    }
  });

  elements.btnNextPage.addEventListener("click", () => {
    const totalPages = Math.ceil(state.total / state.limit);
    if (state.page < totalPages) {
      state.page++;
      loadEmails();
    }
  });

  // Modal Close
  elements.btnCloseModal.addEventListener("click", closeHitlModal);
  elements.hitlModal.addEventListener("click", (e) => {
    if (e.target === elements.hitlModal) closeHitlModal();
  });

  // HITL Decision Buttons
  elements.btnHitlYes.addEventListener("click", () => {
    submitVerification("YES");
  });

  elements.btnHitlNo.addEventListener("click", () => {
    elements.correctionPanel.classList.remove("hidden");
    // Pre-select alternate category if desired
    const currentCat = state.activeAiResult?.category;
    document.querySelectorAll('input[name="correct_category"]').forEach(radio => {
      if (radio.value === currentCat) {
        radio.checked = false;
        radio.parentElement.style.opacity = "0.5";
      } else {
        radio.parentElement.style.opacity = "1";
      }
    });
  });

  // Submit Correction
  elements.btnSubmitCorrection.addEventListener("click", () => {
    const selectedRadio = document.querySelector('input[name="correct_category"]:checked');
    if (!selectedRadio) {
      showToast("Please select the correct category.");
      return;
    }
    const correctCat = selectedRadio.value;
    const feedback = elements.inputFeedback.value.trim() || `Corrected from ${state.activeAiResult?.category} to ${correctCat}`;
    submitVerification("NO", correctCat, feedback);
  });

  // Evaluation Modal
  elements.btnOpenEval.addEventListener("click", openEvaluationModal);
  elements.btnCloseEval.addEventListener("click", closeEvaluationModal);
  elements.evalModal.addEventListener("click", (e) => {
    if (e.target === elements.evalModal) closeEvaluationModal();
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Initial Boot
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  checkHealth();
  loadStatistics();
  loadEmails();
});
