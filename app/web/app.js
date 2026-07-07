const metrics = document.querySelector("#metrics");
const loginShell = document.querySelector("#login-shell");
const appShell = document.querySelector("#app-shell");
const loginForm = document.querySelector("#login-form");
const loginError = document.querySelector("#login-error");
const loginUser = document.querySelector("#login-user");
const logoutButton = document.querySelector("#logout");
const cases = document.querySelector("#cases");
const contracts = document.querySelector("#contracts");
const payments = document.querySelector("#payments");
const documents = document.querySelector("#documents");
const form = document.querySelector("#case-form");
const formTitle = document.querySelector("#form-title");
const submitCase = document.querySelector("#submit-case");
const cancelEdit = document.querySelector("#cancel-edit");
const importPreviewForm = document.querySelector("#import-preview-form");
const importPreviewResult = document.querySelector("#import-preview-result");
const mappingCatalogResult = document.querySelector("#mapping-catalog-result");
const refreshMappingCatalog = document.querySelector("#refresh-mapping-catalog");
const dryRunCases = document.querySelector("#dry-run-cases");
const dryRunResult = document.querySelector("#dry-run-result");
const preflightCases = document.querySelector("#preflight-cases");
const preflightResult = document.querySelector("#preflight-result");
const caseTabs = [...document.querySelectorAll("[data-case-tab]")];
const casePanels = [...document.querySelectorAll("[data-case-panel]")];
const moduleCards = [...document.querySelectorAll(".module-card")];
const modulePanels = [...document.querySelectorAll(".module-panel")];
const moduleExtras = [...document.querySelectorAll("[data-module-parent]")];
const drillCards = [...document.querySelectorAll("[data-drill-target]")];
let lastImportPreview = null;
let lastImportBatchId = null;
let importWarningFilter = { severity: "all", code: "all" };
const resourceForms = {
  contract: document.querySelector("#contract-form"),
  payment: document.querySelector("#payment-form"),
  document: document.querySelector("#document-form"),
};
const resourceLists = { contract: contracts, payment: payments, document: documents };
const resourceCaches = { contract: [], payment: [], document: [] };
const statusLabels = {
  draft: "草稿",
  reviewing: "審核中",
  approved: "已核准",
  disabled: "已停用",
  active: "有效",
  closed: "已結案",
  pending: "待處理",
  scheduled: "已排程",
  archived: "已歸檔",
  not_received: "尚未收到發票",
  received: "已收到發票",
  verified: "已驗證發票",
  blocked: "已阻擋",
  pass: "通過",
  warning: "警示",
  error: "錯誤",
};
let currentUser = null;
const tableLabels = {
  cases: "案件",
  contracts: "合約",
  payments: "付款",
  documents: "資料檢核",
};
const fieldLabels = {
  case_code: "案件編號",
  title: "案件名稱",
  owner: "負責人",
  amount: "金額",
  contract_id: "合約 ID",
  payment_amount: "付款金額",
  payment_month: "付款年月",
  file_name: "檔案名稱",
};
const gateLabels = {
  missing_required: "必填欄位缺漏",
  invalid_amount: "金額格式錯誤",
  invalid_month: "日期月份錯誤",
  duplicate_in_batch: "同批資料重複",
  preview_errors: "預覽錯誤",
  existing_case_code: "既有案件編號",
  requires_confirmation: "需要人工確認",
  formal_write_disabled: "正式寫入尚未開放",
  accepted_warning_codes_policy: "警示接受規則",
  source_chain_contract: "來源舉證鏈",
  stale_preview_guard: "預覽版本檢查",
  server_preview_rerun: "伺服器重新檢核",
  server_preview_fingerprint: "伺服器預覽指紋",
};
const gateMessages = {
  formal_write_disabled: "正式匯入確認仍需交易、回滾、來源舉證、預覽版本、操作者與冪等性閘門完成後才可開放。",
  preview_errors: "預覽錯誤必須為零，才可進入正式確認。",
  duplicate_in_batch: "同批資料不可出現重複案件編號。",
  existing_case_code: "既有案件編號目前視為新增衝突，不能直接覆寫。",
  requires_confirmation: "所有需要人工確認的候選欄位都必須明確確認。",
  accepted_warning_codes_policy: "警示接受清單尚未建立正式白名單規則，不能繞過錯誤或確認。",
  source_chain_contract: "正式寫入必須同步記錄批次、來源列、欄位對應版本與操作者，形成來源舉證鏈。",
  stale_preview_guard: "正式寫入前必須有預覽雜湊、列版本或批次鎖，避免使用過期預覽。",
  server_preview_rerun: "正式寫入前由伺服器重新產生預覽並比對結果。",
};
const modeLabels = {
  direct: "直接對應",
  alias: "別名對應",
  derived: "推導",
  required: "必填",
};
const resourceConfig = {
  contract: {
    plural: "contracts",
    idAttr: "contract-id",
    idField: "contractId",
    api: "/api/contracts",
    fields: ["contract_code", "contract_name", "vendor_name", "amount", "case_id", "status"],
    numberFields: ["amount", "case_id"],
    canDisable: true,
    render: (item) => `
      <strong>${escapeHtml(item.contract_code)}</strong>
      <span>${escapeHtml(item.contract_name)}</span>
      <span class="muted">${escapeHtml(valueOrDash(item.vendor_name))}</span>
      <span class="amount">${money(item.amount)} 元</span>
      <span>${escapeHtml(labelStatus(item.status))}</span>
    `,
  },
  payment: {
    plural: "payments",
    idAttr: "payment-id",
    idField: "paymentId",
    api: "/api/payments",
    fields: ["contract_id", "payment_month", "payment_amount", "invoice_status", "status"],
    numberFields: ["contract_id", "payment_amount"],
    canDisable: true,
    render: (item) => `
      <strong>${escapeHtml(item.payment_month)}</strong>
      <span>合約 #${escapeHtml(item.contract_id)}</span>
      <span class="amount">${money(item.payment_amount)} 元</span>
      <span class="muted">${escapeHtml(labelStatus(item.invoice_status))}</span>
      <span>${escapeHtml(labelStatus(item.status))}</span>
    `,
  },
  document: {
    plural: "documents",
    idAttr: "document-id",
    idField: "documentId",
    api: "/api/documents",
    fields: ["file_name", "document_type", "source_note", "status", "case_id", "contract_id"],
    numberFields: ["case_id", "contract_id"],
    canDisable: true,
    render: (item) => `
      <strong>${escapeHtml(item.file_name)}</strong>
      <span>${escapeHtml(labelDocumentType(item.document_type))}</span>
      <span>${escapeHtml(labelStatus(item.status || "active"))}</span>
      <span class="muted">案件 ${escapeHtml(valueOrDash(item.case_id))} / 合約 ${escapeHtml(valueOrDash(item.contract_id))}</span>
      <span>${escapeHtml(valueOrDash(item.source_note))}</span>
    `,
  },
};
let caseCache = [];

async function api(path, options) {
  const response = await fetch(path, { credentials: "same-origin", ...(options || {}) });
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch (_error) {
      // Keep the HTTP status text when the response body is not JSON.
    }
    throw new Error(message);
  }
  if (response.status === 204) {
    return { ok: true, data: null };
  }
  return response.json();
}

function metric(label, value) {
  return `<article class="metric"><span>${label}</span><strong>${value}</strong></article>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function valueOrDash(value) {
  return value === null || value === undefined || value === "" ? "-" : value;
}

function labelStatus(value) {
  return statusLabels[value] || valueOrDash(value);
}

function labelTable(value) {
  return tableLabels[value] || valueOrDash(value);
}

function labelField(value) {
  return fieldLabels[value] || valueOrDash(value);
}

function labelGate(value) {
  return gateLabels[value] || valueOrDash(value);
}

function labelGateMessage(gate) {
  return gateMessages[gate.code] || gate.message || "";
}

function labelMode(value) {
  return modeLabels[value] || valueOrDash(value);
}

function labelDocumentType(value) {
  return { other: "其他", contract: "合約", invoice: "發票", approval: "核准文件" }[value] || valueOrDash(value);
}

function money(value) {
  return Number(value || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function activateCaseTab(tabName) {
  for (const tab of caseTabs) {
    tab.classList.toggle("active", tab.dataset.caseTab === tabName);
  }
  for (const panel of casePanels) {
    const isActive = panel.dataset.casePanel === tabName;
    panel.hidden = !isActive;
    panel.classList.toggle("active", isActive);
  }
}

function activateModuleCard(card) {
  if (!card || card.hidden) return;
  const targetId = card.getAttribute("href")?.replace("#", "");
  for (const moduleCard of moduleCards) {
    moduleCard.classList.toggle("active", moduleCard === card);
  }
  for (const panel of modulePanels) {
    const isActive = panel.id === targetId;
    panel.hidden = !isActive;
    panel.classList.toggle("active-module", isActive);
  }
  for (const extra of moduleExtras) {
    const isActive = extra.dataset.moduleParent === targetId;
    extra.hidden = !isActive;
  }
  window.scrollTo({ top: 0, left: 0, behavior: "instant" });
}

function rolesForCard(card) {
  return (card.dataset.roles || "cio manager_assistant handler").split(/\s+/).filter(Boolean);
}

function applyRoleVisibility(user) {
  const allowedModules = new Set(user.allowed_modules || []);
  for (const card of moduleCards) {
    const targetId = card.getAttribute("href")?.replace("#", "");
    const allowedByPolicy = allowedModules.size ? allowedModules.has(targetId) : rolesForCard(card).includes(user.role_code);
    card.hidden = !allowedByPolicy;
  }
  const visibleCards = moduleCards.filter((card) => !card.hidden);
  const defaultCard =
    visibleCards.find((card) => card.getAttribute("href") === `#${user.default_module}`) || visibleCards[0];
  if (defaultCard) {
    activateModuleCard(defaultCard);
  }
}

function showLogin(message = "") {
  currentUser = null;
  loginShell.hidden = false;
  appShell.hidden = true;
  loginUser.hidden = true;
  logoutButton.hidden = true;
  loginUser.textContent = "";
  loginError.hidden = !message;
  loginError.textContent = message;
  loginForm.elements.username.focus();
}

async function showApp(user) {
  currentUser = user;
  loginShell.hidden = true;
  appShell.hidden = false;
  loginUser.hidden = false;
  logoutButton.hidden = false;
  loginUser.textContent = `登入身分：${user.role_name}（${user.username}）`;
  loginError.hidden = true;
  applyRoleVisibility(user);
  await refresh();
}

async function initializeSession() {
  try {
    const payload = await api("/api/auth/me");
    await showApp(payload.data);
  } catch (_error) {
    showLogin();
  }
}

async function submitLogin(event) {
  event.preventDefault();
  loginError.hidden = true;
  const formData = new FormData(loginForm);
  try {
    const payload = await api("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: formData.get("username"),
        password: formData.get("password"),
      }),
    });
    await showApp(payload.data);
  } catch (error) {
    showLogin(error.message);
  }
}

async function logout() {
  await api("/api/auth/logout", { method: "POST" });
  showLogin();
}

function activateDrillTarget(card) {
  const targetId = card.dataset.drillTarget;
  const target = targetId ? document.getElementById(targetId) : null;
  if (!target) return;

  for (const activeTarget of document.querySelectorAll(".drill-highlight")) {
    activeTarget.classList.remove("drill-highlight");
  }
  target.classList.add("drill-highlight");
  target.scrollIntoView({ block: "center", behavior: "smooth" });
  target.focus({ preventScroll: true });
}

function parseImportRows(value) {
  const parsed = JSON.parse(value);
  if (!Array.isArray(parsed) || parsed.some((row) => row === null || typeof row !== "object" || Array.isArray(row))) {
    throw new Error("資料列 JSON 必須是物件陣列。");
  }
  return parsed;
}

function renderWarning(warning) {
  return `
    <li class="import-warning ${escapeHtml(warning.severity)}">
      <strong>${escapeHtml(labelGate(warning.code))}</strong>
      <span>${escapeHtml(warning.message)}</span>
      <small>第 ${escapeHtml(warning.row_number)} 列 / ${escapeHtml(labelField(warning.source_field))}</small>
    </li>
  `;
}

function warningMatchesFilter(warning) {
  const severityMatches = importWarningFilter.severity === "all" || warning.severity === importWarningFilter.severity;
  const codeMatches = importWarningFilter.code === "all" || warning.code === importWarningFilter.code;
  return severityMatches && codeMatches;
}

function renderWarningFilters(warnings) {
  const codes = [...new Set(warnings.map((warning) => warning.code))].sort();
  return `
    <div class="filter-bar" data-warning-filters>
      <label>
        嚴重度
        <select id="warning-severity-filter">
          <option value="all"${importWarningFilter.severity === "all" ? " selected" : ""}>全部</option>
          <option value="error"${importWarningFilter.severity === "error" ? " selected" : ""}>錯誤</option>
          <option value="warning"${importWarningFilter.severity === "warning" ? " selected" : ""}>警示</option>
        </select>
      </label>
      <label>
        檢核項目
        <select id="warning-code-filter">
          <option value="all"${importWarningFilter.code === "all" ? " selected" : ""}>全部</option>
          ${codes
            .map((code) => `<option value="${escapeHtml(code)}"${importWarningFilter.code === code ? " selected" : ""}>${escapeHtml(labelGate(code))}</option>`)
            .join("")}
        </select>
      </label>
      <span>顯示 ${escapeHtml(warnings.filter(warningMatchesFilter).length)} / ${escapeHtml(warnings.length)} 筆</span>
    </div>
  `;
}

function renderImportPreview(preview) {
  const warnings = preview.rows.flatMap((row) => row.warnings || []);
  const visibleWarnings = warnings.filter(warningMatchesFilter);
  const unmapped = preview.rows.flatMap((row) =>
    (row.unmapped_fields || []).map((field) => ({ row_number: row.row_number, ...field })),
  );
  const summary = preview.summary;
  importPreviewResult.innerHTML = `
    <div class="import-summary" data-import-summary>
      <span>資料列 <strong>${escapeHtml(preview.row_count)}</strong></span>
      <span>候選欄位 <strong>${escapeHtml(summary.candidate_count)}</strong></span>
      <span>需確認 <strong>${escapeHtml(summary.requires_confirmation_count)}</strong></span>
      <span>警示 <strong>${escapeHtml(summary.warning_count)}</strong></span>
      <span>錯誤 <strong>${escapeHtml(summary.error_count)}</strong></span>
    </div>
    ${renderWarningFilters(warnings)}
    <div class="import-preview-grid">
      <section>
        <h3>檢核訊息</h3>
        ${
          visibleWarnings.length
            ? `<ul class="import-warning-list">${visibleWarnings.map(renderWarning).join("")}</ul>`
            : `<p class="muted">目前篩選條件沒有檢核訊息。</p>`
        }
      </section>
      <section>
        <h3>尚未對應欄位</h3>
        ${
          unmapped.length
            ? `<ul class="import-warning-list">${unmapped
                .map(
                  (field) => `
                    <li>
                      <strong>${escapeHtml(field.source_field)}</strong>
                      <span>${escapeHtml(valueOrDash(field.value))}</span>
                      <small>第 ${escapeHtml(field.row_number)} 列</small>
                    </li>
                  `,
                )
                .join("")}</ul>`
            : `<p class="muted">沒有尚未對應欄位。</p>`
        }
      </section>
    </div>
  `;
  dryRunCases.disabled = false;
  preflightCases.disabled = false;
}

function confirmedCaseFields(preview) {
  return preview.rows.flatMap((row) =>
    row.candidates
      .filter((candidate) => candidate.target_table === "cases" && candidate.requires_confirmation)
      .map((candidate) => ({
        row_number: row.row_number,
        target_table: "cases",
        target_field: candidate.target_field,
      })),
  );
}

function renderDryRunPlan(data) {
  const rows = data.plan.cases || [];
  const batchId = data.preview?.batch?.id || "-";
  const mappingVersion = "draft-v1";
  const totalAmount = rows.reduce((sum, row) => sum + Number(row.record.amount || 0), 0);
  dryRunResult.innerHTML = `
    <div class="import-summary" data-dry-run-plan>
      <span>模式 <strong>試算</strong></span>
      <span>資料表 <strong>案件</strong></span>
      <span>預計新增 <strong>${escapeHtml(data.summary.planned_create_count)}</strong></span>
      <span>正式寫入 <strong>0</strong></span>
      <span>總金額 <strong>${escapeHtml(money(totalAmount))} 元</strong></span>
      <span>批次 <strong>${escapeHtml(batchId)}</strong></span>
      <span>對應版本 <strong>${escapeHtml(mappingVersion)}</strong></span>
    </div>
    ${
      rows.length
        ? `<div class="mapping-list">${rows
            .map(
              (row) => `
                <article class="mapping-row" data-source-row-id="${escapeHtml(row.source_row_id)}">
                  <strong>${escapeHtml(row.record.case_code)}</strong>
                  <span>${escapeHtml(row.record.title)}</span>
                  <span>負責人 ${escapeHtml(valueOrDash(row.record.owner))}</span>
                  <span class="amount">金額 ${escapeHtml(money(row.record.amount))} 元</span>
                  <small>批次 ${escapeHtml(batchId)} / 第 ${escapeHtml(row.row_number)} 列 / 來源列 #${escapeHtml(row.source_row_id)} / 對應版本 ${escapeHtml(mappingVersion)}</small>
                </article>
              `,
            )
            .join("")}</div>`
        : `<p class="muted">本次試算沒有案件資料列。</p>`
    }
  `;
}

async function submitDryRunCases() {
  if (!lastImportBatchId || !lastImportPreview) {
    dryRunResult.innerHTML = `<p class="error">請先執行匯入預覽，再做案件試算。</p>`;
    return;
  }
  dryRunCases.disabled = true;
  dryRunResult.innerHTML = `<p class="muted">正在準備案件試算...</p>`;
  try {
    const payload = await api(`/api/import-batches/${lastImportBatchId}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dry_run: true,
        target_tables: ["cases"],
        confirmed_fields: confirmedCaseFields(lastImportPreview),
      }),
    });
    renderDryRunPlan(payload.data);
  } catch (error) {
    dryRunResult.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  } finally {
    dryRunCases.disabled = false;
  }
}

function renderPreflightReport(data) {
  const gates = data.gates || [];
  const blocked = gates.filter((gate) => gate.status === "blocked");
  const requirements = data.source_chain_requirements || [];
  const freshness = data.freshness || {};
  const summary = data.summary || {};
  preflightResult.innerHTML = `
    <div class="import-summary" data-preflight-report>
      <span>模式 <strong>正式寫入前檢核</strong></span>
      <span>正式寫入 <strong>${data.formal_write_allowed ? "允許" : "阻擋"}</strong></span>
      <span>寫入筆數 <strong>0</strong></span>
      <span>下一步 <strong>${escapeHtml(data.next_allowed_action || "-")}</strong></span>
      <span>阻擋項目 <strong>${escapeHtml(blocked.length)}</strong></span>
      <span>資料表 <strong>${escapeHtml((data.target_tables || []).map(labelTable).join(", ") || "-")}</strong></span>
      <span>對應版本 <strong>${escapeHtml(freshness.mapping_version || data.mapping_version || "-")}</strong></span>
      <span>資料列 <strong>${escapeHtml(summary.row_count || data.preview?.row_count || 0)}</strong></span>
      <span>錯誤 <strong>${escapeHtml(summary.error_count || 0)}</strong></span>
    </div>
    <div class="preflight-grid">
      <section>
        <h3>檢核閘門</h3>
        ${
          gates.length
            ? `<ul class="import-warning-list">${gates
                .map(
                  (gate) => `
                    <li class="preflight-gate ${escapeHtml(gate.status)}" data-gate-code="${escapeHtml(gate.code)}" data-gate-status="${escapeHtml(gate.status)}">
                      <strong>${escapeHtml(labelGate(gate.code))}</strong>
                      <span>${escapeHtml(labelStatus(gate.status))}</span>
                      <small>${escapeHtml(labelGateMessage(gate))}</small>
                      ${renderGateEvidence(gate.evidence)}
                    </li>
                  `,
                )
                .join("")}</ul>`
            : `<p class="muted">沒有回傳檢核閘門。</p>`
        }
      </section>
      <section>
        <h3>來源舉證鏈</h3>
        ${
          requirements.length
            ? `<ul class="import-warning-list">${requirements.map((item) => `<li>${escapeHtml(labelGate(item))}</li>`).join("")}</ul>`
            : `<p class="muted">沒有來源舉證鏈要求。</p>`
        }
      </section>
      <section>
        <h3>版本新鮮度</h3>
        <ul class="import-warning-list">
          <li>
            <strong>${escapeHtml(labelGate(freshness.strategy || "-"))}</strong>
            <span>伺服器重新檢核：${freshness.server_preview_rerun ? "是" : "否"}</span>
            <small>指紋 ${escapeHtml(freshness.fingerprint || "-")}</small>
          </li>
        </ul>
      </section>
    </div>
  `;
}

function renderGateEvidence(evidence) {
  const entries = Object.entries(evidence || {})
    .map(([key, value]) => [key, summarizeEvidenceValue(value)])
    .filter(([, value]) => value !== "");
  if (!entries.length) {
    return "";
  }
  return `<small class="gate-evidence">證據：${entries
    .map(([key, value]) => `${escapeHtml(key)}: ${escapeHtml(value)}`)
    .join(" / ")}</small>`;
}

function summarizeEvidenceValue(value) {
  if (Array.isArray(value)) {
    if (!value.length) return "0";
    if (value.every((item) => typeof item !== "object" || item === null)) {
      return value.join(", ");
    }
    return `${value.length} 筆`;
  }
  if (value && typeof value === "object") {
    return JSON.stringify(value);
  }
  if (value === null || value === undefined || value === "") {
    return "";
  }
  return String(value);
}

async function submitPreflightCases() {
  if (!lastImportBatchId || !lastImportPreview) {
    preflightResult.innerHTML = `<p class="error">請先執行匯入預覽，再做正式寫入前檢核。</p>`;
    return;
  }
  preflightCases.disabled = true;
  preflightResult.innerHTML = `<p class="muted">正在檢查案件正式寫入前閘門...</p>`;
  try {
    const payload = await api(`/api/import-batches/${lastImportBatchId}/confirm-preflight`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_tables: ["cases"],
        accepted_warning_codes: [],
        confirmed_fields: confirmedCaseFields(lastImportPreview),
      }),
    });
    renderPreflightReport(payload.data);
  } catch (error) {
    preflightResult.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  } finally {
    preflightCases.disabled = false;
  }
}

function renderMappingCatalog(catalog) {
  const tableCounts = Object.entries(catalog.target_tables || {})
    .map(([table, count]) => `<span>${escapeHtml(labelTable(table))} <strong>${escapeHtml(count)}</strong></span>`)
    .join("");
  const rows = catalog.fields
    .map(
      (field) => `
        <article class="mapping-row">
          <strong>${escapeHtml(field.source_field)}</strong>
          <span>${escapeHtml(labelTable(field.target_table))}.${escapeHtml(labelField(field.target_field))}</span>
          <span>${escapeHtml(labelMode(field.mode))}</span>
          <span>${field.requires_confirmation ? "需確認" : "自動"}</span>
          <span>${escapeHtml(Math.round(Number(field.confidence || 0) * 100))}%</span>
          <small>${escapeHtml((field.aliases || []).join(", ") || "-")}</small>
        </article>
      `,
    )
    .join("");
  mappingCatalogResult.innerHTML = `
    <div class="import-summary" data-mapping-summary>
      <span>欄位 <strong>${escapeHtml(catalog.field_count)}</strong></span>
      <span>需確認 <strong>${escapeHtml(catalog.requires_confirmation_count)}</strong></span>
      ${tableCounts}
    </div>
    <div class="mapping-list">${rows}</div>
  `;
}

async function loadMappingCatalog() {
  mappingCatalogResult.innerHTML = `<p class="muted">正在載入欄位對應草稿...</p>`;
  try {
    const payload = await api("/api/import-mapping-draft");
    renderMappingCatalog(payload.data);
  } catch (error) {
    mappingCatalogResult.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  }
}

async function submitImportPreview(event) {
  event.preventDefault();
  importPreviewResult.innerHTML = `<p class="muted">正在準備匯入預覽...</p>`;
  dryRunCases.disabled = true;
  preflightCases.disabled = true;
  dryRunResult.innerHTML = "";
  preflightResult.innerHTML = "";
  try {
    const formData = new FormData(importPreviewForm);
    const rows = parseImportRows(formData.get("rows_json"));
    const batchPayload = await api("/api/import-batches", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_name: formData.get("source_name") }),
    });
    await api(`/api/import-batches/${batchPayload.data.id}/rows`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows }),
    });
    lastImportBatchId = batchPayload.data.id;
    const previewPayload = await api(`/api/import-batches/${lastImportBatchId}/mapping-preview`);
    lastImportPreview = previewPayload.data;
    importWarningFilter = { severity: "all", code: "all" };
    renderImportPreview(lastImportPreview);
  } catch (error) {
    importPreviewResult.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  }
}

importPreviewResult.addEventListener("change", (event) => {
  if (!lastImportPreview) return;
  if (event.target.id === "warning-severity-filter") {
    importWarningFilter.severity = event.target.value;
    renderImportPreview(lastImportPreview);
  }
  if (event.target.id === "warning-code-filter") {
    importWarningFilter.code = event.target.value;
    renderImportPreview(lastImportPreview);
  }
});

function emptyList(label) {
  return `<p class="muted">目前沒有${label}資料。</p>`;
}

async function loadDashboard() {
  const payload = await api("/api/dashboard");
  const data = payload.data;
  metrics.innerHTML = [
    metric("案件", data.counts.cases),
    metric("合約", data.counts.contracts),
    metric("付款", data.counts.payments),
    metric("文件", data.counts.documents),
  ].join("");
}

async function loadCases() {
  const payload = await api("/api/cases");
  caseCache = payload.data;
  cases.innerHTML = caseCache.length
    ? caseCache
        .map(
          (item) => `
            <article class="row" data-case-id="${item.id}">
              <strong>${escapeHtml(item.case_code)}</strong>
              <span>${escapeHtml(item.title)}</span>
              <span class="muted">${escapeHtml(item.owner || "未指派")}</span>
              <span>${escapeHtml(item.status)}</span>
              <span class="actions">
                <button type="button" class="secondary" data-action="edit">編輯</button>
                <button type="button" class="secondary" data-action="disable">停用</button>
                <button type="button" class="danger" data-action="delete">刪除</button>
              </span>
            </article>
          `,
        )
        .join("")
    : `<p class="muted">目前沒有案件資料。</p>`;
}

async function loadResource(type) {
  const config = resourceConfig[type];
  const payload = await api(config.api);
  resourceCaches[type] = payload.data;
  resourceLists[type].innerHTML = payload.data.length
    ? payload.data.map((item) => renderResourceRow(type, item)).join("")
    : emptyList(config.plural);
}

function renderResourceRow(type, item) {
  const config = resourceConfig[type];
  const disableButton = config.canDisable
    ? `<button type="button" class="secondary" data-action="disable" data-resource-id="${item.id}">停用</button>`
    : "";
  return `
    <article class="mini-row" data-${config.idAttr}="${item.id}">
      ${config.render(item)}
      <span class="actions">
        <button type="button" class="secondary" data-action="edit" data-resource-id="${item.id}">編輯</button>
        ${disableButton}
        <button type="button" class="danger" data-action="delete" data-resource-id="${item.id}">刪除</button>
      </span>
    </article>
  `;
}

async function loadContracts() {
  await loadResource("contract");
}

async function loadPayments() {
  await loadResource("payment");
}

async function loadDocuments() {
  await loadResource("document");
}

async function refresh() {
  await Promise.all([loadDashboard(), loadCases(), loadContracts(), loadPayments(), loadDocuments(), loadMappingCatalog()]);
}

function resetForm() {
  form.reset();
  form.elements.id.value = "";
  formTitle.textContent = "新增案件";
  submitCase.textContent = "新增";
  cancelEdit.hidden = true;
}

function startEdit(id) {
  const item = caseCache.find((entry) => String(entry.id) === String(id));
  if (!item) return;
  form.elements.id.value = item.id;
  form.elements.case_code.value = item.case_code;
  form.elements.title.value = item.title;
  form.elements.owner.value = item.owner || "";
  form.elements.amount.value = item.amount || 0;
  form.elements.status.value = item.status || "draft";
  form.elements.note.value = item.note || "";
  form.elements.next_step.value = item.next_step || "";
  formTitle.textContent = `編輯 ${item.case_code}`;
  submitCase.textContent = "儲存";
  cancelEdit.hidden = false;
}

function serializeResourceForm(type) {
  const config = resourceConfig[type];
  const targetForm = resourceForms[type];
  const data = Object.fromEntries(new FormData(targetForm).entries());
  const id = data.id;
  delete data.id;
  for (const field of config.numberFields) {
    data[field] = data[field] === "" ? null : Number(data[field]);
  }
  return { id, data };
}

function resetResourceForm(type) {
  const targetForm = resourceForms[type];
  targetForm.reset();
  targetForm.elements.id.value = "";
  targetForm.querySelector('button[type="submit"]').textContent = "新增";
  targetForm.querySelector("[data-cancel]").hidden = true;
}

async function startResourceEdit(type, id) {
  let item = resourceCaches[type].find((entry) => String(entry.id) === String(id));
  if (!item) {
    await loadResource(type);
    item = resourceCaches[type].find((entry) => String(entry.id) === String(id));
  }
  if (!item) return;
  const config = resourceConfig[type];
  const targetForm = resourceForms[type];
  targetForm.elements.id.value = item.id;
  for (const field of config.fields) {
    targetForm.elements[field].value = item[field] ?? "";
  }
  targetForm.querySelector('button[type="submit"]').textContent = "儲存";
  targetForm.querySelector("[data-cancel]").hidden = false;
}

async function submitResource(type, event) {
  event.preventDefault();
  const config = resourceConfig[type];
  const { id, data } = serializeResourceForm(type);
  await api(id ? `${config.api}/${id}` : config.api, {
    method: id ? "PATCH" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  resetResourceForm(type);
  await refresh();
}

async function handleResourceAction(type, event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const config = resourceConfig[type];
  const row = button.closest(`[data-${config.idAttr}]`);
  const id = button.getAttribute("data-resource-id") || row?.getAttribute(`data-${config.idAttr}`);
  if (!id) return;
  const action = button.dataset.action;
  if (action === "edit") {
    await startResourceEdit(type, id);
    return;
  }
  if (action === "disable") {
    await api(`${config.api}/${id}/disable`, { method: "POST" });
  }
  if (action === "delete") {
    await api(`${config.api}/${id}`, { method: "DELETE" });
  }
  resetResourceForm(type);
  await refresh();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());
  const id = data.id;
  delete data.id;
  data.amount = Number(data.amount || 0);
  await api(id ? `/api/cases/${id}` : "/api/cases", {
    method: id ? "PATCH" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  resetForm();
  await refresh();
});

cases.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const row = button.closest("[data-case-id]");
  const id = row.dataset.caseId;
  const action = button.dataset.action;
  if (action === "edit") {
    startEdit(id);
    return;
  }
  if (action === "disable") {
    await api(`/api/cases/${id}/disable`, { method: "POST" });
  }
  if (action === "delete") {
    await api(`/api/cases/${id}`, { method: "DELETE" });
  }
  resetForm();
  await refresh();
});

for (const type of Object.keys(resourceForms)) {
  resourceForms[type].addEventListener("submit", (event) => submitResource(type, event));
  resourceForms[type].querySelector("[data-cancel]").addEventListener("click", () => resetResourceForm(type));
  resourceLists[type].addEventListener("click", (event) => handleResourceAction(type, event));
}

for (const tab of caseTabs) {
  tab.addEventListener("click", () => activateCaseTab(tab.dataset.caseTab));
}

for (const card of moduleCards) {
  card.addEventListener("click", (event) => {
    event.preventDefault();
    activateModuleCard(card);
  });
}

for (const card of drillCards) {
  card.addEventListener("click", () => activateDrillTarget(card));
  card.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    activateDrillTarget(card);
  });
}

loginForm.addEventListener("submit", submitLogin);
logoutButton.addEventListener("click", logout);
cancelEdit.addEventListener("click", resetForm);
importPreviewForm.addEventListener("submit", submitImportPreview);
dryRunCases.addEventListener("click", submitDryRunCases);
preflightCases.addEventListener("click", submitPreflightCases);
refreshMappingCatalog.addEventListener("click", loadMappingCatalog);
initializeSession().catch((error) => {
  cases.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  contracts.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  payments.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  documents.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
});
