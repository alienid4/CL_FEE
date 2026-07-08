// 前端建置版本／日期（單一來源）。每次改前端就 bump 這裡＋index.html 的 ?v=。
// 徽章同時顯示前端(這裡)與後端(/health 的 build)日期；兩者對不上＝後端沒重啟，會亮警告。
const BUILD_TAG = "2026-07-09 · 進度總表匯入";
(async () => {
  const badge = document.querySelector("#build-badge");
  if (!badge) return;
  const shortDate = (s) => (String(s).match(/\d{4}-(\d{2}-\d{2})/) || [, "?"])[1];
  const front = shortDate(BUILD_TAG);
  badge.textContent = `前端 ${front} ｜ 後端 …`;
  try {
    const h = await fetch("/health", { credentials: "same-origin" }).then((r) => r.json());
    const back = shortDate(h.build || "");
    const mismatch = front !== back;
    badge.textContent = `前端 ${front} ｜ 後端 ${back}`;
    badge.classList.toggle("mismatch", mismatch);
    badge.title = mismatch
      ? `前後端版本不一致：前端 ${BUILD_TAG}、後端 ${h.build || "未知"}。請重啟 uvicorn 後端。`
      : `版本一致（${BUILD_TAG}）`;
  } catch (_e) {
    badge.textContent = `前端 ${front} ｜ 後端 ?`;
  }
})();

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
const budgetsList = document.querySelector("#budgets");
const projectsList = document.querySelector("#projects-list");
const signoffsList = document.querySelector("#signoffs");
const purchasesList = document.querySelector("#purchases-list");
const form = document.querySelector("#case-form");
const todoList = document.querySelector("#todo-list");
const cioCasesBody = document.querySelector("#cio-cases-body");
const cioMetrics = document.querySelector("#cio-metrics");
const cioUpcomingBody = document.querySelector("#cio-upcoming-body");
const cioDrill = document.querySelector("#cio-drill");
const cioNextMonthLabel = document.querySelector("#cio-next-month-label");
const monthlyBody = document.querySelector("#monthly-spending-body");
const demoControls = document.querySelector("#demo-controls");
const demoSeed = document.querySelector("#demo-seed");
const demoClear = document.querySelector("#demo-clear");
const demoStatus = document.querySelector("#demo-status");
const setText = (sel, txt) => { const el = document.querySelector(sel); if (el) el.textContent = txt; };
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
const formalImportCases = document.querySelector("#formal-import-cases");
const formalImportResult = document.querySelector("#formal-import-result");
const preflightResult = document.querySelector("#preflight-result");
const caseTabs = [...document.querySelectorAll("[data-case-tab]")];
const casePanels = [...document.querySelectorAll("[data-case-panel]")];
const moduleCards = [...document.querySelectorAll(".module-card")];
const modulePanels = [...document.querySelectorAll(".module-panel")];
if (modulePanels.length && !document.querySelector("#module-unbuilt")) {
  const ph = document.createElement("section");
  ph.className = "module-panel";
  ph.id = "module-unbuilt";
  ph.hidden = true;
  ph.innerHTML =
    '<div class="watch-list"><div class="section-heading compact"><h2>此功能尚未啟用</h2></div>' +
    '<p class="muted">此模組（預算 / 專案 / 簽呈 / 請購）仍在規劃中，pilot 階段先不開放。核心流程請用「案件管理」。</p></div>';
  modulePanels[0].parentNode.appendChild(ph);
  modulePanels.push(ph);
}
const moduleExtras = [...document.querySelectorAll("[data-module-parent]")];
const drillCards = [...document.querySelectorAll("[data-drill-target]")];
let lastImportPreview = null;
let lastImportBatchId = null;
let importWarningFilter = { severity: "all", code: "all" };
const resourceForms = {
  contract: document.querySelector("#contract-form"),
  payment: document.querySelector("#payment-form"),
  document: document.querySelector("#document-form"),
  budget: document.querySelector("#budget-form"),
  project: document.querySelector("#project-form"),
  signoff: document.querySelector("#signoff-form"),
  purchase: document.querySelector("#purchase-form"),
};
const resourceLists = {
  contract: contracts, payment: payments, document: documents,
  budget: budgetsList, project: projectsList, signoff: signoffsList, purchase: purchasesList,
};
const resourceCaches = {
  contract: [], payment: [], document: [],
  budget: [], project: [], signoff: [], purchase: [],
};
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
  completed: "已完成",
  paused: "暫停",
  submitted: "送簽",
  rejected: "退回",
  ordered: "已下單",
  arrived: "已到貨",
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
    fields: ["contract_code", "contract_name", "vendor_name", "amount", "case_id", "status", "end_date"],
    numberFields: ["amount", "case_id"],
    canDisable: true,
    columns: [
      { label: "合約編號", cell: (i) => `<strong>${escapeHtml(i.contract_code)}</strong>` },
      { label: "合約名稱", cell: (i) => escapeHtml(i.contract_name) },
      { label: "廠商", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.vendor_name))}</span>` },
      { label: "金額", cls: "num", cell: (i) => `${money(i.amount)} 元` },
      { label: "到期日", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.end_date))}</span>` },
      { label: "狀態", cell: (i) => statusChip(i.status) },
    ],
  },
  payment: {
    plural: "payments",
    idAttr: "payment-id",
    idField: "paymentId",
    api: "/api/payments",
    fields: ["contract_id", "payment_month", "payment_amount", "invoice_status", "status",
             "item", "settle_no", "ref_no", "period", "billing_period", "settled_by",
             "vendor", "approval_level", "owner", "owner_email", "net_amount", "tax_amount"],
    numberFields: ["contract_id", "payment_amount", "net_amount", "tax_amount"],
    canDisable: true,
    columns: [
      { label: "核銷項目", cell: (i) => `<strong>${escapeHtml(valueOrDash(i.item) === "-" ? valueOrDash(i.payment_month) : i.item)}</strong>` },
      { label: "廠商", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.vendor))}</span>` },
      { label: "期間", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.payment_month))}${i.period ? "｜" + escapeHtml(i.period) : ""}</span>` },
      { label: "金額", cls: "num", cell: (i) => `${money(i.payment_amount)} 元` },
      { label: "發票", cell: (i) => escapeHtml(labelStatus(i.invoice_status)) },
      { label: "狀態", cell: (i) => statusChip(i.status) },
    ],
  },
  document: {
    plural: "documents",
    idAttr: "document-id",
    idField: "documentId",
    api: "/api/documents",
    fields: ["file_name", "document_type", "source_note", "status", "case_id", "contract_id"],
    numberFields: ["case_id", "contract_id"],
    canDisable: true,
    columns: [
      { label: "檔名", cell: (i) => `<strong>${escapeHtml(i.file_name)}</strong>` },
      { label: "類型", cell: (i) => escapeHtml(labelDocumentType(i.document_type)) },
      { label: "關聯", cell: (i) => `<span class="muted">案件 ${escapeHtml(valueOrDash(i.case_id))}／合約 ${escapeHtml(valueOrDash(i.contract_id))}</span>` },
      { label: "來源", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.source_note))}</span>` },
      { label: "狀態", cell: (i) => statusChip(i.status || "active") },
    ],
  },
  budget: {
    plural: "budgets", idAttr: "budget-id", idField: "budgetId", api: "/api/budgets",
    navCount: "nav-count-budgets", navLabel: "預算",
    fields: ["budget_code", "category", "unit_name", "fiscal_year", "amount", "status", "case_id", "note"],
    numberFields: ["amount", "case_id"], canDisable: true,
    columns: [
      { label: "預算編號", cell: (i) => `<strong>${escapeHtml(i.budget_code)}</strong>` },
      { label: "分類", cell: (i) => escapeHtml(valueOrDash(i.category)) },
      { label: "單位／年度", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.unit_name))}｜${escapeHtml(valueOrDash(i.fiscal_year))}</span>` },
      { label: "金額", cls: "num", cell: (i) => `${money(i.amount)} 元` },
      { label: "狀態", cell: (i) => statusChip(i.status) },
    ],
  },
  project: {
    plural: "projects", idAttr: "project-id", idField: "projectId", api: "/api/projects",
    navCount: "nav-count-projects", navLabel: "專案",
    fields: ["project_code", "project_name", "source", "necessity", "progress", "owner", "status", "case_id", "due_date", "note",
             "level", "progress_planned", "rag_status", "start_date", "end_date"],
    numberFields: ["progress", "progress_planned", "case_id"], canDisable: true,
    columns: [
      { label: "編號", cell: (i) => `<strong>${escapeHtml(i.project_code)}</strong>` },
      { label: "專案名稱", cell: (i) => escapeHtml(i.project_name) },
      { label: "層級", cell: (i) => escapeHtml(valueOrDash(i.level)) },
      { label: "必要性", cell: (i) => escapeHtml(valueOrDash(i.necessity)) },
      { label: "負責人", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.owner))}</span>` },
      { label: "進度（預計／實際）", cls: "num", cell: (i) => progressCell(i.progress_planned, i.progress) },
      { label: "燈號", cell: (i) => ragChip(valueOrDash(i.rag_status) === "-" ? labelStatus(i.status) : i.rag_status) },
    ],
  },
  signoff: {
    plural: "signoffs", idAttr: "signoff-id", idField: "signoffId", api: "/api/signoffs",
    navCount: "nav-count-signoffs", navLabel: "簽呈",
    fields: ["signoff_code", "subject", "applicant", "amount", "status", "sign_date", "case_id", "note"],
    numberFields: ["amount", "case_id"], canDisable: true,
    columns: [
      { label: "簽呈編號", cell: (i) => `<strong>${escapeHtml(i.signoff_code)}</strong>` },
      { label: "主旨", cell: (i) => escapeHtml(i.subject) },
      { label: "申請人", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.applicant))}</span>` },
      { label: "簽核日", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.sign_date))}</span>` },
      { label: "金額", cls: "num", cell: (i) => `${money(i.amount)} 元` },
      { label: "狀態", cell: (i) => statusChip(i.status) },
    ],
  },
  purchase: {
    plural: "purchases", idAttr: "purchase-id", idField: "purchaseId", api: "/api/purchases",
    navCount: "nav-count-purchases", navLabel: "請購",
    fields: ["purchase_code", "item_name", "vendor_name", "quantity", "amount", "status", "case_id", "note"],
    numberFields: ["quantity", "amount", "case_id"], canDisable: true,
    columns: [
      { label: "請購編號", cell: (i) => `<strong>${escapeHtml(i.purchase_code)}</strong>` },
      { label: "品項", cell: (i) => escapeHtml(i.item_name) },
      { label: "廠商", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.vendor_name))}</span>` },
      { label: "數量", cls: "num", cell: (i) => `${Number(i.quantity || 0)}` },
      { label: "金額", cls: "num", cell: (i) => `${money(i.amount)} 元` },
      { label: "狀態", cell: (i) => statusChip(i.status) },
    ],
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
  const targetId = ("unbuilt" in card.dataset) ? "module-unbuilt" : card.getAttribute("href")?.replace("#", "");
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
  // 示範資料工具只給主管/助理（有 edit）；CIO 唯讀、承辦被後端擋，也不顯示。
  if (demoControls) {
    demoControls.hidden = user.role_code !== "manager_assistant";
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

async function submitFormalImport() {
  if (!lastImportBatchId || !lastImportPreview) {
    if (formalImportResult) formalImportResult.innerHTML = `<p class="error">請先執行匯入預覽與案件試算。</p>`;
    return;
  }
  if (!window.confirm("確定正式匯入？將寫入資料庫（已存在的案件編號會跳過不覆蓋）。")) return;
  formalImportCases.disabled = true;
  formalImportResult.innerHTML = `<p class="muted">正在正式寫入...</p>`;
  try {
    const payload = await api(`/api/import-batches/${lastImportBatchId}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dry_run: false,
        target_tables: ["cases"],
        confirmed_fields: confirmedCaseFields(lastImportPreview),
      }),
    });
    const d = payload.data || {};
    formalImportResult.innerHTML = `<p class="ok">正式匯入完成：新增 ${d.created_count} 筆、跳過 ${d.skipped_count} 筆（已存在）。</p>`;
    await refresh();
  } catch (error) {
    formalImportResult.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  } finally {
    formalImportCases.disabled = false;
  }
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
  if (formalImportCases) formalImportCases.disabled = false;  // 試算完成才開放正式匯入
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
  setText("#nav-count-cases", `案件 ${data.counts.cases}`);
  setText("#nav-count-contracts", `合約 ${data.counts.contracts}`);
  setText("#nav-count-payments", `付款 ${data.counts.payments}`);
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
              <span class="badge ${item.status === "approved" ? "ok" : item.status === "pending_review" ? "warn" : item.status === "disabled" ? "neutral" : ""}">${escapeHtml(STATUS_LABELS[item.status] || item.status)}</span>
              <span class="actions">
                ${caseWorkflowButtons(item)}
                <button type="button" class="secondary" data-action="edit">編輯</button>
                <button type="button" class="secondary" data-action="disable">停用</button>
                <button type="button" class="danger" data-action="delete">刪除</button>
              </span>
            </article>
          `,
        )
        .join("")
    : `<p class="muted">目前沒有案件資料。</p>`;
  renderCioTable();
}

async function loadResource(type) {
  const config = resourceConfig[type];
  const payload = await api(config.api);
  resourceCaches[type] = payload.data;
  resourceLists[type].innerHTML = payload.data.length
    ? renderResourceTable(type, payload.data)
    : emptyList(config.plural);
  if (config.navCount) setText(`#${config.navCount}`, `${config.navLabel} ${payload.data.length}`);
}

// 表格化：一列一筆、欄位對齊，像 Excel 一樣掃視
function renderResourceTable(type, items) {
  const config = resourceConfig[type];
  const head = config.columns
    .map((c) => `<th${c.cls ? ` class="${c.cls}"` : ""}>${c.label}</th>`)
    .join("");
  const body = items.map((item) => renderResourceRow(type, item)).join("");
  return `
    <div class="grid-scroll">
      <table class="grid-table">
        <thead><tr>${head}<th class="col-actions">操作</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
    </div>
  `;
}

function renderResourceRow(type, item) {
  const config = resourceConfig[type];
  const cells = config.columns
    .map((c) => `<td${c.cls ? ` class="${c.cls}"` : ""}>${c.cell(item)}</td>`)
    .join("");
  return `<tr data-${config.idAttr}="${item.id}">${cells}<td class="col-actions">${renderRowMenu(config, item)}</td></tr>`;
}

// 編輯／停用／刪除收進單一下拉，省版面
function renderRowMenu(config, item) {
  const disableButton = config.canDisable
    ? `<button type="button" data-action="disable" data-resource-id="${item.id}">停用</button>`
    : "";
  return `
    <details class="row-menu">
      <summary>操作 ▾</summary>
      <div class="row-menu-pop">
        <button type="button" data-action="edit" data-resource-id="${item.id}">編輯</button>
        ${disableButton}
        <button type="button" class="danger" data-action="delete" data-resource-id="${item.id}">刪除</button>
      </div>
    </details>
  `;
}

// 狀態小徽章：核准/使用中=綠、停用=灰、待複核/審核=橘
function statusChip(value) {
  const s = String(value || "");
  const tone = (s === "approved" || s === "active")
    ? "ok"
    : s === "disabled"
      ? "neutral"
      : (s === "pending_review" || s === "reviewing")
        ? "warn"
        : "";
  return `<span class="badge ${tone}">${escapeHtml(labelStatus(value))}</span>`;
}

// 進度：預計 vs 實際，含一條迷你進度條
function progressCell(planned, actual) {
  const p = Number(planned || 0);
  const a = Number(actual || 0);
  const tone = a >= p ? "ok" : (p - a) >= 20 ? "danger" : "warn";
  return `<span class="progress-cell">
      <span class="progress-bar"><i class="progress-fill ${tone}" style="width:${Math.min(100, Math.max(0, a))}%"></i></span>
      <span class="progress-num">預計 ${p}%／實際 ${a}%</span>
    </span>`;
}

// 燈號：只認紅/黃/綠或 R/A/G；認不出來（空、數字、雜訊）一律顯示 — 不秀原始值
function ragChip(value) {
  const v = String(value || "").trim();
  if (/紅|red|^r$/i.test(v)) return `<span class="badge danger">紅</span>`;
  if (/黃|橘|amber|^a$/i.test(v)) return `<span class="badge warn">黃</span>`;
  if (/綠|green|^g$/i.test(v)) return `<span class="badge ok">綠</span>`;
  return `<span class="muted">—</span>`;
}

// ===== 專案進度總表（Portfolio）：組別主 tab → 本組總覽＋各專案子 tab =====
const portfolioState = { g: 0, s: "ov" };
let portfolioGroups = [];

// 依起訖日算「今天該到的進度」，與實際比出落後幅度；沒日期就退回用「預計%」
function pfStatus(p) {
  const actual = Number(p.progress || 0);
  const planned = Number(p.progress_planned || 0);
  let expected = planned, hasDates = false, days = null;
  const s = p.start_date, e = p.end_date;
  if (s && e) {
    const ds = new Date(s), de = new Date(e), now = new Date();
    if (!Number.isNaN(ds.getTime()) && !Number.isNaN(de.getTime()) && de > ds) {
      hasDates = true;
      const tf = Math.max(0, Math.min(1, (now - ds) / (de - ds)));
      expected = Math.round(tf * 100);
      days = Math.round((de - now) / 86400000);
    }
  }
  const noBasis = !hasDates && planned <= 0;  // 既無起訖日、也無預計% → 沒有比對基準
  const gap = expected - actual;
  let st, label;
  if (actual >= 100) { st = "ok"; label = "完成"; }
  else if (noBasis) { st = "muted"; label = "未排程"; }
  else if (gap <= 2) { st = "ok"; label = actual > expected + 8 ? "超前" : "準時"; }
  else if (gap <= 18) { st = "warn"; label = "落後 " + Math.round(gap) + "%"; }
  else { st = "danger"; label = "落後 " + Math.round(gap) + "%"; }
  return { actual, planned, expected, gap, tone: st, label, hasDates, days, noBasis };
}

// 單條進度：填色＝實際%，黑記號＝今天該到的進度（無比對基準時不畫記號）
function pfBar(p, c) {
  const mark = (c.noBasis || Number(p.progress || 0) >= 100)
    ? ""
    : `<i class="pf-mark" style="left:${Math.min(100, Math.max(0, c.expected))}%"></i>`;
  return `<span class="pf-bar"><i class="pf-fill ${c.tone}" style="width:${Math.min(100, Math.max(0, c.actual))}%"></i>${mark}</span>`;
}

function pfOverview(group) {
  const rows = group.projects.map((p) => {
    const c = pfStatus(p);
    return `
      <div class="pf-row" data-pf-proj="${p.id}" title="點此看單一專案">
        <span class="pf-row-name"><span class="pf-dot ${c.tone}"></span>${escapeHtml(p.project_name)}</span>
        ${pfBar(p, c)}
        <span class="pf-row-tag"><span class="badge ${c.tone}">${escapeHtml(c.label)}</span></span>
      </div>`;
  }).join("");
  return `<div class="pf-card"><div class="muted pf-card-head">${escapeHtml(group.name)}　全部專案（共 ${group.projects.length} 個）</div>${rows}</div>`;
}

function pfDetail(p) {
  const c = pfStatus(p);
  const metas = [
    ["負責人", valueOrDash(p.owner)],
    ["開始", valueOrDash(p.start_date)],
    ["結束", valueOrDash(p.end_date)],
    ["剩餘", c.hasDates ? (c.days >= 0 ? c.days + " 天" : "逾期 " + (-c.days) + " 天") : "—"],
  ];
  const metaHtml = metas.map(([k, v]) =>
    `<div class="pf-meta"><span class="pf-meta-k">${k}</span><span class="pf-meta-v${k === "剩餘" && c.hasDates && c.days < 0 ? " pf-danger" : ""}">${escapeHtml(v)}</span></div>`).join("");
  const hint = c.hasDates ? "" : `<span class="muted pf-hint">未設定起訖日，落後以「預計%」估算</span>`;
  return `
    <div class="pf-card pf-detail">
      <div class="pf-detail-head">
        <span class="pf-detail-title"><span class="pf-dot ${c.tone}"></span>${escapeHtml(p.project_name)}</span>
        <span class="badge ${c.tone}">${escapeHtml(c.label)}</span>
      </div>
      <div class="pf-metas">${metaHtml}</div>
      <div class="pf-prog-line"><span>預計 <b>${c.expected}%</b></span><span>實際 <b class="pf-${c.tone}">${c.actual}%</b></span>${hint}</div>
      ${pfBar(p, c)}
      <div class="pf-note">${escapeHtml(valueOrDash(p.note))}</div>
    </div>`;
}

function pfSubPill(label, active, dot) {
  const d = dot ? `<span class="pf-dot ${dot}"></span>` : "";
  return `<span class="pf-pill${active ? " active" : ""}">${d}${escapeHtml(label)}</span>`;
}

function renderPortfolio() {
  const groupsEl = document.querySelector("#pf-groups");
  const subsEl = document.querySelector("#pf-subs");
  const viewEl = document.querySelector("#pf-view");
  if (!groupsEl || !subsEl || !viewEl) return;
  if (!portfolioGroups.length) {
    groupsEl.innerHTML = "";
    subsEl.innerHTML = "";
    viewEl.innerHTML = `<p class="muted">目前沒有專案資料。可到「專案」模組新增，或用 Excel 匯入。</p>`;
    return;
  }
  if (portfolioState.g >= portfolioGroups.length) portfolioState.g = 0;
  const group = portfolioGroups[portfolioState.g];
  groupsEl.innerHTML = portfolioGroups.map((g, i) =>
    `<button type="button" class="pf-gtab${i === portfolioState.g ? " active" : ""}" data-pf-g="${i}">${escapeHtml(g.name)} <span class="pf-gcount">${g.projects.length}</span></button>`).join("");
  const subs = [`<span data-pf-s="ov">${pfSubPill("本組總覽", portfolioState.s === "ov")}</span>`];
  group.projects.forEach((p, i) => {
    const c = pfStatus(p);
    subs.push(`<span data-pf-s="${i}">${pfSubPill(p.project_name, portfolioState.s === i, c.tone)}</span>`);
  });
  subsEl.innerHTML = subs.join("");
  viewEl.innerHTML = portfolioState.s === "ov" ? pfOverview(group) : pfDetail(group.projects[portfolioState.s]);
}

async function loadPortfolio() {
  if (!document.querySelector("#pf-view")) return;
  const payload = await api("/api/projects");
  const byGroup = new Map();
  for (const p of payload.data || []) {
    const key = (p.source && String(p.source).trim()) || "未分組";
    if (!byGroup.has(key)) byGroup.set(key, []);
    byGroup.get(key).push(p);
  }
  portfolioGroups = [...byGroup.entries()].map(([name, projects]) => ({ name, projects }));
  renderPortfolio();
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

const STATUS_LABELS = { draft: "草稿", pending_review: "待複核", reviewing: "審核中", approved: "已核准", disabled: "已停用" };

// 依角色/建立者算出案件的複核動作按鈕（送出複核 / 核准）
function caseWorkflowButtons(item) {
  const btns = [];
  if (item.status === "draft" || item.status === "reviewing") {
    btns.push(`<button type="button" class="secondary" data-action="submit">送出複核</button>`);
  }
  if (item.status === "pending_review" && currentUser && currentUser.role_code === "manager_assistant") {
    if ((item.created_by || "") === currentUser.username) {
      btns.push(`<span class="muted" title="不能核准自己建立的案件">待他人複核</span>`);
    } else {
      btns.push(`<button type="button" data-action="approve">核准</button>`);
    }
  }
  return btns.join(" ");
}

async function loadTodo() {
  if (!todoList) return;
  const payload = await api("/api/todo");
  const items = payload.data || [];
  setText("#nav-count-todo", `待辦 ${items.length}`);
  todoList.innerHTML = items.length
    ? items
        .map(
          (c) => `
            <li data-case-id="${c.id}" style="cursor:pointer" title="點此編輯此案件">
              <span class="badge ${c.status === "reviewing" ? "warn" : "ok"}">${STATUS_LABELS[c.status] || escapeHtml(c.status)}</span>
              <strong>${escapeHtml(c.case_code)}　${escapeHtml(c.title)}</strong>
              <small>備註：${escapeHtml(c.note || "—")}；下一步：${escapeHtml(c.next_step || "—")}；負責人：${escapeHtml(c.owner || "未指派")}</small>
            </li>`
        )
        .join("")
    : `<li><small class="muted">目前沒有需處理的案件。</small></li>`;
}

function renderCioTable() {
  if (!cioCasesBody) return;
  cioCasesBody.innerHTML = caseCache.length
    ? caseCache
        .map(
          (c, i) => `
            <tr data-case-id="${c.id}">
              <td>${i + 1}</td>
              <td>${escapeHtml(c.case_code)}</td>
              <td>${escapeHtml(c.title)}</td>
              <td><span class="badge ${c.status === "reviewing" || c.status === "pending_review" ? "warn" : c.status === "disabled" ? "neutral" : "ok"}">${STATUS_LABELS[c.status] || escapeHtml(c.status)}</span></td>
              <td>${Number(c.amount || 0).toLocaleString()}</td>
              <td>${escapeHtml(c.owner || "未指派")}</td>
              <td>${escapeHtml(c.note || "—")}</td>
              <td>${escapeHtml(c.next_step || "—")}</td>
              <td><button type="button" class="secondary" data-cio-edit>編輯</button></td>
            </tr>`
        )
        .join("")
    : `<tr><td colspan="9" class="muted">目前沒有案件資料。</td></tr>`;
}

async function loadMonthly() {
  if (!monthlyBody) return;
  const payload = await api("/api/reports/monthly-spending");
  const rows = payload.data || [];
  monthlyBody.innerHTML = rows.length
    ? rows
        .map(
          (r) => `
            <tr>
              <td>${escapeHtml(r.month)}</td>
              <td>${r.count}</td>
              <td>${Number(r.total || 0).toLocaleString()}</td>
              <td>${Number(r.paid || 0).toLocaleString()}</td>
              <td>${Number(r.pending || 0).toLocaleString()}</td>
            </tr>`
        )
        .join("")
    : `<tr><td colspan="5" class="muted">目前沒有付款資料。</td></tr>`;
}

async function loadExpiring() {
  const el = document.querySelector("#expiring-list");
  if (!el) return;
  const payload = await api("/api/reports/expiring-contracts");
  const items = payload.data || [];
  const today = new Date().toISOString().slice(0, 10);
  el.innerHTML = items.length
    ? items
        .map((c) => {
          const overdue = c.end_date && c.end_date < today;
          return `
            <li>
              <span class="badge ${overdue ? "danger" : "warn"}">${overdue ? "已過期" : "快到期"}</span>
              <strong>${escapeHtml(c.contract_code)}　${escapeHtml(c.contract_name)}</strong>
              <small>到期日：${escapeHtml(c.end_date)}；廠商：${escapeHtml(c.vendor_name || "—")}；金額：${Number(c.amount || 0).toLocaleString()}</small>
            </li>`;
        })
        .join("")
    : `<li><small class="muted">目前沒有快到期或已過期的合約。</small></li>`;
}

// ---- 內嵌 SVG 圖表（不依賴外部函式庫，離線可用）----
const CHART_COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2", "#64748b"];

function donutSVG(segments, { size = 132, thickness = 22, center = "" } = {}) {
  const pos = segments.filter((s) => s.value > 0);
  const total = pos.reduce((s, x) => s + x.value, 0);
  const r = (size - thickness) / 2;
  const cx = size / 2;
  const circ = 2 * Math.PI * r;
  let offset = 0;
  const rings = total
    ? pos
        .map((s) => {
          const dash = (s.value / total) * circ;
          const el = `<circle cx="${cx}" cy="${cx}" r="${r}" fill="none" stroke="${s.color}" stroke-width="${thickness}" stroke-dasharray="${dash.toFixed(2)} ${(circ - dash).toFixed(2)}" stroke-dashoffset="${(-offset).toFixed(2)}" transform="rotate(-90 ${cx} ${cx})"/>`;
          offset += dash;
          return el;
        })
        .join("")
    : "";
  return `<svg viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" role="img" aria-label="圓餅圖">
    <circle cx="${cx}" cy="${cx}" r="${r}" fill="none" stroke="#e5e7eb" stroke-width="${thickness}"/>${rings}
    ${center ? `<text x="${cx}" y="${cx}" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="600" fill="currentColor">${escapeHtml(center)}</text>` : ""}
  </svg>`;
}

function barsSVG(bars, { width = 300, height = 150 } = {}) {
  const max = Math.max(1, ...bars.map((b) => b.value));
  const n = bars.length || 1;
  const gap = 12;
  const bw = Math.max(8, (width - gap * (n + 1)) / n);
  const chartH = height - 26;
  const body = bars
    .map((b, i) => {
      const h = (b.value / max) * chartH;
      const x = gap + i * (bw + gap);
      const y = chartH - h;
      return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" rx="3" fill="${b.color || CHART_COLORS[0]}"/>
        <text x="${(x + bw / 2).toFixed(1)}" y="${height - 8}" text-anchor="middle" font-size="10" fill="currentColor">${escapeHtml(b.label)}</text>`;
    })
    .join("");
  return `<svg viewBox="0 0 ${width} ${height}" width="100%" height="${height}" role="img" aria-label="長條圖">${body}</svg>`;
}

function chartLegend(segments) {
  return `<ul style="list-style:none;margin:8px 0 0;padding:0;font-size:12px;display:flex;flex-wrap:wrap;gap:4px 12px;">${segments
    .map((s) => `<li style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:10px;border-radius:2px;background:${s.color};display:inline-block;"></span>${escapeHtml(s.label)}${s.text ? `：${escapeHtml(s.text)}` : ""}</li>`)
    .join("")}</ul>`;
}

function chartCard(title, inner) {
  return `<article class="chart-card" style="flex:1 1 240px;min-width:220px;border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;">
    <h3 style="margin:0 0 8px;font-size:14px;">${escapeHtml(title)}</h3>
    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">${inner}</div>
  </article>`;
}

async function loadCioOverview() {
  if (!cioMetrics) return;
  const payload = await api("/api/reports/cio-overview");
  const d = payload.data || {};
  const unplanned = d.unplanned_next_month || 0;
  const planned = Math.max(0, (d.next_month_total || 0) - unplanned);
  cioMetrics.innerHTML = [
    metric("下月應付", `${money(d.next_month_total)} 元`),
    metric("要準備的資金", `${money(d.funds_to_prepare)} 元`),
    metric("本月應付", `${money(d.this_month_total)} 元`),
    metric("下月預算外", `${money(unplanned)} 元`),
  ].join("");
  const cioCharts = document.querySelector("#cio-charts");
  if (cioCharts) {
    const planSeg = [
      { label: "計畫內（有預算）", value: planned, color: CHART_COLORS[1], text: `${money(planned)} 元` },
      { label: "預算外（無對應預算）", value: unplanned, color: CHART_COLORS[3], text: `${money(unplanned)} 元` },
    ];
    const flow = (d.forecast || []).map((f, i) => ({ label: f.month.slice(5), value: f.total || 0, color: i === 0 ? CHART_COLORS[6] : CHART_COLORS[0] }));
    cioCharts.innerHTML =
      chartCard("下月支出：計畫內 vs 預算外", donutSVG(planSeg, { center: unplanned > 0 ? "留意" : "OK" }) + chartLegend(planSeg)) +
      chartCard("未來 6 個月應付現金流", flow.length ? barsSVG(flow, { width: 340 }) : `<p class="muted">尚無資料</p>`);
  }
  if (cioNextMonthLabel) cioNextMonthLabel.textContent = d.next_month ? `付款月份：${d.next_month}` : "";
  const rows = d.upcoming_next_month || [];
  if (cioUpcomingBody) {
    cioUpcomingBody.innerHTML = rows.length
      ? rows
          .map(
            (r) => `
            <tr data-case-id="${r.case_id}" class="clickable" title="點擊追查明細">
              <td>${escapeHtml(r.case_code)}${r.unplanned ? ' <span class="badge danger">預算外</span>' : ""}${r.overspent ? ' <span class="badge danger">超支</span>' : ""}</td>
              <td>${escapeHtml(r.case_title)}</td>
              <td>${escapeHtml(r.owner || "未指派")}</td>
              <td>${escapeHtml(valueOrDash(r.contract_code))}</td>
              <td>${money(r.payment_amount)}</td>
              <td>${escapeHtml(labelStatus(r.status))}</td>
            </tr>`
          )
          .join("")
      : `<tr><td colspan="6" class="muted">下月沒有排定要出的款。</td></tr>`;
  }
}

async function loadCioDrill(caseId) {
  if (!cioDrill) return;
  cioDrill.hidden = false;
  cioDrill.innerHTML = `<p class="muted">追查中…</p>`;
  try {
    const payload = await api(`/api/cases/${caseId}/360`);
    const d = payload.data || {};
    const c = d.case || {};
    const contracts = (d.contracts || [])
      .map((k) => `<li><strong>${escapeHtml(k.contract_code)}</strong> ${escapeHtml(k.contract_name || "")} ｜ 廠商：${escapeHtml(valueOrDash(k.vendor_name))} ｜ 金額：${money(k.amount)} ｜ 到期：${escapeHtml(valueOrDash(k.end_date))}</li>`)
      .join("") || `<li class="muted">無關聯合約</li>`;
    const payments = (d.payments || [])
      .map((p) => `<li>${escapeHtml(p.payment_month)} ｜ ${money(p.payment_amount)} 元 ｜ ${escapeHtml(labelStatus(p.status))}</li>`)
      .join("") || `<li class="muted">無付款紀錄</li>`;
    const documents = (d.documents || [])
      .map((doc) => `<li>${escapeHtml(doc.file_name)} ｜ ${escapeHtml(labelStatus(doc.status || "active"))}</li>`)
      .join("") || `<li class="muted">無文件</li>`;
    const budgets = (d.budgets || [])
      .map((b) => `<li><strong>${escapeHtml(b.budget_code)}</strong> ${escapeHtml(valueOrDash(b.category))} ｜ ${escapeHtml(valueOrDash(b.unit_name))} ｜ 金額：${money(b.amount)} 元</li>`)
      .join("") || `<li class="muted">無關聯預算</li>`;
    const signoffs = (d.signoffs || [])
      .map((s) => `<li><strong>${escapeHtml(s.signoff_code)}</strong> ${escapeHtml(s.subject || "")} ｜ 申請人：${escapeHtml(valueOrDash(s.applicant))} ｜ 金額：${money(s.amount)} 元 ｜ ${escapeHtml(labelStatus(s.status))}</li>`)
      .join("") || `<li class="muted">無關聯簽呈</li>`;
    const purchases = (d.purchases || [])
      .map((p) => `<li><strong>${escapeHtml(p.purchase_code)}</strong> ${escapeHtml(p.item_name || "")} ｜ 廠商：${escapeHtml(valueOrDash(p.vendor_name))} ｜ 金額：${money(p.amount)} 元 ｜ ${escapeHtml(labelStatus(p.status))}</li>`)
      .join("") || `<li class="muted">無關聯請購</li>`;
    const projects = (d.projects || [])
      .map((p) => `<li><strong>${escapeHtml(p.project_code)}</strong> ${escapeHtml(p.project_name || "")} ｜ 進度 ${Number(p.progress || 0)}% ｜ ${escapeHtml(labelStatus(p.status))}</li>`)
      .join("") || `<li class="muted">無關聯專案</li>`;
    cioDrill.innerHTML = `
      <div class="section-heading compact">
        <h2>追查：${escapeHtml(c.case_code || "")}　${escapeHtml(c.title || "")}</h2>
        <button type="button" class="secondary" id="cio-drill-close">收起</button>
      </div>
      <div class="metrics">
        ${metric("案件金額", `${money(c.amount)} 元`)}
        ${metric("承辦", escapeHtml(c.owner || "未指派"))}
        ${metric("狀態", escapeHtml(labelStatus(c.status || "")))}
        ${metric("付款合計", `${money((d.totals || {}).payment_amount)} 元`)}
      </div>
      <h3>對應預算</h3><ul class="note-list">${budgets}</ul>
      <h3>對應專案</h3><ul class="note-list">${projects}</ul>
      <h3>對應簽呈</h3><ul class="note-list">${signoffs}</ul>
      <h3>對應請購</h3><ul class="note-list">${purchases}</ul>
      <h3>關聯合約</h3><ul class="note-list">${contracts}</ul>
      <h3>付款明細</h3><ul class="note-list">${payments}</ul>
      <h3>文件</h3><ul class="note-list">${documents}</ul>`;
  } catch (error) {
    cioDrill.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  }
}

async function loadReminders() {
  const el = document.querySelector("#reminders-list");
  if (!el) return;
  const payload = await api("/api/reports/reminders");
  const items = payload.data || [];
  const countEl = document.querySelector("#reminders-count");
  const overdue = items.filter((i) => i.severity === "overdue").length;
  if (countEl) {
    countEl.hidden = items.length === 0;
    countEl.textContent = overdue ? `${overdue} 逾期 / 共 ${items.length}` : `${items.length}`;
  }
  el.innerHTML = items.length
    ? items
        .map((i) => {
          const kind = i.type === "case" ? "案件" : i.type === "project" ? "專案" : "合約";
          const tag = i.severity === "overdue" ? `已逾期 ${Math.abs(i.days)} 天` : `剩 ${i.days} 天`;
          return `
            <li>
              <span class="badge ${i.severity === "overdue" ? "danger" : "warn"}">${tag}</span>
              <strong>${escapeHtml(kind)}｜${escapeHtml(i.code)}　${escapeHtml(i.title)}</strong>
              <small>期限：${escapeHtml(i.date)}；負責人：${escapeHtml(i.owner || "未指派")}；狀態：${escapeHtml(labelStatus(i.status))}</small>
            </li>`;
        })
        .join("")
    : `<li><small class="muted">目前沒有逾期或即將到期的催辦項目。</small></li>`;
}

async function loadPendingApprovals() {
  const el = document.querySelector("#pending-approvals-list");
  const wrap = document.querySelector("#pending-approvals");
  if (!el || !wrap) return;
  const canApprove = currentUser && currentUser.role_code === "manager_assistant";
  wrap.hidden = !canApprove;
  if (!canApprove) return;
  const items = (await api("/api/reports/pending-approvals")).data || [];
  const countEl = document.querySelector("#pending-approvals-count");
  if (countEl) { countEl.hidden = items.length === 0; countEl.textContent = `${items.length}`; }
  el.innerHTML = items.length
    ? items
        .map((c) => `
          <li data-case-id="${c.id}">
            <strong>${escapeHtml(c.case_code)}　${escapeHtml(c.title)}</strong>
            <small>承辦：${escapeHtml(c.owner || "未指派")}｜建立者：${escapeHtml(valueOrDash(c.created_by))}｜金額：${money(c.amount)} 元</small>
            <button type="button" data-action="approve-pending">核准</button>
          </li>`)
        .join("")
    : `<li><small class="muted">目前沒有等你複核的案件。</small></li>`;
}

async function loadOrphanPayments() {
  const el = document.querySelector("#orphan-payments-list");
  const wrap = document.querySelector("#orphan-payments");
  if (!el || !wrap) return;
  if (!currentUser || currentUser.role_code !== "manager_assistant") { wrap.hidden = true; return; }
  const items = (await api("/api/reports/orphan-payments")).data || [];
  const countEl = document.querySelector("#orphan-payments-count");
  wrap.hidden = items.length === 0;
  if (countEl) { countEl.hidden = items.length === 0; countEl.textContent = `${items.length}`; }
  el.innerHTML = items
    .map((p) => `<li><span class="badge danger">未歸戶</span> <strong>${escapeHtml(p.contract_code)}</strong> <small>${escapeHtml(p.payment_month)}｜${money(p.payment_amount)} 元｜${escapeHtml(labelStatus(p.status))}</small></li>`)
    .join("");
}

async function loadAdminConsole() {
  const form = document.querySelector("#admin-settings-form");
  if (!form) return;
  if (!currentUser || currentUser.role_code !== "admin") return;
  const s = (await api("/api/admin/settings")).data || {};
  for (const k of ["smtp_host", "smtp_port", "smtp_user", "smtp_from", "email_map", "notify_enabled"]) {
    if (form.elements[k]) form.elements[k].value = s[k] ?? "";
  }
  if (form.elements.smtp_password) form.elements.smtp_password.placeholder = s.smtp_password_set ? "已設定（留空＝不變更）" : "SMTP 密碼（留空＝不變更）";
  const opt = (await api("/api/options")).data || {};
  if (form.elements.opt_budget_categories) form.elements.opt_budget_categories.value = (opt.budget_categories || []).join(",");
  if (form.elements.opt_project_necessity) form.elements.opt_project_necessity.value = (opt.project_necessity || []).join(",");

  const dash = (await api("/api/dashboard")).data || {};
  const health = await api("/health");
  const statusEl = document.querySelector("#admin-status");
  if (statusEl) {
    statusEl.innerHTML = [
      metric("版本", escapeHtml(String(health.version || "-"))),
      metric("資料庫", escapeHtml((health.database || {}).type || "-")),
      metric("案件數", (dash.counts || {}).cases ?? "-"),
      metric("SMTP", s.smtp_host ? "已設定" : "未設定"),
    ].join("");
  }

  await loadAdminUsers();

  const logs = (await api("/api/audit-logs?limit=20")).data || [];
  const body = document.querySelector("#admin-audit-body");
  if (body) {
    body.innerHTML = logs.length
      ? logs
          .map((l) => `<tr><td>${escapeHtml(l.created_at || "")}</td><td>${escapeHtml(l.actor || "")}</td><td>${escapeHtml(l.table_name || "")}</td><td>${escapeHtml(l.action || "")}</td><td>${escapeHtml(String(l.row_id ?? ""))}</td></tr>`)
          .join("")
      : `<tr><td colspan="5" class="muted">尚無稽核紀錄</td></tr>`;
  }
}

async function loadAdminUsers() {
  const body = document.querySelector("#admin-users-body");
  if (!body) return;
  const d = (await api("/api/admin/users")).data || {};
  const roleSel = document.querySelector("#admin-user-role");
  if (roleSel && !roleSel.dataset.filled) {
    roleSel.innerHTML = (d.roles || []).map((r) => `<option value="${escapeHtml(r.code)}">${escapeHtml(r.name)}</option>`).join("");
    roleSel.dataset.filled = "1";
  }
  body.innerHTML = (d.users || [])
    .map((u) => {
      const state = u.builtin
        ? '<span class="badge">內建</span>'
        : u.disabled
        ? '<span class="badge danger">已停用</span>'
        : '<span class="badge ok">啟用</span>';
      const actions = u.builtin
        ? '<span class="muted">—</span>'
        : `<button type="button" class="secondary" data-uaction="${u.disabled ? "enable" : "disable"}" data-username="${escapeHtml(u.username)}">${u.disabled ? "啟用" : "停用"}</button>
           <button type="button" class="secondary" data-uaction="reset" data-username="${escapeHtml(u.username)}">改密碼</button>
           <button type="button" class="danger" data-uaction="delete" data-username="${escapeHtml(u.username)}">刪除</button>`;
      return `<tr><td>${escapeHtml(u.username)}</td><td>${escapeHtml(u.role_name)}</td><td>${escapeHtml(valueOrDash(u.display_name))}</td><td>${escapeHtml(valueOrDash(u.email))}</td><td>${state}</td><td>${actions}</td></tr>`;
    })
    .join("");
}

async function loadOptions() {
  try {
    const o = (await api("/api/options")).data || {};
    const fill = (sel, arr) => {
      const dl = document.querySelector(sel);
      if (dl) dl.innerHTML = (arr || []).map((v) => `<option value="${escapeHtml(v)}"></option>`).join("");
    };
    fill("#opt-budget-categories", o.budget_categories);
    fill("#opt-project-necessity", o.project_necessity);
    fill("#opt-project-level", o.project_level);
    fill("#opt-project-rag", o.project_rag);
  } catch (error) {
    /* 選項載入失敗不影響主流程 */
  }
}

async function loadManagerCharts() {
  const el = document.querySelector("#manager-charts");
  if (!el) return;
  const [ms, cs] = await Promise.all([api("/api/reports/monthly-spending"), api("/api/cases")]);
  const months = (ms.data || []).slice(0, 6).reverse();  // 舊到新
  const bars = months.map((m) => ({ label: m.month, value: m.total || 0, color: CHART_COLORS[0] }));
  // 案件狀態分布
  const counts = {};
  for (const c of cs.data || []) counts[c.status] = (counts[c.status] || 0) + 1;
  const order = ["draft", "pending_review", "reviewing", "approved", "disabled"];
  const segs = order
    .filter((s) => counts[s])
    .map((s, i) => ({ label: labelStatus(s), value: counts[s], color: CHART_COLORS[i % CHART_COLORS.length], text: `${counts[s]} 件` }));
  const totalCases = (cs.data || []).length;
  el.innerHTML =
    chartCard("月度支出趨勢", bars.length ? barsSVG(bars) : `<p class="muted">尚無付款資料</p>`) +
    chartCard("案件狀態分布", segs.length ? donutSVG(segs, { center: `${totalCases} 件` }) + chartLegend(segs) : `<p class="muted">尚無案件</p>`);
}

async function refresh() {
  await Promise.all([
    loadDashboard(), loadCases(), loadContracts(), loadPayments(), loadDocuments(),
    loadResource("budget"), loadResource("project"), loadResource("signoff"), loadResource("purchase"),
    loadMappingCatalog(), loadTodo(), loadMonthly(), loadExpiring(), loadCioOverview(), loadReminders(),
    loadManagerCharts(), loadPendingApprovals(), loadOrphanPayments(), loadAdminConsole(), loadOptions(),
    loadPortfolio(),
  ]);
}

// 進度總表：組別 tab / 子 tab / 由總覽點列進單一專案
document.querySelector("#pf-groups")?.addEventListener("click", (event) => {
  const t = event.target.closest("[data-pf-g]");
  if (!t) return;
  portfolioState.g = Number(t.getAttribute("data-pf-g"));
  portfolioState.s = "ov";
  renderPortfolio();
});
document.querySelector("#pf-subs")?.addEventListener("click", (event) => {
  const t = event.target.closest("[data-pf-s]");
  if (!t) return;
  const v = t.getAttribute("data-pf-s");
  portfolioState.s = v === "ov" ? "ov" : Number(v);
  renderPortfolio();
});
document.querySelector("#pf-view")?.addEventListener("click", (event) => {
  const row = event.target.closest("[data-pf-proj]");
  if (!row) return;
  const group = portfolioGroups[portfolioState.g];
  const idx = group.projects.findIndex((p) => String(p.id) === String(row.getAttribute("data-pf-proj")));
  if (idx >= 0) { portfolioState.s = idx; renderPortfolio(); }
});

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
  if (form.elements.due_date) form.elements.due_date.value = item.due_date || "";
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

if (todoList) {
  todoList.addEventListener("click", (event) => {
    const li = event.target.closest("li[data-case-id]");
    if (!li || !li.dataset.caseId) return;
    startEdit(li.dataset.caseId);
    form.scrollIntoView({ block: "center" });
  });
}

if (cioCasesBody) {
  cioCasesBody.addEventListener("click", (event) => {
    if (!event.target.closest("[data-cio-edit]")) return;
    const tr = event.target.closest("tr[data-case-id]");
    if (!tr) return;
    startEdit(tr.dataset.caseId);
    form.scrollIntoView({ block: "center" });
  });
}

if (cioUpcomingBody) {
  cioUpcomingBody.addEventListener("click", (event) => {
    const tr = event.target.closest("tr[data-case-id]");
    if (!tr || !tr.dataset.caseId) return;
    loadCioDrill(tr.dataset.caseId);
    cioDrill?.scrollIntoView({ block: "nearest" });
  });
}

if (cioDrill) {
  cioDrill.addEventListener("click", (event) => {
    if (event.target.id === "cio-drill-close") cioDrill.hidden = true;
  });
}

document.querySelector("#pending-approvals-list")?.addEventListener("click", async (event) => {
  if (!event.target.closest('[data-action="approve-pending"]')) return;
  const li = event.target.closest("li[data-case-id]");
  if (!li) return;
  try {
    await api(`/api/cases/${li.dataset.caseId}/approve`, { method: "POST" });
  } catch (error) {
    window.alert(error.message);
  }
  await refresh();
});

document.querySelector("#export-cases")?.addEventListener("click", () => {
  window.location.href = "/api/cases.csv";
});

document.querySelector("#goto-import")?.addEventListener("click", () => {
  const card = document.querySelector('a.module-card[href="#data-review"]');
  if (card) activateModuleCard(card);  // 匯入工作區在「資料檢核」模組
});

async function projXlsx(commit) {
  const file = document.querySelector("#proj-xlsx-file")?.files?.[0];
  const el = document.querySelector("#proj-xlsx-status");
  const commitBtn = document.querySelector("#proj-xlsx-commit");
  if (!file) { if (el) el.textContent = "請先選一個 .xlsx 檔"; return; }
  if (commit && !window.confirm("確定正式匯入？已存在的專案會跳過不覆蓋。")) return;
  if (el) el.textContent = commit ? "匯入中…" : "解析中…";
  try {
    const res = (await api(`/api/projects/import-xlsx?commit=${commit}`, { method: "POST", body: file })).data || {};
    if (commit) {
      if (el) el.textContent = `匯入完成：新增 ${res.created_count} 個、跳過 ${res.skipped_count} 個（已存在）。`;
      await refresh();
    } else {
      const names = (res.sample || []).slice(0, 3).map((s) => s.project_name).join("、");
      if (el) el.textContent = `預覽：共 ${res.count} 個專案${names ? "（例：" + names + "…）" : ""}`;
      if (commitBtn) commitBtn.disabled = !res.count;
    }
  } catch (error) {
    if (el) el.textContent = `失敗：${error.message}`;
  }
}
document.querySelector("#proj-xlsx-preview")?.addEventListener("click", () => projXlsx(false));
document.querySelector("#proj-xlsx-commit")?.addEventListener("click", () => projXlsx(true));

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
  try {
    if (action === "submit") {
      await api(`/api/cases/${id}/submit`, { method: "POST" });
    }
    if (action === "approve") {
      await api(`/api/cases/${id}/approve`, { method: "POST" });
    }
    if (action === "disable") {
      await api(`/api/cases/${id}/disable`, { method: "POST" });
    }
    if (action === "delete") {
      await api(`/api/cases/${id}`, { method: "DELETE" });
    }
  } catch (error) {
    window.alert(error.message);
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
formalImportCases?.addEventListener("click", submitFormalImport);
refreshMappingCatalog.addEventListener("click", loadMappingCatalog);

async function runDemo(action) {
  if (!demoStatus) return;
  demoStatus.textContent = action === "load" ? "載入中…" : "清空中…";
  if (demoSeed) demoSeed.disabled = true;
  if (demoClear) demoClear.disabled = true;
  try {
    const res = await api(`/api/dev-console/demo-data/${action}`, { method: "POST" });
    const counts = res.data || {};
    const total = Object.values(counts).reduce((sum, n) => sum + (Number(n) || 0), 0);
    demoStatus.textContent = action === "load" ? `已載入 ${total} 筆示範資料` : `已清空 ${total} 筆示範資料`;
    await refresh();
  } catch (error) {
    demoStatus.textContent = `失敗：${error.message}`;
  } finally {
    if (demoSeed) demoSeed.disabled = false;
    if (demoClear) demoClear.disabled = false;
  }
}
demoSeed?.addEventListener("click", () => runDemo("load"));
demoClear?.addEventListener("click", () => runDemo("clear"));

// 每個模組的 crud-zone 注入「匯出 CSV」按鈕
for (const [type, cfg] of Object.entries(resourceConfig)) {
  const zone = resourceForms[type]?.closest(".crud-zone");
  const h2 = zone?.querySelector("h2");
  if (h2 && !h2.querySelector("[data-export]")) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "secondary";
    btn.dataset.export = `${cfg.api}.csv`;
    btn.textContent = "匯出 CSV";
    btn.style.marginLeft = "12px";
    h2.appendChild(btn);
  }
}
document.addEventListener("click", (event) => {
  const b = event.target.closest("[data-export]");
  if (b) window.location.href = b.dataset.export;
  // 操作下拉：一次只開一個，點外面就收起
  const openedSummary = event.target.closest(".row-menu > summary");
  const current = openedSummary ? openedSummary.parentElement : null;
  for (const menu of document.querySelectorAll("details.row-menu[open]")) {
    if (menu !== current && !menu.contains(event.target)) menu.removeAttribute("open");
  }
});

const globalSearch = document.querySelector("#global-search");
const searchResults = document.querySelector("#search-results");
let searchTimer = null;
globalSearch?.addEventListener("input", () => {
  clearTimeout(searchTimer);
  const q = globalSearch.value.trim();
  if (!searchResults) return;
  if (q.length < 2) { searchResults.hidden = true; searchResults.innerHTML = ""; return; }
  searchTimer = setTimeout(async () => {
    const label = { case: "案件", contract: "合約", document: "文件", budget: "預算", project: "專案", signoff: "簽呈", purchase: "請購" };
    try {
      const rows = (await api(`/api/search?q=${encodeURIComponent(q)}`)).data || [];
      searchResults.hidden = false;
      searchResults.innerHTML = rows.length
        ? rows
            .map((r) => `<div class="search-hit"><span class="badge">${escapeHtml(label[r.type] || r.type)}</span> <strong>${escapeHtml(valueOrDash(r.code))}</strong> ${escapeHtml(r.title || "")}<small class="muted"> ${escapeHtml(valueOrDash(r.detail))}</small></div>`)
            .join("")
        : `<div class="muted" style="padding:.45rem .3rem;">找不到「${escapeHtml(q)}」</div>`;
    } catch (error) {
      searchResults.hidden = false;
      searchResults.innerHTML = `<div class="muted" style="padding:.45rem .3rem;">搜尋失敗：${escapeHtml(error.message)}</div>`;
    }
  }, 250);
});

document.querySelector("#admin-settings-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form).entries());
  const el = document.querySelector("#admin-settings-status");
  try {
    await api("/api/admin/settings", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    if (el) el.textContent = "已儲存";
    if (form.elements.smtp_password) form.elements.smtp_password.value = "";
    await loadAdminConsole();
  } catch (error) {
    if (el) el.textContent = `失敗：${error.message}`;
  }
});

document.querySelector("#admin-backup")?.addEventListener("click", () => {
  window.location.href = "/api/admin/backup";
});

document.querySelector("#admin-user-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target).entries());
  const el = document.querySelector("#admin-user-status");
  try {
    await api("/api/admin/users", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    if (el) el.textContent = "已新增";
    event.target.reset();
    await loadAdminUsers();
  } catch (error) {
    if (el) el.textContent = `失敗：${error.message}`;
  }
});

document.querySelector("#admin-users-body")?.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-uaction]");
  if (!btn) return;
  const username = btn.dataset.username;
  const act = btn.dataset.uaction;
  try {
    if (act === "disable" || act === "enable") {
      await api(`/api/admin/users/${username}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ disabled: act === "disable" }) });
    } else if (act === "reset") {
      const pw = window.prompt(`為 ${username} 設定新密碼：`);
      if (!pw) return;
      await api(`/api/admin/users/${username}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password: pw }) });
    } else if (act === "delete") {
      if (!window.confirm(`確定刪除帳號 ${username}？`)) return;
      await api(`/api/admin/users/${username}`, { method: "DELETE" });
    }
    await loadAdminUsers();
  } catch (error) {
    window.alert(error.message);
  }
});

document.querySelector("#admin-test-email")?.addEventListener("click", async () => {
  const to = (document.querySelector("#admin-test-to")?.value || "").trim();
  const el = document.querySelector("#admin-test-status");
  try {
    const res = (await api("/api/admin/settings/test-email", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ to }) })).data || {};
    if (el) el.textContent = res.sent ? `已寄到 ${res.to}` : `未寄出：${res.reason || ""}`;
  } catch (error) {
    if (el) el.textContent = `失敗：${error.message}`;
  }
});

document.querySelector("#notify-reminders")?.addEventListener("click", async () => {
  const el = document.querySelector("#notify-preview");
  try {
    const res = (await api("/api/reports/reminders/notify", { method: "POST" })).data || {};
    const digests = res.digests || [];
    if (!digests.length) { el.textContent = "目前沒有需要通知的催辦項目。"; return; }
    const head = res.sent ? `已寄出 ${res.count} 封通知。\n\n` : `（${res.reason || "尚未設定 email，先預覽"}）\n\n`;
    el.textContent = head + digests.map((d) => `▸ ${d.owner}（${d.count} 件）\n${d.body}`).join("\n\n");
  } catch (error) {
    el.textContent = `失敗：${error.message}`;
  }
});

initializeSession().catch((error) => {
  cases.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  contracts.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  payments.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  documents.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
});
