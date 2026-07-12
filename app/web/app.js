// 前端建置版本（單一來源）。每次改前端就 bump 版本號＋index.html 的 ?v=。
// 版本號「vX.Y.Z」永遠往上加、永不重複——同一天更新多次也分得出第幾版；號碼大＝新。
// 徽章顯示前後端版本號，對不上＝後端沒重啟，會亮警告。格式「vX.Y.Z · 日期 · 摘要」。
const BUILD_TAG = "v0.9.95 · 2026-07-12 · 承辦補齊7大模組可見範圍＋隱藏主管儀表板＋登入顯示姓名";
(async () => {
  const badge = document.querySelector("#build-badge");
  if (!badge) return;
  const verOf = (s) => (String(s).split("·")[0] || "?").trim();  // 取「vX.Y.Z」那段
  const front = verOf(BUILD_TAG);
  badge.textContent = `前端 ${front} ｜ 後端 …`;
  try {
    const h = await fetch("/health", { credentials: "same-origin", cache: "no-store" }).then((r) => r.json());
    const back = verOf(h.build || "");
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
const testDataControls = document.querySelector("#test-data-controls");
const testDataClear = document.querySelector("#test-data-clear");
const testDataStatus = document.querySelector("#test-data-status");
const backfillControls = document.querySelector("#backfill-controls");
const backfillRun = document.querySelector("#backfill-run");
const backfillStatusEl = document.querySelector("#backfill-status");
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
let lastPanelId = null;
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
    fields: ["contract_code", "contract_name", "vendor_name", "amount", "case_id", "purchase_id", "status", "end_date"],
    numberFields: ["amount", "case_id", "purchase_id"],
    canDisable: true,
    columns: [
      { label: "系統編號", cell: (i) => systemCodeCell(SYS_PREFIX.contract, i.case_id) },
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
      { label: "系統編號", cell: (i) => systemCodeCellPayment(i) },
      { label: "核銷編號", cell: (i) => `<strong>${escapeHtml(valueOrDash(i.settle_no))}</strong>` },
      { label: "核銷項目", cell: (i) => escapeHtml(valueOrDash(i.item) === "-" ? valueOrDash(i.payment_month) : i.item) },
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
    fields: ["budget_code", "category", "unit_name", "expense_detail", "fill_dept", "estimator",
             "fiscal_year", "amount", "status", "case_id", "note",
             "alloc_method", "alloc_category_kind", "alloc_category"],
    numberFields: ["amount", "case_id"], canDisable: true,
    columns: [
      { label: "系統編號", cell: (i) => i.case_id
          ? systemCodeCell(SYS_PREFIX.budget, i.case_id)
          : `<button type="button" class="btn-sm" data-assign-case="${i.id}" title="歸戶到案件才會有系統編號">＋歸戶</button>` },
      { label: "預算編號", cell: (i) => `<strong>${escapeHtml(i.budget_code)}</strong>` },
      { label: "金額", cls: "num", cell: (i) => `${money(i.amount)} 元` },
      { label: "分類", cell: (i) => escapeHtml(valueOrDash(i.category)) },
      { label: "單位／年度", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.unit_name))}｜${escapeHtml(valueOrDash(i.fiscal_year))}</span>` },
      { label: "狀態", cell: (i) => statusChip(i.status) },
      { label: "年度費用", cell: (i) => `<button type="button" class="secondary btn-sm" data-annual="${i.id}">比較</button>` },
      { label: "共同費用", cell: (i) => `<button type="button" class="secondary btn-sm" data-alloc-view="${i.id}">分攤</button>` },
    ],
  },
  project: {
    plural: "projects", idAttr: "project-id", idField: "projectId", api: "/api/projects",
    navCount: "nav-count-projects", navLabel: "專案",
    fields: ["project_code", "project_name", "source", "necessity", "progress", "owner", "status", "case_id", "due_date", "note",
             "level", "progress_planned", "rag_status", "start_date", "end_date"],
    numberFields: ["progress", "progress_planned", "case_id"], canDisable: true,
    columns: [
      { label: "系統編號", cell: (i) => i.case_id
          ? systemCodeCell(SYS_PREFIX.project, i.case_id)
          : `<button type="button" class="btn-sm" data-assign-project-case="${i.id}" title="歸戶到案件才會有系統編號、也才會出現在案件的進度圖/矩陣">＋歸戶</button>` },
      { label: "編號", cell: (i) => `<strong>${escapeHtml(i.project_code)}</strong>` },
      { label: "專案名稱", cell: (i) => `<button type="button" class="link-btn" data-view-items="${i.id}" title="查看細項（進度總表）">${escapeHtml(i.project_name)}</button>` },
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
    fields: ["signoff_code", "subject", "applicant", "amount", "status", "sign_date", "case_id", "note", "attachment_ref"],
    numberFields: ["amount", "case_id"], canDisable: true,
    columns: [
      { label: "系統編號", cell: (i) => systemCodeCell(SYS_PREFIX.signoff, i.case_id) },
      { label: "簽呈號碼", cell: (i) => `<strong>${escapeHtml(i.signoff_code)}</strong>` },
      { label: "主旨", cell: (i) => escapeHtml(i.subject) },
      { label: "附件", cell: (i) => attachmentLink(i.attachment_ref) },
      { label: "簽核日", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.sign_date))}</span>` },
      { label: "金額", cls: "num", cell: (i) => `${money(i.amount)} 元` },
      { label: "狀態", cell: (i) => statusChip(i.status) },
    ],
  },
  purchase: {
    plural: "purchases", idAttr: "purchase-id", idField: "purchaseId", api: "/api/purchases",
    navCount: "nav-count-purchases", navLabel: "請購",
    fields: ["purchase_code", "item_name", "vendor_name", "quantity", "amount", "status", "case_id", "signoff_id", "note"],
    numberFields: ["quantity", "amount", "case_id", "signoff_id"], canDisable: true,
    columns: [
      { label: "系統編號", cell: (i) => systemCodeCell(SYS_PREFIX.purchase, i.case_id) },
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
  // no-store：權限/資料 GET 永不吃瀏覽器快取，避免後端更新後前端還讀到舊的 allowed_modules
  const response = await fetch(path, { credentials: "same-origin", cache: "no-store", ...(options || {}) });
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

// 系統編號：案件領「年度-四位流水號」，各階段用同尾碼＋前綴組成，做跨階段勾稽
const SYS_PREFIX = { budget: "Budget", project: "Project", signoff: "Sign", contract: "Contract", purchase: "Purchase", payment: "Pay" };
function caseNumber(c) {
  return (c && c.fiscal_year && c.seq) ? `${c.fiscal_year}-${String(c.seq).padStart(4, "0")}` : "";
}
function systemCodeCell(prefix, caseId) {
  const c = (caseCache || []).find((x) => String(x.id) === String(caseId));
  const n = caseNumber(c);
  return n ? `<strong>${escapeHtml(prefix + "-" + n)}</strong>` : `<span class="muted" title="尚未關聯案件，無系統編號">—</span>`;
}
// 付款經「合約」再回溯到案件（付款掛合約、合約掛案件）
function systemCodeCellPayment(payment) {
  const k = (resourceCaches.contract || []).find((x) => String(x.id) === String(payment.contract_id));
  return systemCodeCell(SYS_PREFIX.payment, k ? k.case_id : null);
}

// 簽呈附件參照：是網址就做成可點連結（新視窗），否則顯示 📎＋文字（如檔案路徑）
function attachmentLink(ref) {
  const v = String(ref || "").trim();
  if (!v) return `<span class="muted">-</span>`;
  if (/^https?:\/\//i.test(v)) {
    return `<a href="${escapeHtml(v)}" target="_blank" rel="noopener noreferrer" title="開啟簽呈附件">📎 開啟</a>`;
  }
  return `<span title="${escapeHtml(v)}">📎 ${escapeHtml(v.length > 20 ? v.slice(0, 20) + "…" : v)}</span>`;
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
  if (tabName === "progress" || tabName === "matrix") loadCaseProgress();
  if (tabName === "portfolio") loadPortfolio();  // 進度總表併入案件管理分頁
}

// ── 線性進度圖／處理優先矩陣：讀 /api/cases/progress，系統自動推導、唯讀 ──
const TONE_LABEL = { green: "完成", white: "還沒輪到", orange: "快逾期待處理", red: "已逾期", na: "不適用" };
let lastProgressItems = [];  // 快取最近一次進度資料，供矩陣過濾器不重打 API 重繪
// 矩陣依狀態分類：可自由選要看哪一類（單看或組合看）
const PHASE_META = [
  { key: "active", label: "進行中／有風險" },
  { key: "done", label: "已完成" },
  { key: "not_started", label: "未開始" },
];
let matrixPhaseFilter = new Set(["active"]);  // 預設看進行中；點分類 chip 可切換
const QUAD_LABEL = { now: "立即處理", confirm: "主管確認", week: "本週處理", plan: "可安排" };
const QUAD_RANK = { now: 0, week: 1, confirm: 2, plan: 3 };

function urgencyText(days) {
  if (days == null) return "待確認";
  if (days < 0) return `逾期 ${-days} 天`;
  return `${days} 天`;
}

function renderProgressRow(it) {
  const dots = (it.stages || []).map((s) =>
    `<span class="case-step ${s.tone}" title="${escapeHtml(s.label)}：${TONE_LABEL[s.tone] || s.tone}${s.days != null ? "（" + urgencyText(s.days) + "）" : ""}">`
    + `<span class="case-dot ${s.tone}"></span><span>${escapeHtml(s.label)}</span></span>`).join("");
  const amt = it.amount ? `${money(it.amount)} 元` : "—";
  return `<div class="case-progress-row" data-case-id="${it.case_id}">
    <div class="case-progress-name"><b>${escapeHtml(it.case_code)}　${escapeHtml(it.title)}</b>
      <span>${amt}｜${escapeHtml(it.owner || "未指派")}</span></div>
    <div class="case-progress-track">${dots || '<span class="muted">尚未建立流程階段</span>'}</div>
    <div class="case-progress-status"><span class="status-pill ${it.block.tone}">${escapeHtml(it.block.text)}</span></div>
  </div>`;
}

function renderMatrix(allItems) {
  const box = document.querySelector("#case-matrix");
  const body = document.querySelector("#case-matrix-body");
  // 依狀態分類：render chips（各帶件數），只顯示被選分類的案子
  const counts = { active: 0, done: 0, not_started: 0 };
  allItems.forEach((it) => { counts[it.phase] = (counts[it.phase] || 0) + 1; });
  if (matrixPhaseFilter.size === 0) matrixPhaseFilter = new Set(["active"]);
  const filtersEl = document.querySelector("#matrix-filters");
  if (filtersEl) {
    filtersEl.innerHTML = PHASE_META.map((p) =>
      `<button type="button" class="phase-chip${matrixPhaseFilter.has(p.key) ? " active" : ""}" data-phase="${p.key}">`
      + `${p.label} <span class="phase-chip-count">${counts[p.key] || 0}</span></button>`).join("");
  }
  const items = allItems.filter((it) => matrixPhaseFilter.has(it.phase));
  if (box) {
    box.querySelectorAll(".matrix-item").forEach((n) => n.remove());
    // 真散佈：直接落在 (x,y)＝金額×急迫度的座標，位置反映數值，不排排站
    for (const it of items) {
      const m = it.matrix || {};
      const el = document.createElement("div");
      el.className = `matrix-item ${m.quadrant || "plan"}`;
      el.style.left = `${m.x}%`;
      el.style.top = `${m.y}%`;
      el.title = `${escapeHtml(it.title)}｜${it.amount ? money(it.amount) + " 元" : "0"}｜${urgencyText(it.urgency_days)}`;
      el.innerHTML = `<b>${escapeHtml(it.title.slice(0, 8))}</b><span>${it.amount ? money(it.amount) : 0} / ${urgencyText(it.urgency_days)}</span>`;
      box.appendChild(el);
    }
  }
  if (body) {
    const sorted = [...items].sort((a, b) => (QUAD_RANK[a.matrix.quadrant] ?? 9) - (QUAD_RANK[b.matrix.quadrant] ?? 9));
    body.innerHTML = sorted.length
      ? sorted.map((it, i) => `<tr data-case-id="${it.case_id}">
          <td>${i + 1}</td>
          <td>${escapeHtml(it.title)}</td>
          <td class="num">${it.amount ? money(it.amount) + " 元" : "—"}</td>
          <td>${urgencyText(it.urgency_days)}</td>
          <td>${QUAD_LABEL[it.matrix.quadrant] || "-"} / ${escapeHtml(it.matrix.reason || "")}</td>
          <td><span class="status-pill ${it.block.tone}">${escapeHtml(it.block.text)}</span></td>
        </tr>`).join("")
      : `<tr><td colspan="6" class="muted">目前沒有案件。</td></tr>`;
  }
}

async function loadCaseProgress() {
  const listEl = document.querySelector("#case-progress-list");
  try {
    const payload = await api("/api/cases/progress");
    const items = (payload.data && payload.data.items) || [];
    lastProgressItems = items;
    if (listEl) {
      listEl.innerHTML = items.length
        ? items.map(renderProgressRow).join("")
        : `<p class="muted">目前沒有案件。</p>`;
    }
    renderMatrix(items);
  } catch (error) {
    if (listEl) listEl.innerHTML = `<p class="muted">載入失敗：${escapeHtml(error.message)}</p>`;
  }
}
// 矩陣分類 chip：點一下切換該分類的顯示（至少留一類），用快取重繪不重打 API
document.querySelector("#matrix-filters")?.addEventListener("click", (event) => {
  const chip = event.target.closest(".phase-chip");
  if (!chip) return;
  const p = chip.getAttribute("data-phase");
  if (matrixPhaseFilter.has(p)) matrixPhaseFilter.delete(p);
  else matrixPhaseFilter.add(p);
  if (matrixPhaseFilter.size === 0) matrixPhaseFilter.add(p);  // 不允許全空，留住剛點的
  renderMatrix(lastProgressItems);
});

// ── L3 預算年度費用比較（唯讀衍生）：全年度/年增差異由後端算；% 全部獨立成欄、無 inline 註解 ──
let annualData = null;
let annualSort = { col: null, dir: "asc" };
let annualEditMode = false;

// 承辦編輯模式：逐年逐期填金額（budget_periods 整批取代）
function budgetPeriodRowHtml(periods, y) {
  return `<tr class="pe-row">`
    + `<td><input class="pe-year" type="text" value="${escapeHtml(y ? y.fiscal_year : "")}" placeholder="年度" /></td>`
    + periods.map((p) => `<td class="num"><input class="pe-amt" data-period="${escapeHtml(p)}" type="number" step="1" value="${y ? (y.periods[p] ?? 0) : 0}" /></td>`).join("")
    + `<td><button type="button" class="secondary btn-sm pe-remove" title="刪這一年">✕</button></td></tr>`;
}
function renderBudgetAnnualEditor(data) {
  const el = document.querySelector("#budget-annual");
  const b = data.budget || {};
  const periods = (data.periods && data.periods.length) ? data.periods : ["1-9月", "10-12月"];
  el.dataset.budgetId = b.id;
  el.dataset.periods = JSON.stringify(periods);
  const head = `<tr><th>年度</th>${periods.map((p) => `<th class="num">${escapeHtml(p)}</th>`).join("")}<th></th></tr>`;
  const rows = (data.years || []).length
    ? data.years.map((y) => budgetPeriodRowHtml(periods, y)).join("")
    : budgetPeriodRowHtml(periods, null);
  el.innerHTML = `
    <div class="section-heading compact"><h3>編輯年度費用明細 <span class="muted">— ${escapeHtml(b.category || "")}</span></h3>
      <div class="toolbar">
        <button type="button" class="secondary btn-sm" id="pe-add">＋ 新增年度</button>
        <button type="button" class="btn-sm" id="pe-save">儲存明細</button>
        <button type="button" class="secondary btn-sm" id="pe-cancel">取消</button>
      </div></div>
    <div class="table-shell"><table class="grid-table budget-annual-table"><thead>${head}</thead><tbody id="pe-body">${rows}</tbody></table></div>
    <p class="muted" id="pe-status">逐年逐期填金額，可＋新增年度；儲存＝整批取代這個預算的年度明細。</p>`;
  el.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function renderBudgetAnnual(data) {
  const el = document.querySelector("#budget-annual");
  if (!el) return;
  annualData = data;
  if (annualEditMode) { renderBudgetAnnualEditor(data); return; }
  const b = data.budget || {};
  const periods = data.periods || [];
  const fmtN = (n) => (n == null ? "—" : Number(n).toLocaleString());
  const nOrNeg = (v) => (v == null ? -Infinity : Number(v));
  const pctCell = (pct) => pct == null
    ? `<span class="muted">—</span>`
    : `<span class="period-diff ${pct > 0 ? "up" : pct < 0 ? "down" : ""}">${pct > 0 ? "+" : ""}${pct}%</span>`;
  const diffAmtCell = (d) => d == null
    ? `<span class="muted">—</span>`
    : `<span class="budget-diff ${d > 0 ? "up" : d < 0 ? "down" : ""}">${d > 0 ? "+" : ""}${fmtN(d)}</span>`;
  const noteCell = (y) => `<input type="text" class="budget-note-input" data-year="${escapeHtml(y.fiscal_year)}" value="${escapeHtml(y.note || "")}" placeholder="可填差異說明／決策註記…" />`;

  // 欄位驅動：每個 % 都是獨立一欄（對齊），無 cell 內註解
  const cols = [{ key: "fiscal_year", label: "年度", get: (y) => `${escapeHtml(y.fiscal_year)} 年`, sv: (y) => Number(y.fiscal_year) || 0 }];
  periods.forEach((p) => {
    cols.push({ key: `amt:${p}`, label: p, cls: "num", get: (y) => fmtN(y.periods[p]), sv: (y) => Number(y.periods[p]) || 0 });
    cols.push({ key: `pct:${p}`, label: `${p} 增減%`, cls: "num", get: (y) => pctCell(y.period_diff_pct ? y.period_diff_pct[p] : null), sv: (y) => nOrNeg(y.period_diff_pct ? y.period_diff_pct[p] : null) });
  });
  cols.push({ key: "annual_total", label: "全年度費用", cls: "num", get: (y) => `<b>${fmtN(y.annual_total)}</b>`, sv: (y) => Number(y.annual_total) || 0 });
  cols.push({ key: "diff", label: "費用差異", cls: "num", get: (y) => diffAmtCell(y.diff), sv: (y) => nOrNeg(y.diff) });
  cols.push({ key: "diff_pct", label: "差異%", cls: "num", get: (y) => pctCell(y.diff_pct), sv: (y) => nOrNeg(y.diff_pct) });
  cols.push({ key: "note", label: "備註", cls: "note-col", noSort: true, get: noteCell });

  let years = [...(data.years || [])];
  if (annualSort.col) {
    const c = cols.find((x) => x.key === annualSort.col);
    if (c) years.sort((r1, r2) => { const d = c.sv(r1) - c.sv(r2); return annualSort.dir === "desc" ? -d : d; });
  }
  const head = cols.map((c) => {
    const arrow = annualSort.col === c.key ? (annualSort.dir === "asc" ? " ▲" : " ▼") : "";
    const cls = [c.cls || "", c.noSort ? "" : "sortable"].filter(Boolean).join(" ");
    return `<th class="${cls}"${c.noSort ? "" : ` data-annual-sort="${escapeHtml(c.key)}" title="點欄名可排序"`}>${escapeHtml(c.label)}${arrow}</th>`;
  }).join("");
  const body = years.length
    ? years.map((y) => `<tr>${cols.map((c) => `<td class="${c.cls || ""}">${c.get(y)}</td>`).join("")}</tr>`).join("")
    : `<tr><td colspan="${cols.length}" class="muted">尚無年度費用明細（後續由匯入／編輯建立）。</td></tr>`;
  el.dataset.budgetId = b.id;
  el.innerHTML = `
    <div class="section-heading compact"><h3>年度費用比較 <span class="muted">— ${escapeHtml(b.category || "")}</span></h3>
      <div class="toolbar">
        <button type="button" class="secondary btn-sm" id="budget-annual-edit">編輯明細</button>
        <button type="button" class="secondary btn-sm" id="budget-annual-close">收起</button>
      </div></div>
    <div class="budget-annual-meta">
      <span>費用內容：${escapeHtml(b.expense_detail || "—")}</span>
      <span>填寫部門：${escapeHtml(b.fill_dept || "—")}</span>
      <span>預估人員：${escapeHtml(b.estimator || "—")}</span>
    </div>
    <div class="table-shell"><table class="grid-table budget-annual-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  el.scrollIntoView({ block: "nearest", behavior: "smooth" });
}
// 階段 1 歸戶：沒系統編號的預算，點「＋歸戶」→ 就地選案件 → 掛上即有系統編號
// 列上「共同費用/分攤」連結：就地開分攤（跟「年度費用/比較」並排，另一條路是 資料管理›費用分攤）
document.querySelector("#budgets")?.addEventListener("click", (event) => {
  const view = event.target.closest("[data-alloc-view]");
  if (view) { loadBudgetAllocations(view.getAttribute("data-alloc-view"), "#budget-annual-alloc"); return; }
});
// 專案清單「細項」捷徑：跳去進度總表看該專案的工作項細節（跟全文搜尋比對到子項目時同一套導覽）。
document.querySelector("#projects-list")?.addEventListener("click", async (event) => {
  const view = event.target.closest("[data-view-items]");
  if (!view) return;
  navigateToPanel("cases-module");
  await openProjectItem(view.getAttribute("data-view-items"));
});
// 專案歸戶（比照預算既有機制）：沒掛案件的專案點「＋歸戶」→ 就地選案件 → 掛上即有系統編號，
// 掛好之後線性進度圖/處理優先矩陣的「專案」那顆燈才會亮（那兩張圖只認案件底下掛的資料）。
document.querySelector("#projects-list")?.addEventListener("click", (event) => {
  const assign = event.target.closest("[data-assign-project-case]");
  if (!assign) return;
  const id = assign.getAttribute("data-assign-project-case");
  const opts = `<option value="">選案件…</option>`
    + (caseCache || []).map((c) => `<option value="${c.id}">${escapeHtml(c.case_code)}｜${escapeHtml(c.title || "")}</option>`).join("");
  assign.outerHTML = `<select class="btn-sm" data-assign-project-case-select="${id}">${opts}</select>`;
});
document.querySelector("#projects-list")?.addEventListener("change", async (event) => {
  const sel = event.target.closest("[data-assign-project-case-select]");
  if (!sel || !sel.value) return;
  try {
    await api(`/api/projects/${sel.getAttribute("data-assign-project-case-select")}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ case_id: Number(sel.value) }),
    });
    await loadResource("project");  // 重載→系統編號就出現
  } catch (error) { window.alert(`歸戶失敗：${error.message}`); }
});
document.querySelector("#budgets")?.addEventListener("click", (event) => {
  const assign = event.target.closest("[data-assign-case]");
  if (!assign) return;
  const id = assign.getAttribute("data-assign-case");
  const opts = `<option value="">選案件…</option>`
    + (caseCache || []).map((c) => `<option value="${c.id}">${escapeHtml(c.case_code)}｜${escapeHtml(c.title || "")}</option>`).join("");
  assign.outerHTML = `<select class="btn-sm" data-assign-case-select="${id}">${opts}</select>`;
});
document.querySelector("#budgets")?.addEventListener("change", async (event) => {
  const sel = event.target.closest("[data-assign-case-select]");
  if (!sel || !sel.value) return;
  try {
    await api(`/api/budgets/${sel.getAttribute("data-assign-case-select")}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ case_id: Number(sel.value) }),
    });
    await loadResource("budget");  // 重載→系統編號就出現
  } catch (error) { window.alert(`歸戶失敗：${error.message}`); }
});

// 點預算列的「比較」→ 讀衍生資料展開；收起清空
document.querySelector("#budgets")?.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-annual]");
  if (!btn) return;
  try {
    const data = (await api(`/api/budgets/${btn.getAttribute("data-annual")}/annual`)).data;
    renderBudgetAnnual(data);
  } catch (error) {
    const el = document.querySelector("#budget-annual");
    if (el) el.innerHTML = `<p class="muted">載入失敗：${escapeHtml(error.message)}</p>`;
  }
});
async function saveBudgetPeriods() {
  const el = document.querySelector("#budget-annual");
  const budgetId = el.dataset.budgetId;
  const status = document.querySelector("#pe-status");
  const rows = [];
  el.querySelectorAll(".pe-row").forEach((tr) => {
    const year = tr.querySelector(".pe-year").value.trim();
    if (!year) return;
    tr.querySelectorAll(".pe-amt").forEach((inp) => {
      rows.push({ fiscal_year: year, period: inp.getAttribute("data-period"), amount: Number(inp.value) || 0 });
    });
  });
  if (status) status.textContent = "儲存中…";
  try {
    await api(`/api/budgets/${budgetId}/periods`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ periods: rows }),
    });
    const data = (await api(`/api/budgets/${budgetId}/annual`)).data;
    annualEditMode = false;
    renderBudgetAnnual(data);
  } catch (error) {
    if (status) status.textContent = `儲存失敗：${error.message}`;
  }
}

document.querySelector("#budget-annual")?.addEventListener("click", async (event) => {
  const el = document.querySelector("#budget-annual");
  if (event.target.closest("#budget-annual-close")) {
    el.innerHTML = "";
    delete el.dataset.budgetId;
    annualData = null; annualSort = { col: null, dir: "asc" }; annualEditMode = false;
    const allocBox = document.querySelector("#budget-annual-alloc");
    if (allocBox) allocBox.innerHTML = "";
    return;
  }
  // 進編輯模式
  if (event.target.closest("#budget-annual-edit") && annualData) {
    annualEditMode = true; renderBudgetAnnual(annualData); return;
  }
  // 取消編輯：重讀丟棄未存
  if (event.target.closest("#pe-cancel")) {
    annualEditMode = false;
    try { renderBudgetAnnual((await api(`/api/budgets/${el.dataset.budgetId}/annual`)).data); } catch (_e) { /* ignore */ }
    return;
  }
  // 新增一年
  if (event.target.closest("#pe-add")) {
    const periods = JSON.parse(el.dataset.periods || "[]");
    document.querySelector("#pe-body")?.insertAdjacentHTML("beforeend", budgetPeriodRowHtml(periods, null));
    return;
  }
  // 刪一年（列）
  if (event.target.closest(".pe-remove")) {
    event.target.closest(".pe-row")?.remove(); return;
  }
  // 儲存明細
  if (event.target.closest("#pe-save")) { saveBudgetPeriods(); return; }
  // 點欄名排序（檢視模式）
  const th = event.target.closest("th[data-annual-sort]");
  if (th && annualData && !annualEditMode) {
    const col = th.getAttribute("data-annual-sort");
    annualSort = annualSort.col === col ? { col, dir: annualSort.dir === "asc" ? "desc" : "asc" } : { col, dir: "asc" };
    renderBudgetAnnual(annualData);
  }
});
// 備註即時存：input 失焦/改動就 PUT（主管/助理可寫）
document.querySelector("#budget-annual")?.addEventListener("change", async (event) => {
  const input = event.target.closest(".budget-note-input");
  if (!input) return;
  const el = document.querySelector("#budget-annual");
  const budgetId = el.dataset.budgetId;
  if (!budgetId) return;
  input.classList.remove("saved", "save-failed");
  try {
    await api(`/api/budgets/${budgetId}/annual-note`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fiscal_year: input.getAttribute("data-year"), note: input.value }),
    });
    input.classList.add("saved");
    // 同步到記憶體資料，之後排序重繪不會把剛存的備註洗掉
    const yr = (annualData && annualData.years || []).find((y) => y.fiscal_year === input.getAttribute("data-year"));
    if (yr) yr.note = input.value;
  } catch (error) {
    input.classList.add("save-failed");
    input.title = `存檔失敗：${error.message}`;
  }
});

// 後台「資料管理」底下的工具面板（沒有各自的側欄卡片，改由資料管理頁的磚塊開啟）
const BACKOFFICE_PANELS = new Set(["io-center", "unit-admin", "data-review", "fee-alloc", "name-admin"]);

// 只切換面板顯示（不動側欄 active）——給有卡片、無卡片兩種入口共用
function showModulePanel(targetId) {
  for (const panel of modulePanels) {
    const isActive = panel.id === targetId;
    panel.hidden = !isActive;
    panel.classList.toggle("active-module", isActive);
  }
  for (const extra of moduleExtras) {
    extra.hidden = extra.dataset.moduleParent !== targetId;
  }
  lastPanelId = targetId;
  window.scrollTo({ top: 0, left: 0, behavior: "instant" });
}

function activateModuleCard(card) {
  if (!card || card.hidden) return;
  const targetId = ("unbuilt" in card.dataset) ? "module-unbuilt" : card.getAttribute("href")?.replace("#", "");
  for (const moduleCard of moduleCards) {
    moduleCard.classList.toggle("active", moduleCard === card);
  }
  showModulePanel(targetId);
}

// 開啟後台工具：側欄「資料管理」卡維持 active，面板切到工具本身
function openBackofficeTool(panelId) {
  const daCard = document.querySelector('a.module-card[href="#data-admin"]');
  for (const moduleCard of moduleCards) moduleCard.classList.toggle("active", moduleCard === daCard);
  showModulePanel(panelId);
  if (panelId === "unit-admin") loadUnitConflicts();
  if (panelId === "fee-alloc") loadFeeAllocPicker();
  if (panelId === "name-admin") loadNameCleaning();
}

// 統一導覽：後台工具走 openBackofficeTool，其餘走各自卡片
function navigateToPanel(panelId) {
  if (!panelId) return;
  if (BACKOFFICE_PANELS.has(panelId)) { openBackofficeTool(panelId); return; }
  document.querySelector(`.module-card[href="#${panelId}"]`)?.click();
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
  // 案件管理內的分頁：「主管儀表板」是決策彙總資訊（單位別預算vs實付、廠商別合約金額等），
  // 承辦不需要看到；其餘分頁（案件清單/待辦/線性進度圖/矩陣/進度總表/一條龍新案）不分角色都看得到。
  let dashboardTabHidden = false;
  for (const tab of caseTabs) {
    const roles = tab.getAttribute("data-roles");
    if (!roles) continue;
    const allowed = roles.split(/\s+/).includes(user.role_code);
    tab.hidden = !allowed;
    if (tab.dataset.caseTab === "dashboard" && !allowed) dashboardTabHidden = true;
  }
  if (dashboardTabHidden && document.querySelector('[data-case-tab="dashboard"]')?.classList.contains("active")) {
    activateCaseTab("list");
  }
  // 後台「資料管理」磚塊：依 allowed_modules 過濾（承辦只看得到資料檢核）
  for (const tile of document.querySelectorAll(".admin-tile[data-panel-gate]")) {
    const gate = tile.getAttribute("data-panel-gate");
    tile.hidden = allowedModules.size ? !allowedModules.has(gate) : false;
  }
  // 示範資料工具只給主管/助理（有 edit）；CIO 唯讀、承辦被後端擋，也不顯示。
  if (demoControls) {
    demoControls.hidden = user.role_code !== "manager_assistant";
  }
  // AI 測試資料清除，同樣只給主管/助理。
  if (testDataControls) {
    testDataControls.hidden = user.role_code !== "manager_assistant";
  }
  // 舊資料補號同樣只給主管/助理；顯示時載入「還缺幾筆」。
  if (backfillControls) {
    backfillControls.hidden = user.role_code !== "manager_assistant";
    if (!backfillControls.hidden) loadBackfillStatus();
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
  loginUser.textContent = `登入身分：${user.display_name || user.username}（${user.role_name}）`;
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

// 登入頁：用下拉選角色。試辦免密碼時隱藏密碼欄；否則顯示。
async function loadLoginOptions() {
  const roleSel = document.querySelector("#login-role");
  const passWrap = document.querySelector("#login-pass-wrap");
  const hint = document.querySelector("#login-hint");
  if (!roleSel) return;
  try {
    const opt = (await api("/api/auth/options")).data;
    roleSel.innerHTML = (opt.accounts || [])
      .map((a) => `<option value="${escapeHtml(a.username)}">${escapeHtml(a.label)}（${escapeHtml(a.username)}）</option>`)
      .join("");
    const passwordless = !!opt.passwordless;
    if (passWrap) passWrap.hidden = passwordless;
    if (hint) hint.textContent = passwordless ? "選好角色按登入即可（試辦模式免密碼）。" : "選好角色、輸入密碼後登入。";
  } catch (_error) {
    // 取不到選項就退回可自由輸入：把下拉換成文字框，避免完全卡死
    roleSel.innerHTML = `<option value="ap02">主管/助理（ap02）</option>`;
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
        password: formData.get("password") || "",
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

// Excel 來源勾稽：匯入的案件有記來源檔＋列號時顯示 📎，滑過看「來源檔｜第N列」，提醒回 Excel 核對
function sourceTag(item) {
  const file = String((item && item.source_file) || "").trim();
  if (!file) return "";
  const row = Number((item && item.source_row) || 0);
  const loc = row ? `${file}｜第 ${row} 列` : file;
  return ` <span class="source-tag" title="Excel 來源：${escapeHtml(loc)}（回原檔核對）" role="img" aria-label="Excel 來源 ${escapeHtml(loc)}">📎</span>`;
}

// 案件列：跟其他清單(預算/合約...)一樣用 .grid-table 表格化，欄位各有自己的位置，
// 不要像以前那樣用 flex/grid 卡片擠在一起（曾經 6 個欄位只設定 5 個 grid-template-columns，
// 案號徽章跟案件編號會疊在一起）。
function renderCaseRow(item) {
  const statusClass = item.status === "approved" ? "ok" : item.status === "pending_review" ? "warn" : item.status === "disabled" ? "neutral" : "";
  return `<tr data-case-id="${item.id}">
    <td class="col-narrow"><span class="badge" title="案號（年度-流水號）＝這個案的身分證，各階段共用">${escapeHtml(caseNumber(item) || "—")}</span></td>
    <td class="col-narrow"><strong>${escapeHtml(item.case_code)}</strong>${sourceTag(item)}</td>
    <td>${escapeHtml(item.title)}</td>
    <td class="col-narrow muted">${escapeHtml(item.owner || "未指派")}</td>
    <td class="col-narrow"><span class="badge ${statusClass}">${escapeHtml(STATUS_LABELS[item.status] || item.status)}</span></td>
    <td class="col-actions">
      <span class="row-actions">
        ${caseWorkflowButtons(item)}
        <button type="button" class="icon-btn" data-action="trace" title="追溯鏈" aria-label="追溯鏈">${ICON_TRACE}</button>
        <button type="button" class="icon-btn" data-action="edit" title="編輯" aria-label="編輯">${ICON_EDIT}</button>
        <button type="button" class="icon-btn" data-action="disable" title="停用" aria-label="停用">${ICON_DISABLE}</button>
        <button type="button" class="icon-btn danger" data-action="delete" title="刪除" aria-label="刪除">${ICON_DELETE}</button>
      </span>
    </td>
  </tr>`;
}

async function loadCases() {
  const payload = await api("/api/cases");
  caseCache = payload.data;
  cases.innerHTML = caseCache.length
    ? `<div class="grid-scroll"><table class="grid-table">
        <thead><tr><th class="col-narrow">案號</th><th class="col-narrow">案件編號</th><th>案件名稱</th><th class="col-narrow">負責人</th><th class="col-narrow">狀態</th><th class="col-actions">操作</th></tr></thead>
        <tbody>${caseCache.map(renderCaseRow).join("")}</tbody>
      </table></div>`
    : `<p class="muted">目前沒有案件資料。</p>`;
  renderCioTable();
}

// 作業年度：新案件「所屬年度」的預設；顯示＋可改
async function loadWorkingYear() {
  try {
    const y = (await api("/api/working-year")).data.working_year || "";
    setText("#working-year-label", y);
    const fy = document.querySelector('#case-form [name="fiscal_year"]');
    if (fy) fy.placeholder = `所屬年度（空＝作業年度 ${y}）`;
  } catch (_e) { /* ignore */ }
}
document.querySelector("#working-year-edit")?.addEventListener("click", async () => {
  const cur = document.querySelector("#working-year-label")?.textContent || "";
  const y = window.prompt("設定目前作業年度（四位數字，例如 2027）：", cur);
  if (!y) return;
  try {
    await api(`/api/working-year?year=${encodeURIComponent(y.trim())}`, { method: "POST" });
    await loadWorkingYear();
  } catch (error) { window.alert(`設定失敗：${error.message}`); }
});

// 關聯案件下拉：把各表單的 .case-picker 填成「案件編號｜名稱」，保留原選值（供編輯）
let caseOptionsCache = [];
async function loadCaseOptions() {
  const pickers = document.querySelectorAll(".case-picker");
  if (!pickers.length) return;
  let list = [];
  try { list = (await api("/api/cases")).data || []; } catch (_e) { return; }
  caseOptionsCache = list;
  const opts = `<option value="">（不關聯案件）</option>` +
    list.map((c) => `<option value="${c.id}">${escapeHtml(c.case_code)}｜${escapeHtml(c.title || "")}</option>`).join("");
  for (const sel of pickers) {
    const cur = sel.value;
    sel.innerHTML = opts;
    if (cur) sel.value = cur;
  }
}

// 簽呈/請購串接（方案A：只存關聯不重做簽核系統）：請購表單可選「這是哪張簽呈核准的」、
// 合約表單可選「這是哪筆請購變成的」，兩條都可選填，供 Case 360 追溯鏈串出完整舉證鏈。
async function loadSignoffOptions() {
  const pickers = document.querySelectorAll(".signoff-picker");
  if (!pickers.length) return;
  let list = [];
  try { list = (await api("/api/signoffs")).data || []; } catch (_e) { return; }
  const opts = `<option value="">（不關聯簽呈）</option>` +
    list.map((s) => `<option value="${s.id}">${escapeHtml(s.signoff_code)}｜${escapeHtml(s.subject || "")}</option>`).join("");
  for (const sel of pickers) {
    const cur = sel.value;
    sel.innerHTML = opts;
    if (cur) sel.value = cur;
  }
}

async function loadPurchaseOptions() {
  const pickers = document.querySelectorAll(".purchase-picker");
  if (!pickers.length) return;
  let list = [];
  try { list = (await api("/api/purchases")).data || []; } catch (_e) { return; }
  const opts = `<option value="">（不關聯請購）</option>` +
    list.map((p) => `<option value="${p.id}">${escapeHtml(p.purchase_code)}｜${escapeHtml(p.item_name || "")}</option>`).join("");
  for (const sel of pickers) {
    const cur = sel.value;
    sel.innerHTML = opts;
    if (cur) sel.value = cur;
  }
}

// 案名沿用：選了案子，若該表單的「名稱」欄目前是空的，就帶入案名當預設值（仍可改，不鎖死）。
// 只套用在概念上「跟案子同一個代稱」的欄位——合約名稱/專案名稱/簽呈主旨；預算編號、請購品項、
// 文件檔名性質不同（同一案底下本來就會有多筆不同名稱的預算/品項），不套用。
const CASE_NAME_AUTOFILL_FIELD = { "contract-form": "contract_name", "project-form": "project_name", "signoff-form": "subject" };
document.addEventListener("change", (event) => {
  const picker = event.target.closest(".case-picker");
  if (!picker) return;
  const form = picker.closest("form");
  // 注意：form.id 這個 DOM 屬性會被表單裡 <input name="id"> 遮蔽（每個 resource-form 都有這欄位
  // 記編輯中的列 id），拿到的會是那個 input 元素、不是字串，一定要用 getAttribute("id")。
  const fieldName = form && CASE_NAME_AUTOFILL_FIELD[form.getAttribute("id")];
  if (!fieldName) return;
  const nameEl = form.elements[fieldName];
  if (!nameEl || nameEl.value.trim()) return;  // 已經有值就不覆蓋，避免蓋掉使用者已填的
  const c = caseOptionsCache.find((x) => String(x.id) === String(picker.value));
  if (c && c.title) nameEl.value = c.title;
});

// 追溯鏈：從案件一路看 簽呈 ▸ 請購 ▸ 合約 ▸ 付款（用 case_360 的聚合）。
// 編輯經理：每一筆都可點「編輯」直接開對應模組表單；缺的階段可點「＋新增」帶入本案／案名，
// 一段一段各自獨立送出（沿用各模組既有 PATCH/POST，不做整批 atomic 交易）。
let traceCaseId = null;
let traceLatestContractId = null;
async function loadCaseTrace(caseId) {
  const box = document.querySelector("#case-trace");
  if (!box) return;
  box.innerHTML = `<p class="muted">載入追溯鏈…</p>`;
  try {
    const d = (await api(`/api/cases/${caseId}/360`)).data || {};
    const c = d.case || {};
    const t = d.totals || {};
    traceCaseId = c.id;
    traceLatestContractId = (d.contracts && d.contracts[0]) ? d.contracts[0].id : null;
    const n = (a) => (a || []).length;
    const chip = (label, count, amount) =>
      `<div class="trace-node"><span class="trace-count">${count}</span><span class="trace-label">${label}</span>${amount != null ? `<span class="trace-amt">${money(amount)} 元</span>` : ""}</div>`;
    const editBtn = (type, id) => ` <button type="button" class="link-btn" data-trace-edit="${type}" data-trace-id="${id}">編輯</button>`;
    // 簽呈/請購串接（方案A）：合約若關聯請購、請購若關聯簽呈，在項目後面標出來源，讓「這筆付款是哪張簽呈核准的」追得回去。
    const sourceTag = (label, id, arr, codeField) => {
      if (!id) return "";
      const row = (arr || []).find((x) => x.id === id);
      return ` <span class="muted">← ${label} ${escapeHtml(row ? row[codeField] : `#${id}`)}</span>`;
    };
    const listOf = (arr, type, fn, empty) => (arr && arr.length)
      ? arr.map((row) => `<li>${fn(row)}${editBtn(type, row.id)}</li>`).join("")
      : `<li class="muted">${empty}${addBtn(type)}</li>`;
    const addBtn = (type) => {
      if (type === "payment" && !traceLatestContractId) return "";  // 沒有合約，無法帶合約 id，不給捷徑
      return ` <button type="button" class="link-btn" data-trace-add="${type}">＋新增（帶入本案）</button>`;
    };
    box.innerHTML = `
      <div class="trace-panel">
        <div class="section-heading compact">
          <h3>追溯鏈：${escapeHtml(c.case_code || "")}　${escapeHtml(c.title || "")}</h3>
          <button type="button" class="secondary btn-sm" id="trace-close">收起</button>
        </div>
        <p class="muted">點項目可直接編輯，或用「＋新增」補齊缺的階段。</p>
        <div class="trace-chain">
          ${chip("預算", n(d.budgets), t.budget_amount)}<span class="trace-arrow">▸</span>
          ${chip("專案", n(d.projects), null)}<span class="trace-arrow">▸</span>
          ${chip("簽呈", n(d.signoffs), t.signoff_amount)}<span class="trace-arrow">▸</span>
          ${chip("請購", n(d.purchases), t.purchase_amount)}<span class="trace-arrow">▸</span>
          ${chip("合約", n(d.contracts), t.contract_amount)}<span class="trace-arrow">▸</span>
          ${chip("付款", n(d.payments), t.payment_amount)}
        </div>
        <div class="trace-lists">
          <div><h4>預算</h4><ul class="note-list">${listOf(d.budgets, "budget", (b) => `<strong>${escapeHtml(b.budget_code)}</strong> ${escapeHtml(valueOrDash(b.unit_name))}｜${money(b.amount)} 元`, "無關聯預算——在「預算」模組把它關聯到本案件")}</ul></div>
          <div><h4>專案</h4><ul class="note-list">${listOf(d.projects, "project", (p) => `<strong>${escapeHtml(p.project_code)}</strong> ${escapeHtml(p.project_name || "")}｜${escapeHtml(labelStatus(p.status))}`, "無關聯專案")}</ul></div>
          <div><h4>簽呈</h4><ul class="note-list">${listOf(d.signoffs, "signoff", (s) => `<strong>${escapeHtml(s.signoff_code)}</strong> ${escapeHtml(s.subject || "")}｜${money(s.amount)} 元｜${escapeHtml(labelStatus(s.status))}${s.attachment_ref ? "｜" + attachmentLink(s.attachment_ref) : ""}`, "無關聯簽呈——在「簽呈」模組把它關聯到本案件")}</ul></div>
          <div><h4>請購</h4><ul class="note-list">${listOf(d.purchases, "purchase", (p) => `<strong>${escapeHtml(p.purchase_code)}</strong> ${escapeHtml(p.item_name || "")}｜廠商 ${escapeHtml(valueOrDash(p.vendor_name))}｜${money(p.amount)} 元${sourceTag("簽呈", p.signoff_id, d.signoffs, "signoff_code")}`, "無關聯請購")}</ul></div>
          <div><h4>合約</h4><ul class="note-list">${listOf(d.contracts, "contract", (k) => `<strong>${escapeHtml(k.contract_code)}</strong> ${escapeHtml(k.contract_name || "")}｜廠商 ${escapeHtml(valueOrDash(k.vendor_name))}｜${money(k.amount)} 元${sourceTag("請購", k.purchase_id, d.purchases, "purchase_code")}`, "無關聯合約")}</ul></div>
          <div><h4>付款</h4><ul class="note-list">${listOf(d.payments, "payment", (p) => `${escapeHtml(p.payment_month)}｜${money(p.payment_amount)} 元｜${escapeHtml(labelStatus(p.status))}`, traceLatestContractId ? "無付款紀錄" : "無付款紀錄（需先建立合約才能新增付款）")}</ul></div>
        </div>
      </div>`;
    box.scrollIntoView({ block: "nearest" });
  } catch (error) {
    box.innerHTML = `<p class="muted">追溯鏈載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

// 編輯經理：把表單（新增用途）預帶本案關聯，並在有案名沿用機制的表單觸發 change 讓案名帶入。
function presetCaseOnForm(type, caseId, contractId) {
  const targetForm = resourceForms[type];
  if (!targetForm) return;
  const casePicker = targetForm.querySelector(".case-picker");
  if (casePicker) {
    casePicker.value = String(caseId);
    casePicker.dispatchEvent(new Event("change", { bubbles: true }));
  }
  if (type === "payment" && contractId && targetForm.elements.contract_id) {
    targetForm.elements.contract_id.value = contractId;
  }
}

document.querySelector("#case-trace")?.addEventListener("click", async (event) => {
  if (event.target.closest("#trace-close")) { document.querySelector("#case-trace").innerHTML = ""; return; }
  const editBtn = event.target.closest("[data-trace-edit]");
  if (editBtn) {
    const type = editBtn.getAttribute("data-trace-edit");
    const id = editBtn.getAttribute("data-trace-id");
    const nav = SEARCH_NAV[type];
    if (!nav) return;
    navigateToPanel(nav.href.replace("#", ""));
    await nav.open(id);
    resourceForms[type]?.scrollIntoView({ block: "center", behavior: "smooth" });
    return;
  }
  const addBtn = event.target.closest("[data-trace-add]");
  if (addBtn) {
    const type = addBtn.getAttribute("data-trace-add");
    const nav = SEARCH_NAV[type];
    if (!nav) return;
    navigateToPanel(nav.href.replace("#", ""));
    setManualForm(resourceForms[type], true);
    presetCaseOnForm(type, traceCaseId, traceLatestContractId);
    resourceForms[type]?.scrollIntoView({ block: "center", behavior: "smooth" });
  }
});

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
// 每個表格的排序狀態：{col: 欄索引, dir: "asc"|"desc"}
const resourceSort = {};
const _sortProbe = document.createElement("div");
function cellText(type, item, colIdx) {
  _sortProbe.innerHTML = resourceConfig[type].columns[colIdx].cell(item);
  return (_sortProbe.textContent || "").trim();
}
// 只由「純數字＋千分位/元/%/空白/負號」組成才當數字比，否則字串比（中文用 localeCompare）
function looksNumeric(s) { return /\d/.test(s) && /^[0-9.,\s元%+-]+$/.test(s); }
function sortItems(type, items) {
  const st = resourceSort[type];
  if (!st) return items;
  const arr = [...items];
  arr.sort((a, b) => {
    const va = cellText(type, a, st.col), vb = cellText(type, b, st.col);
    let r;
    if (looksNumeric(va) && looksNumeric(vb)) {
      r = (parseFloat(va.replace(/[^0-9.-]/g, "")) || 0) - (parseFloat(vb.replace(/[^0-9.-]/g, "")) || 0);
    } else if (!va || !vb) {
      r = (va ? 1 : 0) - (vb ? 1 : 0);  // 空值排最後
    } else {
      r = va.localeCompare(vb, "zh-Hant");
    }
    return st.dir === "desc" ? -r : r;
  });
  return arr;
}
function renderResourceTable(type, items) {
  const config = resourceConfig[type];
  const st = resourceSort[type];
  const head = config.columns
    .map((c, i) => {
      const arrow = st && st.col === i ? (st.dir === "asc" ? " ▲" : " ▼") : "";
      return `<th class="sortable${c.cls ? " " + c.cls : ""}" data-sort-type="${type}" data-col-index="${i}" title="點欄名可排序">${c.label}${arrow}</th>`;
    })
    .join("");
  const body = sortItems(type, items).map((item) => renderResourceRow(type, item)).join("");
  return `
    <div class="grid-scroll">
      <table class="grid-table">
        <thead><tr>${head}<th class="col-actions">操作</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
    </div>
  `;
}
// 點欄名排序（切換 asc/desc），由快取重繪、不重打 API
document.addEventListener("click", (event) => {
  const th = event.target.closest("th.sortable");
  if (!th) return;
  const type = th.getAttribute("data-sort-type");
  if (!type) return;  // CIO 案件表也用 sortable 樣式但走另一套（data-cio-col），這裡略過
  const col = Number(th.getAttribute("data-col-index"));
  const st = resourceSort[type];
  resourceSort[type] = (st && st.col === col) ? { col, dir: st.dir === "asc" ? "desc" : "asc" } : { col, dir: "asc" };
  if (resourceLists[type] && resourceCaches[type]) {
    resourceLists[type].innerHTML = resourceCaches[type].length
      ? renderResourceTable(type, resourceCaches[type]) : emptyList(resourceConfig[type].plural);
  }
});

function renderResourceRow(type, item) {
  const config = resourceConfig[type];
  const cells = config.columns
    .map((c) => `<td${c.cls ? ` class="${c.cls}"` : ""}>${c.cell(item)}</td>`)
    .join("");
  return `<tr data-${config.idAttr}="${item.id}">${cells}<td class="col-actions">${renderRowMenu(config, item)}</td></tr>`;
}

// 一鍵圖示鈕用內嵌 SVG（不吃字型、跨平台一致）；stroke=currentColor 會吃 .icon-btn 顏色
const ICON_EDIT = `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.5 2.5l3 3L6 13l-3.5.5L3 10z"/><path d="M9.5 3.5l3 3"/></svg>`;
const ICON_DISABLE = `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="5.5"/><line x1="4.1" y1="4.1" x2="11.9" y2="11.9" stroke-linecap="round"/></svg>`;
const ICON_DELETE = `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2.8 4.2h10.4M6 4.2V2.6h4v1.6M5 4.2l.5 9h5l.5-9"/></svg>`;
const ICON_TRACE = `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9.5a2.5 2.5 0 0 0 3.5 0l2-2a2.5 2.5 0 1 0-3.5-3.5l-1 1"/><path d="M10 6.5a2.5 2.5 0 0 0-3.5 0l-2 2a2.5 2.5 0 1 0 3.5 3.5l1-1"/></svg>`;

// 編輯／停用／刪除＝一排圖示鈕（一鍵，不用點兩次）；hover 顯示文字
function renderRowMenu(config, item) {
  const disableButton = config.canDisable
    ? `<button type="button" class="icon-btn" data-action="disable" data-resource-id="${item.id}" title="停用" aria-label="停用">${ICON_DISABLE}</button>`
    : "";
  return `<span class="row-actions">
    <button type="button" class="icon-btn" data-action="edit" data-resource-id="${item.id}" title="編輯" aria-label="編輯">${ICON_EDIT}</button>
    ${disableButton}
    <button type="button" class="icon-btn danger" data-action="delete" data-resource-id="${item.id}" title="刪除" aria-label="刪除">${ICON_DELETE}</button>
  </span>`;
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

// 單條＝專案的時間軸（左端=開始日、右端=結束日）：填色＝實際完成%，紅色▼=今天在時間軸上的位置
function pfBar(p, c) {
  const clamp = (v) => Math.min(100, Math.max(0, v));
  const today = c.noBasis ? "" : `<i class="pf-today" style="left:${clamp(c.expected)}%"></i>`;
  return `<span class="pf-bar"><i class="pf-fill ${c.tone}" style="width:${clamp(c.actual)}%"></i>${today}</span>`;
}

// 名稱下方的起訖日小字（沒日期就標「未設定起訖日」）
function pfDateLine(p, c) {
  if (c.hasDates) return `<span class="pf-daterange">${escapeHtml(p.start_date)} → ${escapeHtml(p.end_date)}</span>`;
  return `<span class="pf-daterange pf-nodate">未設定起訖日</span>`;
}

// 落後幅度＝排序權重：越落後越前；超前/完成/未排程往後（長官只需盯落後的）
function pfSortKey(c) { return c.actual >= 100 ? -2 : c.noBasis ? -1 : c.gap; }

function pfOverview(group) {
  const ranked = group.projects
    .map((p) => ({ p, c: pfStatus(p) }))
    .sort((a, b) => pfSortKey(b.c) - pfSortKey(a.c));
  const rows = ranked.map(({ p, c }) => `
      <div class="pf-row" data-pf-proj="${p.id}" title="點此看單一專案">
        <span class="pf-row-name"><span class="pf-dot ${c.tone}"></span><span class="pf-name-col"><span class="pf-name-txt">${escapeHtml(p.project_name)}</span>${pfDateLine(p, c)}</span></span>
        ${pfBar(p, c)}
        <span class="pf-row-tag"><span class="badge ${c.tone}">${escapeHtml(c.label)}</span></span>
      </div>`).join("");
  const legend = `<div class="pf-legend">
    <span><span class="pf-lg-fill"></span>填色＝實際完成度</span>
    <span><span class="pf-lg-today"></span>紅線▼＝今天在時間軸上的位置（填色在紅線左邊＝落後）</span>
    <span>條的左端＝開始日、右端＝結束日（名稱下方標出）</span>
  </div>`;
  return `<div class="pf-card"><div class="muted pf-card-head">${escapeHtml(group.name)}　全部專案（共 ${group.projects.length} 個）</div>${legend}${rows}</div>`;
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
      <div class="pf-items" id="pf-items" data-project-id="${p.id}"><p class="muted">載入工作項…</p></div>
    </div>`;
}

// 工作項清單（可維護）：進度總表點進去看到的 Excel 細節
const PF_ITEM_FIELDS = [
  ["item_name", "工作主項目", "text", true],
  ["owner", "負責人", "text"],
  ["start_date", "開始日 YYYY-MM-DD", "text"],
  ["end_date", "結束日 YYYY-MM-DD", "text"],
  ["exec_status", "執行進度（如：進行中/已完成）", "text"],
  ["progress", "完成度 %", "number"],
  ["rag", "燈號（綠/黃/紅）", "text"],
  ["risk_note", "關鍵風險點／備註", "text"],
  ["decision_needed", "需決策項目", "text"],
  ["support_needed", "需支援項目", "text"],
];
const canEditPortfolio = () => currentUser && (currentUser.allowed_actions || []).includes("edit");

async function loadProjectItems(projectId) {
  const box = document.querySelector("#pf-items");
  if (!box) return;
  try {
    const items = (await api(`/api/projects/${projectId}/items`)).data || [];
    box.innerHTML = renderItemsSection(projectId, items);
  } catch (error) {
    box.innerHTML = `<p class="muted">工作項載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

// 工作項表格：開始日/結束日拆兩欄才能各自排序；預設依「結束日離今天的遠近」排，越急迫的越前面
// （跟處理優先矩陣「橫軸=急迫度」同一個邏輯，不是單純日期由小到大)。
const PF_ITEM_COLUMNS = [
  { label: "工作主項目", key: "item_name" },
  { label: "負責人", key: "owner" },
  { label: "開始日", key: "start_date", cls: "num" },
  { label: "結束日", key: "end_date", cls: "num" },
  { label: "執行進度", key: "exec_status" },
  { label: "完成度", key: "progress", cls: "num" },
  { label: "追蹤事項", key: "track" },
];
let pfItemSort = null;  // {col, dir}；null＝用預設的「離今天近的先」排序

function pfItemTrackText(it) {
  return [it.risk_note, it.decision_needed, it.support_needed].filter(Boolean).join(" ");
}

function pfItemDefaultSort(items) {
  const today = Date.now();
  const dist = (d) => {
    const t = d ? new Date(d).getTime() : NaN;
    return Number.isNaN(t) ? Infinity : Math.abs(t - today);
  };
  return [...items].sort((a, b) => dist(a.end_date) - dist(b.end_date));
}

function sortPfItems(items) {
  if (!pfItemSort) return pfItemDefaultSort(items);
  const { col, dir } = pfItemSort;
  const key = PF_ITEM_COLUMNS[col].key;
  const arr = [...items];
  arr.sort((a, b) => {
    let r;
    if (key === "progress") {
      r = Number(a.progress || 0) - Number(b.progress || 0);
    } else if (key === "start_date" || key === "end_date") {
      const da = a[key] ? new Date(a[key]).getTime() : Infinity;
      const db = b[key] ? new Date(b[key]).getTime() : Infinity;
      r = da - db;
    } else {
      const va = key === "track" ? pfItemTrackText(a) : String(a[key] || "");
      const vb = key === "track" ? pfItemTrackText(b) : String(b[key] || "");
      r = va.localeCompare(vb, "zh-Hant");
    }
    return dir === "desc" ? -r : r;
  });
  return arr;
}

function renderItemsSection(projectId, items) {
  const editable = canEditPortfolio();
  const addBtn = editable
    ? `<button type="button" class="secondary" data-item-add="${projectId}"><span aria-hidden="true">＋</span> 新增工作項</button>`
    : "";
  const sorted = sortPfItems(items);
  const head = PF_ITEM_COLUMNS.map((c, i) => {
    const arrow = pfItemSort && pfItemSort.col === i ? (pfItemSort.dir === "asc" ? " ▲" : " ▼") : "";
    return `<th class="sortable${c.cls ? " " + c.cls : ""}" data-pf-sort-col="${i}" title="點欄名可排序">${c.label}${arrow}</th>`;
  }).join("");
  const rows = sorted.length
    ? sorted.map((it) => {
        const tone = ragTone(it.rag);
        const track = pfItemTrackText(it)
          ? [
              it.risk_note && `風險：${escapeHtml(it.risk_note)}`,
              it.decision_needed && `決策：${escapeHtml(it.decision_needed)}`,
              it.support_needed && `支援：${escapeHtml(it.support_needed)}`,
            ].filter(Boolean).join("　")
          : '<span class="muted">—</span>';
        const ops = editable
          ? `<button type="button" class="secondary" data-item-edit="${it.id}">編輯</button> <button type="button" class="danger" data-item-del="${it.id}">刪除</button>`
          : "—";
        return `<tr data-item-id="${it.id}">
          <td>${escapeHtml(it.item_name)}</td>
          <td>${escapeHtml(valueOrDash(it.owner))}</td>
          <td class="num">${escapeHtml(valueOrDash(it.start_date))}</td>
          <td class="num">${escapeHtml(valueOrDash(it.end_date))}</td>
          <td><span class="pf-dot ${tone}"></span> ${escapeHtml(valueOrDash(it.exec_status))}</td>
          <td class="num">${Number(it.progress || 0)}%</td>
          <td>${track}</td>
          <td class="col-actions">${ops}</td>
        </tr>`;
      }).join("")
    : `<tr><td colspan="8" class="muted">尚無工作項${editable ? "，可按右上「新增工作項」建立。" : "。"}</td></tr>`;
  return `
    <div class="pf-items-head"><strong>工作項（${items.length}）</strong>${addBtn}</div>
    <div class="grid-scroll">
      <table class="grid-table">
        <thead><tr>${head}<th class="col-actions">操作</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div id="pf-item-editor"></div>`;
}

function ragTone(v) {
  const s = String(v || "").trim();
  if (/紅|red|^r$/i.test(s)) return "danger";
  if (/黃|橘|amber|^a$/i.test(s)) return "warn";
  if (/綠|green|^g$/i.test(s)) return "ok";
  return "muted";
}

function openItemEditor(projectId, item) {
  const box = document.querySelector("#pf-item-editor");
  if (!box) return;
  const inputs = PF_ITEM_FIELDS.map(([name, ph, type, req]) =>
    `<input name="${name}" placeholder="${ph}" ${type === "number" ? 'type="number" min="0" max="100" step="1"' : ""} ${req ? "required" : ""} value="${item ? escapeHtml(item[name] ?? "") : ""}" />`).join("");
  box.innerHTML = `
    <form class="pf-item-form" data-project-id="${projectId}" data-item-id="${item ? item.id : ""}">
      <div class="pf-item-form-title">${item ? "編輯工作項" : "新增工作項"}</div>
      <div class="pf-item-grid">${inputs}</div>
      <div class="pf-item-actions">
        <button type="submit">儲存</button>
        <button type="button" class="secondary" data-item-cancel>取消</button>
      </div>
    </form>`;
  box.querySelector("input")?.focus();
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
  if (portfolioState.s === "ov") {
    viewEl.innerHTML = pfOverview(group);
  } else {
    const proj = group.projects[portfolioState.s];
    viewEl.innerHTML = pfDetail(proj);
    loadProjectItems(proj.id);  // 非同步補上工作項清單
  }
}

// 工作項維護：新增/編輯/刪除/儲存（承辦也可，直接生效）
document.querySelector("#pf-view")?.addEventListener("click", async (event) => {
  const sortTh = event.target.closest("th.sortable[data-pf-sort-col]");
  if (sortTh) {
    const col = Number(sortTh.getAttribute("data-pf-sort-col"));
    pfItemSort = (pfItemSort && pfItemSort.col === col)
      ? { col, dir: pfItemSort.dir === "asc" ? "desc" : "asc" }
      : { col, dir: "asc" };
    const pid = document.querySelector("#pf-items")?.getAttribute("data-project-id");
    if (pid) await loadProjectItems(Number(pid));
    return;
  }
  const add = event.target.closest("[data-item-add]");
  const edit = event.target.closest("[data-item-edit]");
  const del = event.target.closest("[data-item-del]");
  const cancel = event.target.closest("[data-item-cancel]");
  if (add) { openItemEditor(Number(add.getAttribute("data-item-add")), null); return; }
  if (edit) {
    const pid = document.querySelector("#pf-items")?.getAttribute("data-project-id");
    const items = (await api(`/api/projects/${pid}/items`)).data || [];
    const it = items.find((x) => String(x.id) === edit.getAttribute("data-item-edit"));
    if (it) openItemEditor(Number(pid), it);
    return;
  }
  if (del) {
    if (!window.confirm("確定刪除這個工作項？")) return;
    await api(`/api/project-items/${del.getAttribute("data-item-del")}`, { method: "DELETE" });
    const pid = document.querySelector("#pf-items")?.getAttribute("data-project-id");
    await loadProjectItems(Number(pid));
    return;
  }
  if (cancel) { const b = document.querySelector("#pf-item-editor"); if (b) b.innerHTML = ""; return; }
});

document.querySelector("#pf-view")?.addEventListener("submit", async (event) => {
  const form = event.target.closest(".pf-item-form");
  if (!form) return;
  event.preventDefault();
  const projectId = form.getAttribute("data-project-id");
  const itemId = form.getAttribute("data-item-id");
  const data = Object.fromEntries(new FormData(form).entries());
  if (data.progress !== undefined && data.progress !== "") data.progress = Number(data.progress);
  try {
    if (itemId) {
      await api(`/api/project-items/${itemId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    } else {
      await api(`/api/projects/${projectId}/items`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    }
    await loadProjectItems(Number(projectId));
  } catch (error) {
    window.alert(`儲存失敗：${error.message}`);
  }
});

// 全文搜尋比對到專案「工作項」子項時，導去進度總表點開那個專案（子項細節在這裡才看得到，
// 不是專案模組的基本編輯表單）——找到所屬組別/子分頁後設定 portfolioState 再重繪。
async function openProjectItem(projectId) {
  activateCaseTab("portfolio");
  if (!portfolioGroups.length) await loadPortfolio();
  for (let g = 0; g < portfolioGroups.length; g++) {
    const idx = portfolioGroups[g].projects.findIndex((p) => String(p.id) === String(projectId));
    if (idx >= 0) {
      portfolioState.g = g;
      portfolioState.s = idx;
      renderPortfolio();
      break;
    }
  }
  document.querySelector("#pf-items")?.scrollIntoView({ block: "center", behavior: "smooth" });
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
    btns.push(`<button type="button" class="secondary btn-sm" data-action="submit">送出複核</button>`);
  }
  if (item.status === "pending_review") {
    const isSubmitter = currentUser && (item.created_by || "") === currentUser.username;
    const isManager = currentUser && currentUser.role_code === "manager_assistant";
    if (isManager && !isSubmitter) {
      btns.push(`<button type="button" class="btn-sm" data-action="approve">核准</button>`);
    }
    if (isManager && isSubmitter) {
      btns.push(`<span class="muted" title="不能核准自己建立的案件">待他人複核</span>`);
    }
    // 取消複核（退回草稿）：原提交者或主管/助理都可以，不像核准有球員兼裁判風險
    if (isSubmitter || isManager) {
      btns.push(`<button type="button" class="secondary btn-sm" data-action="cancel-review">取消複核</button>`);
    }
  }
  return btns.join(" ");
}

async function loadTodo() {
  if (!todoList) return;
  const payload = await api("/api/todo");
  const items = payload.data || [];
  setText("#tile-count-todo", `匯入預檢・待辦 ${items.length}`);
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

let cioSort = { field: null, dir: "asc" };
function renderCioTable() {
  if (!cioCasesBody) return;
  let rows = [...caseCache];
  if (cioSort.field) {
    const f = cioSort.field;
    rows.sort((a, b) => {
      let r;
      if (f === "amount") {
        r = (Number(a.amount) || 0) - (Number(b.amount) || 0);
      } else {
        const pick = (x) => (f === "status" ? (STATUS_LABELS[x.status] || x.status || "") : String(x[f] || ""));
        const va = pick(a), vb = pick(b);
        r = (!va || !vb) ? (va ? 1 : 0) - (vb ? 1 : 0) : va.localeCompare(vb, "zh-Hant");
      }
      return cioSort.dir === "desc" ? -r : r;
    });
  }
  cioCasesBody.innerHTML = rows.length
    ? rows
        .map(
          (c, i) => `
            <tr data-case-id="${c.id}">
              <td>${i + 1}</td>
              <td>${escapeHtml(c.case_code)}${sourceTag(c)}</td>
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
  // 更新表頭排序箭頭（表頭是靜態 HTML，只更箭頭）
  document.querySelectorAll("#cio-cases-table th[data-cio-col]").forEach((th) => {
    const f = th.getAttribute("data-cio-col");
    const base = th.getAttribute("data-label") || th.textContent.replace(/[▲▼\s]+$/, "");
    th.setAttribute("data-label", base);
    th.innerHTML = base + (cioSort.field === f ? (cioSort.dir === "asc" ? " ▲" : " ▼") : "");
  });
}
// CIO 案件表點欄名排序（由快取重繪，不重打 API）
document.addEventListener("click", (event) => {
  const th = event.target.closest("#cio-cases-table th[data-cio-col]");
  if (!th) return;
  const field = th.getAttribute("data-cio-col");
  cioSort = cioSort.field === field
    ? { field, dir: cioSort.dir === "asc" ? "desc" : "asc" }
    : { field, dir: "asc" };
  renderCioTable();
});

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

// 單位別 預算 vs 實付：主管一眼看各單位錢花到哪、誰超支。年度下拉可篩「所屬年度」。
let unitBvaYear = "";  // "" = 全部年度
async function loadUnitBva() {
  const body = document.querySelector("#unit-bva-body");
  if (!body) return;
  const q = unitBvaYear ? `?year=${encodeURIComponent(unitBvaYear)}` : "";
  const data = (await api(`/api/reports/unit-budget-vs-actual${q}`)).data || {};
  // 年度下拉只建一次（保留使用者選取）
  const sel = document.querySelector("#unit-bva-year");
  if (sel && sel.options.length === 0) {
    sel.innerHTML = ['<option value="">全部年度</option>']
      .concat((data.years || []).map((y) => `<option value="${y}">${y} 年度</option>`))
      .join("");
    sel.value = unitBvaYear;
  }
  const fmt = (n) => Number(n || 0).toLocaleString();
  const rows = data.rows || [];
  const lines = rows.map((r) => {
    const usage = r.usage_pct == null ? "—" : `${r.usage_pct}%`;
    const over = r.over ? ' <span class="badge danger">超支</span>' : "";
    return `<tr${r.over ? ' class="over-budget"' : ""}>
      <td>${escapeHtml(r.unit)}</td>
      <td class="num">${fmt(r.budget)}</td>
      <td class="num">${fmt(r.paid)}</td>
      <td class="num">${fmt(r.pending)}</td>
      <td class="num">${fmt(r.remaining)}</td>
      <td class="num">${usage}${over}</td>
    </tr>`;
  });
  const ua = data.unattributed || {};
  if ((ua.paid || 0) || (ua.pending || 0)) {
    lines.push(`<tr>
      <td>未歸單位<span class="help" data-tip="這些付款的案件沒有掛任何預算，無法歸到單位；請到「預算」用「＋歸戶」把該案預算補上，或替該案建預算。" role="button" tabindex="0" aria-label="說明">?</span></td>
      <td class="num">—</td><td class="num">${fmt(ua.paid)}</td><td class="num">${fmt(ua.pending)}</td>
      <td class="num">—</td><td class="num">—</td></tr>`);
  }
  const t = data.totals || {};
  if (rows.length || lines.length) {
    lines.push(`<tr class="total-row">
      <td>合計</td>
      <td class="num">${fmt(t.budget)}</td>
      <td class="num">${fmt(t.paid)}</td>
      <td class="num">${fmt(t.pending)}</td>
      <td class="num">${fmt(t.remaining)}</td>
      <td class="num">${t.budget ? `${Math.round((t.paid / t.budget) * 100)}%` : "—"}</td>
    </tr>`);
  }
  body.innerHTML = lines.join("") || `<tr><td colspan="6" class="muted">目前沒有預算或付款資料。</td></tr>`;
}

document.querySelector("#unit-bva-year")?.addEventListener("change", (event) => {
  unitBvaYear = event.target.value;
  loadUnitBva();
});

// 廠商別 合約金額 vs 實付：不分年度（合約金額是存續期間總額，非逐年概念）。
async function loadVendorAmt() {
  const body = document.querySelector("#vendor-amt-body");
  if (!body) return;
  const data = (await api("/api/reports/vendor-amount-summary")).data || {};
  const fmt = (n) => Number(n || 0).toLocaleString();
  const rows = data.rows || [];
  const lines = rows.map((r) => {
    const usage = r.usage_pct == null ? "—" : `${r.usage_pct}%`;
    const over = r.over ? ' <span class="badge danger">超支</span>' : "";
    return `<tr${r.over ? ' class="over-budget"' : ""}>
      <td>${escapeHtml(r.vendor)}</td>
      <td class="num">${fmt(r.contract_amount)}</td>
      <td class="num">${fmt(r.paid)}</td>
      <td class="num">${fmt(r.pending)}</td>
      <td class="num">${fmt(r.remaining)}</td>
      <td class="num">${usage}${over}</td>
    </tr>`;
  });
  const t = data.totals || {};
  if (rows.length) {
    lines.push(`<tr class="total-row">
      <td>合計</td>
      <td class="num">${fmt(t.contract_amount)}</td>
      <td class="num">${fmt(t.paid)}</td>
      <td class="num">${fmt(t.pending)}</td>
      <td class="num">${fmt(t.remaining)}</td>
      <td class="num">${t.contract_amount ? `${Math.round((t.paid / t.contract_amount) * 100)}%` : "—"}</td>
    </tr>`);
  }
  body.innerHTML = lines.join("") || `<tr><td colspan="6" class="muted">目前沒有合約或付款資料。</td></tr>`;
}

// 待辦清單類（合約續約提醒／催辦清單）預設只顯示前 N 筆，其餘收在「展開」按鈕後面，避免一次全灌爆版面。
const EXPANDABLE_LIST_LIMIT = 5;
const expandableListState = {};  // key(如 "expiring") -> true 代表使用者已展開，重繪(refresh)時記得維持
function renderExpandableList(el, key, items, renderItem, emptyMsg) {
  if (!items.length) { el.innerHTML = `<li><small class="muted">${emptyMsg}</small></li>`; return; }
  const expanded = !!expandableListState[key];
  const shown = expanded ? items : items.slice(0, EXPANDABLE_LIST_LIMIT);
  const toggle = items.length > EXPANDABLE_LIST_LIMIT
    ? `<li class="expand-toggle"><button type="button" class="link-btn" data-expand-list="${key}">${expanded ? "收起" : `展開全部（共 ${items.length} 筆）`}</button></li>`
    : "";
  el.innerHTML = shown.map(renderItem).join("") + toggle;
}
document.addEventListener("click", (event) => {
  const btn = event.target.closest("[data-expand-list]");
  if (!btn) return;
  const key = btn.getAttribute("data-expand-list");
  expandableListState[key] = !expandableListState[key];
  if (key === "expiring") loadExpiring();
  if (key === "reminders") loadReminders();
});

async function loadExpiring() {
  const el = document.querySelector("#expiring-list");
  if (!el) return;
  const payload = await api("/api/reports/expiring-contracts");
  const items = payload.data || [];
  const today = new Date().toISOString().slice(0, 10);
  renderExpandableList(el, "expiring", items, (c) => {
    const overdue = c.end_date && c.end_date < today;
    return `
      <li>
        <span class="badge ${overdue ? "danger" : "warn"}">${overdue ? "已過期" : "快到期"}</span>
        <strong>${escapeHtml(c.contract_code)}　${escapeHtml(c.contract_name)}</strong>
        <small>到期日：${escapeHtml(c.end_date)}；廠商：${escapeHtml(c.vendor_name || "—")}；金額：${Number(c.amount || 0).toLocaleString()}</small>
      </li>`;
  }, "目前沒有快到期或已過期的合約。");
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
  if (currentUser && currentUser.role_code === "cio") await loadCioChanges();
}

// CIO「自上次查看以來」變動提醒：查看即視為已讀，下次只顯示這之後的變動。
async function loadCioChanges() {
  const el = document.querySelector("#cio-changes-banner");
  if (!el) return;
  const d = (await api("/api/reports/cio-changes-since-last-view")).data || {};
  if (d.first_visit) {
    el.hidden = false;
    el.textContent = "首次查看決策總覽：之後這裡會顯示「自上次查看以來」的變動摘要。";
    return;
  }
  const changes = d.changes || [];
  if (!changes.length) {
    el.hidden = false;
    el.textContent = `自上次查看（${escapeHtml(d.since)}）以來，沒有新變動。`;
    return;
  }
  const parts = changes
    .slice(0, 8)
    .map((c) => `${escapeHtml(c.table_label)}${escapeHtml(c.action_label)} ${c.count} 筆`);
  el.hidden = false;
  el.innerHTML = `<strong>自上次查看（${escapeHtml(d.since)}）以來共 ${d.total_count} 筆變動：</strong>${parts.join("、")}`;
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
  renderExpandableList(el, "reminders", items, (i) => {
    const kind = i.type === "case" ? "案件" : i.type === "project" ? "專案" : "合約";
    const tag = i.severity === "overdue" ? `已逾期 ${Math.abs(i.days)} 天` : `剩 ${i.days} 天`;
    return `
      <li>
        <span class="badge ${i.severity === "overdue" ? "danger" : "warn"}">${tag}</span>
        <strong>${escapeHtml(kind)}｜${escapeHtml(i.code)}　${escapeHtml(i.title)}</strong>
        <small>期限：${escapeHtml(i.date)}；負責人：${escapeHtml(i.owner || "未指派")}；狀態：${escapeHtml(labelStatus(i.status))}</small>
      </li>`;
  }, "目前沒有逾期或即將到期的催辦項目。");
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
    loadMappingCatalog(), loadTodo(), loadMonthly(), loadUnitBva(), loadVendorAmt(), loadExpiring(), loadCioOverview(), loadReminders(),
    loadManagerCharts(), loadPendingApprovals(), loadOrphanPayments(), loadAdminConsole(), loadOptions(),
    loadPortfolio(), loadUnitConflicts(), loadPersonnelMaster(), loadCaseOptions(), loadWorkingYear(),
    loadSignoffOptions(), loadPurchaseOptions(),
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

// 手動新增/編輯表單：平常收合、不佔版面；點「＋手動新增」或按清單「編輯」才展開
function setManualForm(formEl, open) {
  if (!formEl) return;
  const fid = formEl.getAttribute("id");  // 注意：form.id 會被表單內 <input name="id"> 遮蔽，須用 getAttribute
  formEl.hidden = !open;
  if (fid === "case-form") { const t = document.querySelector("#form-title"); if (t) t.hidden = !open; }
  const btn = document.querySelector(`[data-form-toggle="${fid}"]`);
  if (btn) btn.textContent = open ? "－ 收起" : "＋ 新增";
}
document.addEventListener("click", (event) => {
  const t = event.target.closest("[data-form-toggle]");
  if (!t) return;
  const formEl = document.getElementById(t.getAttribute("data-form-toggle"));
  setManualForm(formEl, !!formEl?.hidden);  // hidden → 打開
});

function resetForm() {
  form.reset();
  form.elements.id.value = "";
  formTitle.textContent = "新增案件";
  submitCase.textContent = "新增";
  cancelEdit.hidden = true;
  setManualForm(form, false);  // 取消後收合
}

function startEdit(id) {
  const item = caseCache.find((entry) => String(entry.id) === String(id));
  if (!item) return;
  setManualForm(form, true);  // 編輯時自動展開
  form.elements.id.value = item.id;
  if (form.elements.fiscal_year) form.elements.fiscal_year.value = item.fiscal_year || "";
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
  form.scrollIntoView({ block: "nearest" });
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
  setManualForm(targetForm, false);  // 取消後收合
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
  setManualForm(targetForm, true);  // 編輯時自動展開
  targetForm.elements.id.value = item.id;
  for (const field of config.fields) {
    const el = targetForm.elements[field];
    const val = item[field] ?? "";
    // select 若沒有這個值的選項（例如舊資料的單位名稱還沒登記進主檔），先補一個選項，
    // 避免編輯時看起來「值不見了」、存檔時被誤蓋成空白
    if (el.tagName === "SELECT" && val && ![...el.options].some((o) => o.value === String(val))) {
      el.add(new Option(`${val}（未登記）`, val));
    }
    el.value = val;
  }
  targetForm.querySelector('button[type="submit"]').textContent = "儲存";
  targetForm.querySelector("[data-cancel]").hidden = false;
  targetForm.scrollIntoView({ block: "nearest" });
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
  const item = (resourceCaches[type] || []).find((x) => String(x.id) === String(id));
  const label = item ? (item.budget_code || item.contract_code || item.settle_no || item.project_code || item.signoff_code || item.purchase_code || item.file_name || item.category || `#${id}`) : `#${id}`;
  if (action === "disable") {
    if (!window.confirm(`確定停用「${label}」？停用後不再出現在清單，可再啟用。`)) return;
    await api(`${config.api}/${id}/disable`, { method: "POST" });
  }
  if (action === "delete") {
    if (!window.confirm(`確定刪除「${label}」？此動作無法復原。`)) return;
    if (!window.confirm(`再次確認：真的要永久刪除「${label}」嗎？`)) return;
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

// 案件清單的匯入/匯出按鈕已移除（統一在「資料管理 › 匯入／匯出」），故不再綁 handler。

async function projXlsx(commit) {
  const file = document.querySelector("#proj-xlsx-file")?.files?.[0];
  const el = document.querySelector("#proj-xlsx-status");
  const commitBtn = document.querySelector("#proj-xlsx-commit");
  if (!file) { if (el) el.textContent = "請先選一個 .xlsx 檔"; return; }
  if (commit && !window.confirm("確定正式匯入？同名專案會更新、沒見過的會新增。")) return;
  if (el) el.textContent = commit ? "匯入中…" : "解析中…";
  try {
    const res = (await api(`/api/projects/import-xlsx?commit=${commit}`, { method: "POST", body: file })).data || {};
    if (commit) {
      if (el) el.textContent = `匯入完成：新增 ${res.created_count} 個、更新 ${res.updated_count} 個。`;
      await refresh();
    } else {
      const names = (res.sample || []).slice(0, 3).map((s) => s.project_name).join("、");
      if (el) el.textContent = res.count ? `預覽：共 ${res.count} 個專案${names ? "（例：" + names + "…）" : ""}` : "共 0 個——這個檔不像專案總表，請確認選了「…處級專案進度追蹤總表.xlsx」。";
      if (commitBtn) commitBtn.disabled = !res.count;
    }
  } catch (error) {
    if (el) el.textContent = `失敗：${error.message}`;
  }
}
document.querySelector("#proj-xlsx-preview")?.addEventListener("click", () => projXlsx(false));
document.querySelector("#proj-xlsx-commit")?.addEventListener("click", () => projXlsx(true));

// 預算匯入（表單型 xlsx）：作法同專案——預覽→正式匯入→同名更新
async function budgetXlsx(commit, ids) {
  const q = ids || { file: "#budget-xlsx-file", status: "#budget-xlsx-status", commitBtn: "#budget-xlsx-commit" };
  const file = document.querySelector(q.file)?.files?.[0];
  const el = document.querySelector(q.status);
  const commitBtn = document.querySelector(q.commitBtn);
  if (!file) { if (el) el.textContent = "請先選一個 .xlsx 檔"; return; }
  if (commit && !window.confirm("確定正式匯入？同名預算會更新、沒見過的會新增。")) return;
  if (el) el.textContent = commit ? "匯入中…" : "解析中…";
  try {
    const res = (await api(`/api/budgets/import-xlsx?commit=${commit}&filename=${encodeURIComponent(file.name)}`, { method: "POST", body: file })).data || {};
    if (commit) {
      if (el) el.textContent = `匯入完成：新增 ${res.created_count} 筆、更新 ${res.updated_count} 筆。`
        + `下一步：未歸戶的預算點各列「＋歸戶」發號；疑似重複名稱到「資料管理›名稱歸納›預算項目」清洗。`;
      await refresh();
    } else {
      const names = (res.sample || []).slice(0, 3).map((s) => s.budget_code).join("、");
      if (el) el.textContent = res.count ? `預覽：共 ${res.count} 筆預算${names ? "（例：" + names + "…）" : ""}` : "共 0 筆——這個檔不像費用項目表，請確認選了「一、預算.xlsx」（類別矩陣檔暫不支援）。";
      if (commitBtn) commitBtn.disabled = !res.count;
    }
  } catch (error) {
    if (el) el.textContent = `失敗：${error.message}`;
  }
}
document.querySelector("#budget-xlsx-preview")?.addEventListener("click", () => budgetXlsx(false));
document.querySelector("#budget-xlsx-commit")?.addEventListener("click", () => budgetXlsx(true));
// 預算模組內嵌匯入（B：不用跑去資料管理，就地匯入 Excel）
const BUD_INLINE_IDS = { file: "#bud-inline-file", status: "#bud-inline-status", commitBtn: "#bud-inline-commit" };
document.querySelector("#bud-inline-preview")?.addEventListener("click", () => budgetXlsx(false, BUD_INLINE_IDS));
document.querySelector("#bud-inline-commit")?.addEventListener("click", () => budgetXlsx(true, BUD_INLINE_IDS));

// ===== 共同費用分攤：以費用項目看（某預算攤給哪些單位）＋ 以單位看（部門負擔彙總）=====
// 容器可切換：fee-alloc 模組用 #budget-alloc；預算面板用 #budget-annual-alloc（分攤編輯就地做，不用跳資料管理）
let allocBoxSel = "#budget-alloc";
async function loadBudgetAllocations(budgetId, sel) {
  if (sel) allocBoxSel = sel;
  const box = document.querySelector(allocBoxSel);
  if (!box) return;
  box.innerHTML = `<p class="muted">載入分攤明細…</p>`;
  try {
    const al = (await api(`/api/budgets/${budgetId}/allocations`)).data || [];
    const bud = (resourceCaches.budget || []).find((b) => String(b.id) === String(budgetId));
    const total = al.reduce((s, a) => s + Number(a.amount_int || 0), 0);  // 整數欄合計＝項目總額
    const editable = currentUser && (currentUser.allowed_actions || []).includes("edit");
    const absorber = al.find((a) => a.is_remainder_unit);
    const method = bud ? (bud.alloc_method || "fixed") : "fixed";
    const methodLabel = { fixed: "固定金額", headcount: "按人數", category: "按類別" }[method] || method;
    const recomputeBtn = (editable && method !== "fixed")
      ? ` <button type="button" class="btn-sm" data-recompute="${budgetId}">重算分攤</button>`
      : "";
    // 分攤方法可改；選「按類別」再出類別下拉（台股/複委託/台複共用…）
    const methodCtl = editable
      ? `<label class="rem-ctl">分攤方法：
          <select data-alloc-method="${budgetId}">
            <option value="fixed"${method === "fixed" ? " selected" : ""}>固定金額</option>
            <option value="headcount"${method === "headcount" ? " selected" : ""}>按人數</option>
            <option value="category"${method === "category" ? " selected" : ""}>按類別</option>
          </select></label>`
      : "";
    let categoryCtl = "";
    if (editable && method === "category") {
      const cats = ((await api("/api/category-shares")).data || {}).categories || [];
      const cur = (bud && bud.alloc_category) || "";
      categoryCtl = `<label class="rem-ctl">分攤類別：
        <select data-alloc-category="${budgetId}">
          <option value=""${!cur ? " selected" : ""}>（請選類別）</option>
          ${cats.map((c) => `<option value="${escapeHtml(c.category)}"${c.category === cur ? " selected" : ""}>${escapeHtml(c.category)}（${c.units}單位）</option>`).join("")}
        </select></label>${cats.length ? "" : ` <span class="muted">尚未匯入類別基準表，請先到匯入/匯出匯入「對照表」。</span>`}`;
    }
    const rows = al.length
      ? al.map((a) => {
          const remTag = a.is_remainder_unit
            ? ` <span class="badge warn" title="整數化湊不齊的尾數歸此單位">含尾數 ${a.remainder >= 0 ? "+" : ""}${money(a.remainder)}</span>`
            : "";
          return `<tr>
          <td>${escapeHtml(valueOrDash(a.unit_code))}</td>
          <td>${escapeHtml(a.unit_name)}${remTag}</td>
          <td class="num">${Number(a.share_pct || 0)}%</td>
          <td class="num">${money(a.amount_int)} 元</td></tr>`;
        }).join("")
      : `<tr><td colspan="4" class="muted">這筆預算沒有分攤明細（可能是手動建立、或匯入時無分攤表）。</td></tr>`;
    const overrideCtl = (editable && al.length)
      ? `<label class="rem-ctl">尾數承擔單位：
           <select data-rem-budget="${budgetId}">
             ${al.map((a) => `<option value="${escapeHtml(a.unit_code)}"${absorber && a.unit_code === absorber.unit_code ? " selected" : ""}>${escapeHtml(a.unit_name)}（${escapeHtml(valueOrDash(a.unit_code))}）</option>`).join("")}
           </select>
         </label>`
      : "";
    box.innerHTML = `
      <div class="budget-alloc-head">
        <strong>${escapeHtml(bud ? bud.budget_code : "費用項目")}</strong> 的單位分攤（整數）
        <span class="muted">共 ${al.length} 個單位，合計 ${money(total)} 元 ｜ 方法：${methodLabel}</span>${recomputeBtn}
        <button type="button" class="secondary btn-sm" data-alloc-close>關閉</button>
      </div>
      <div class="alloc-ctls">${methodCtl}${categoryCtl}${overrideCtl}</div>
      <div class="grid-scroll"><table class="grid-table">
        <thead><tr><th>單位代碼</th><th>單位名稱</th><th>分攤%</th><th>分攤金額</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>`;
    box.scrollIntoView({ block: "nearest" });
  } catch (error) {
    box.innerHTML = `<p class="muted">分攤載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

async function loadBudgetUnitRollup(unitCode) {
  const box = document.querySelector("#budget-alloc");
  if (!box) return;
  box.innerHTML = `<p class="muted">載入單位彙總…</p>`;
  try {
    const data = (await api(`/api/budget-units${unitCode ? `?unit_code=${encodeURIComponent(unitCode)}` : ""}`)).data || {};
    const units = data.units || [];
    const grand = units.reduce((s, u) => s + Number(u.total_amount || 0), 0);
    const rows = units.length
      ? units.map((u) => `<tr>
          <td>${escapeHtml(valueOrDash(u.unit_code))}</td>
          <td><button type="button" class="link-btn" data-unit-code="${escapeHtml(u.unit_code)}">${escapeHtml(u.unit_name)}</button></td>
          <td class="num">${Number(u.item_count || 0)}</td>
          <td class="num">${money(u.total_amount)} 元</td></tr>`).join("")
      : `<tr><td colspan="4" class="muted">尚無分攤資料。請先匯入預算 Excel。</td></tr>`;
    let detailHtml = "";
    if (unitCode && data.detail) {
      const drows = data.detail.map((d) => `<tr>
        <td>${escapeHtml(valueOrDash(d.budget_code))}</td>
        <td>${escapeHtml(valueOrDash(d.category))}</td>
        <td class="num">${Number(d.share_pct || 0)}%</td>
        <td class="num">${money(d.amount)} 元</td></tr>`).join("");
      detailHtml = `<div class="budget-alloc-detail"><strong>單位 ${escapeHtml(unitCode)}</strong> 被攤的項目
        <div class="grid-scroll"><table class="grid-table">
          <thead><tr><th>費用項目</th><th>類別</th><th>分攤%</th><th>分攤金額</th></tr></thead>
          <tbody>${drows || '<tr><td colspan="4" class="muted">無</td></tr>'}</tbody>
        </table></div></div>`;
    }
    box.innerHTML = `
      <div class="budget-alloc-head">
        <strong>單位分攤彙總（部門負擔表）</strong>
        <span class="muted">共 ${units.length} 個單位，總分攤 ${money(grand)} 元。點單位看它被攤的項目。</span>
        <button type="button" class="secondary btn-sm" data-alloc-close>關閉</button>
      </div>
      <div class="grid-scroll"><table class="grid-table">
        <thead><tr><th>單位代碼</th><th>單位名稱</th><th>項目數</th><th>分攤合計</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
      ${detailHtml}`;
    box.scrollIntoView({ block: "nearest" });
  } catch (error) {
    box.innerHTML = `<p class="muted">單位彙總載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

document.querySelector("#budget-units-btn")?.addEventListener("click", () => loadBudgetUnitRollup());

// 費用分攤（資料管理磚）：列出預算供選一筆看/設分攤
async function loadFeeAllocPicker() {
  const box = document.querySelector("#fee-alloc-list");
  if (!box) return;
  box.innerHTML = `<p class="muted">載入預算清單…</p>`;
  try {
    const budgets = (await api("/api/budgets")).data || [];
    resourceCaches.budget = budgets;  // 供 loadBudgetAllocations 讀方法/類別
    const methodLabel = { fixed: "固定金額", headcount: "按人數", category: "按類別" };
    const rows = budgets.length
      ? budgets.map((b) => `<tr>
          <td><button type="button" class="btn-sm" data-budget-alloc="${b.id}">看分攤 ▸</button></td>
          <td><strong>${escapeHtml(b.budget_code)}</strong></td>
          <td class="num">${money(b.amount)} 元</td>
          <td>${escapeHtml(methodLabel[b.alloc_method || "fixed"] || b.alloc_method)}${b.alloc_category ? "／" + escapeHtml(b.alloc_category) : ""}</td></tr>`).join("")
      : `<tr><td colspan="4" class="muted">尚無預算。請先到「預算」新增或匯入。</td></tr>`;
    box.innerHTML = `<div class="grid-scroll"><table class="grid-table">
      <thead><tr><th>分攤</th><th>預算編號</th><th>金額</th><th>目前方法</th></tr></thead>
      <tbody>${rows}</tbody></table></div>`;
  } catch (error) {
    box.innerHTML = `<p class="muted">預算清單載入失敗：${escapeHtml(error.message)}</p>`;
  }
}
document.querySelector("#fee-alloc-list")?.addEventListener("click", (event) => {
  const b = event.target.closest("[data-budget-alloc]");
  if (b) loadBudgetAllocations(b.getAttribute("data-budget-alloc"), "#budget-alloc");  // 明確容器，避免殘留到預算面板
});
document.addEventListener("click", async (event) => {
  if (event.target.closest("[data-alloc-close]")) {
    const box = event.target.closest(".budget-annual-panel, #budget-alloc") || document.querySelector(allocBoxSel);
    if (box) box.innerHTML = "";
    return;
  }
  const rec = event.target.closest("[data-recompute]");
  if (rec) {
    const budgetId = rec.getAttribute("data-recompute");
    rec.disabled = true; rec.textContent = "重算中…";
    try {
      await api(`/api/budgets/${budgetId}/recompute`, { method: "POST" });
      await loadBudgetAllocations(budgetId);
    } catch (error) {
      window.alert(`重算失敗：${error.message}`);
      rec.disabled = false; rec.textContent = "重算分攤";
    }
    return;
  }
  const u = event.target.closest("[data-unit-code]");
  if (u) loadBudgetUnitRollup(u.getAttribute("data-unit-code"));
});

// 通用「?」說明圖示：說明收進 tooltip，不佔版面。hover 顯示；點擊 toggle（觸控友善）。
function helpIcon(tip, extraClass = "") {
  return `<span class="help ${extraClass}" data-tip="${escapeHtml(tip)}" role="button" tabindex="0" aria-label="說明">?</span>`;
}
document.addEventListener("click", (event) => {
  const h = event.target.closest(".help");
  document.querySelectorAll(".help.open").forEach((el) => { if (el !== h) el.classList.remove("open"); });
  if (h) { event.preventDefault(); h.classList.toggle("open"); }
});

// 單位管理：撞名偵測（Step1）＋ 合併/分開裁決（Step2）
let unitConflictCache = { code: [], name: [] };  // 供裁決按鈕依 kind+index 取回變體

function unitVariantRows(variants, keyKind) {
  // keyKind: "byCode" → 顯示各名稱；"byName" → 顯示各代號。末欄「改派」處理某筆代號打錯、其實屬別的單位
  return variants.map((v, vi) => `<tr>
    <td>${escapeHtml(valueOrDash(keyKind === "byCode" ? v.unit_name : v.unit_code))}</td>
    <td>${escapeHtml((v.sources || []).join("、") || "-")}</td>
    <td class="num">${Number(v.count || 0)}</td>
    <td class="col-actions"><button type="button" class="link-btn" data-reassign="${vi}">改派…</button></td></tr>`).join("");
}

// 一組撞名的裁決區：以誰為準下拉 + 理由（必填）+ 合併/分開；曾裁決過會亮警告
function conflictActions(kind, index, variants) {
  const opts = variants.map((v, i) =>
    `<option value="${i}">${escapeHtml(v.unit_name || "(無名稱)")}${v.unit_code ? "（" + escapeHtml(v.unit_code) + "）" : ""}</option>`).join("");
  const dup = variants.some((v) => v.master) ? `<span class="dup-warn">⚠ 已裁決過</span>` : "";
  return `<div class="conflict-actions" data-conflict-kind="${kind}" data-conflict-index="${index}">
    <label class="conflict-canon">以誰為準
      <select class="conflict-canonical">${opts}</select>
    </label>
    <input type="text" class="conflict-reason" maxlength="120" placeholder="理由（必填）" />
    <button type="button" class="btn-sm" data-merge>合併</button>
    <button type="button" class="secondary btn-sm" data-split>分開</button>
    ${dup}
  </div>`;
}

// 去掉常見通用字尾，比對「有辨識度的核心」（避免『分公司』這種尾巴造成誤判）
function unitNameCore(s) {
  return String(s || "").replace(/(股份有限公司|有限公司|分公司|公司|部門|事業處|處|部|科|室|中心|組|課)$/g, "").trim();
}
function longestCommonSubstr(a, b) {
  let best = 0;
  const dp = Array(b.length + 1).fill(0);
  for (let i = 0; i < a.length; i++) {
    let prev = 0;
    for (let j = 0; j < b.length; j++) {
      const tmp = dp[j + 1];
      dp[j + 1] = a[i] === b[j] ? prev + 1 : 0;
      if (dp[j + 1] > best) best = dp[j + 1];
      prev = tmp;
    }
  }
  return best;
}
function namesLookSame(a, b) {
  a = unitNameCore(a); b = unitNameCore(b);
  if (!a || !b) return false;
  if (a === b || a.includes(b) || b.includes(a)) return true;
  // 中文縮寫常保留「頭字＋尾字」（法二處→法二 vs 法人業務二處→法人業務二，頭法尾二）；
  // 頭尾都相同視為相近，能區分 法二/法人業務二（同）與 永和/信義（頭尾皆不同）。
  if (a.length >= 2 && b.length >= 2 && a[0] === b[0] && a[a.length - 1] === b[b.length - 1]) return true;
  const lcs = longestCommonSubstr(a, b);
  return lcs >= 2 && lcs >= Math.min(a.length, b.length) * 0.5;
}
// 「傾向合併/傾向分開」的參考提示——只留一句短結論，理由收進 ?
function mergeHint(c, kind) {
  if (kind === "name") {
    return { lean: "merge", label: "建議：合併",
      why: "名稱一模一樣、只有代號不同，多半是同一單位代號有出入，通常選「合併」。（僅供參考，最後你決定）" };
  }
  const names = c.variants.map((v) => v.unit_name).filter(Boolean);
  let allSame = names.length > 1;
  for (let i = 1; i < names.length; i++) if (!namesLookSame(names[0], names[i])) allSame = false;
  return allSame
    ? { lean: "merge", label: "建議：合併",
        why: "名稱高度相近（像簡寫 vs 全名），比較可能是同一單位，傾向「合併」。（僅供參考，最後你決定）" }
    : { lean: "split", label: "建議：分開",
        why: "名稱差異較大，可能是不同單位、或某筆代號打錯，請確認，多半選「分開」。（僅供參考，最後你決定）" };
}

function conflictCardHtml(c, kind) {
  const key = kind === "code"
    ? `代號 <strong>${escapeHtml(c.unit_code)}</strong> ＝ ${c.variants.length} 個名稱`
    : `名稱 <strong>${escapeHtml(c.unit_name)}</strong> ＝ ${c.variants.length} 個代號`;
  const head = kind === "code" ? "名稱" : "代號";
  const rows = unitVariantRows(c.variants, kind === "code" ? "byCode" : "byName");
  const idx = kind === "code" ? unitConflictCache.code.indexOf(c) : unitConflictCache.name.indexOf(c);
  const hint = mergeHint(c, kind);
  return `<div class="unit-conflict-card" data-ckind="${kind}" data-cindex="${idx}">
    <div class="unit-conflict-key">${key}</div>
    <div class="grid-scroll"><table class="grid-table">
      <thead><tr><th>${head}</th><th>來源檔</th><th>筆數</th><th class="col-actions"></th></tr></thead>
      <tbody>${rows}</tbody>
    </table></div>
    <div class="reassign-box" hidden></div>
    <div class="conflict-hint ${hint.lean === "split" ? "lean-split" : ""}">💡 <strong>${hint.label}</strong>${helpIcon(hint.why)}</div>
    ${conflictActions(kind, idx, c.variants)}</div>`;
}

async function loadUnitConflicts() {
  const box = document.querySelector("#unitconf-result");
  const sum = document.querySelector("#unitconf-summary");
  if (!box) return;
  box.innerHTML = `<p class="muted">掃描中…</p>`;
  try {
    const data = (await api("/api/unit-conflicts")).data || {};
    const codeC = data.code_conflicts || [];
    const nameC = data.name_conflicts || [];
    unitConflictCache = { code: codeC, name: nameC };
    const total = codeC.length + nameC.length;
    const resolved = (data.summary || {}).resolved_groups || 0;
    setText("#tile-count-unitconf", total ? `撞名待確認 ${total}` : "撞名待確認 0");
    if (sum) {
      sum.innerHTML = total
        ? `<p class="warn-line">⚠ 還有 <strong>${total}</strong> 組要你裁決：同代號多名 ${codeC.length} 組、同名多代號 ${nameC.length} 組。系統<strong>不會自動合併</strong>，由你決定。${resolved ? `（已處理 ${resolved} 組）` : ""}</p>`
        : `<p class="ok-line">✓ 沒有待裁決的撞名了${resolved ? `，已處理 ${resolved} 組` : ""}。</p>`;
    }

    const codeBlock = codeC.length ? `
      <h4>同一代號、對到多個名稱（最可能是不同檔案代號撞在一起）</h4>
      ${codeC.map((c) => conflictCardHtml(c, "code")).join("")}` : "";
    const nameBlock = nameC.length ? `
      <h4>同一名稱、對到多個代號（可能是代號改過或缺代號）</h4>
      ${nameC.map((c) => conflictCardHtml(c, "name")).join("")}` : "";

    box.innerHTML = (codeBlock + nameBlock) || `<p class="muted">沒有待裁決的撞名。匯入更多資料後可再按「重新掃描」。</p>`;
    loadUnitMaster();
    loadUnitDecisions();
  } catch (error) {
    box.innerHTML = `<p class="muted">掃描失敗：${escapeHtml(error.message)}</p>`;
    if (sum) sum.innerHTML = "";
  }
}

const UNIT_ACTION_LABEL = { merge: "合併", split: "分開", reassign: "改派" };
async function loadUnitDecisions() {
  const box = document.querySelector("#unitdecisions-result");
  if (!box) return;
  try {
    const data = (await api("/api/unit-decisions")).data || {};
    const list = data.decisions || [];
    if (!list.length) { box.innerHTML = `<p class="muted">還沒有裁決紀錄。</p>`; return; }
    box.innerHTML = `<div class="grid-scroll"><table class="grid-table">
      <thead><tr><th>時間</th><th>動作</th><th>內容</th><th>理由</th><th>操作者</th><th class="col-actions">復原</th></tr></thead>
      <tbody>${list.map((d) => {
        const names = (d.variants || []).map((v) => v.unit_name || v.unit_code).join("、");
        const content = (d.action === "merge" || d.action === "reassign")
          ? `${escapeHtml(names)} → 以「${escapeHtml(d.canonical_name || d.canonical_code)}」為準`
          : `${escapeHtml(names)}（分開）`;
        return `<tr class="${d.undone ? "decision-undone" : ""}">
          <td class="muted">${escapeHtml((d.created_at || "").replace("T", " ").slice(0, 16))}</td>
          <td><span class="badge">${escapeHtml(UNIT_ACTION_LABEL[d.action] || d.action)}</span></td>
          <td>${content}</td>
          <td>${escapeHtml(d.reason || "-")}</td>
          <td class="muted">${escapeHtml(d.actor || "-")}</td>
          <td class="col-actions">${d.undone ? `<span class="muted">已復原</span>` : `<button type="button" class="secondary btn-sm" data-undo="${d.id}">復原</button>`}</td>
        </tr>`;
      }).join("")}</tbody></table></div>`;
  } catch (error) {
    box.innerHTML = `<p class="muted">決策紀錄載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

let unitMasterCache = [];  // 供「改派」下拉列出現有單位
// 單位下拉：預算表單(含精靈)的「單位名稱」只能選單位主檔已登記的乾淨名稱，避免手打錯字/寫法不一。
// 保留 select 目前選到、但主檔沒有的值（見 startResourceEdit），這裡只負責從主檔灌選項。
function populateUnitSelects() {
  const rest = (unitMasterCache || []).map((m) => `<option value="${escapeHtml(m.canonical_name)}">${escapeHtml(m.canonical_name)}</option>`).join("");
  for (const sel of document.querySelectorAll("select.unit-select")) {
    // 第一個選項文字各表單各自標記（用 data-placeholder），不要整批蓋成同一句「（未選擇）」
    const placeholder = sel.dataset.placeholder ? `（未選擇）${sel.dataset.placeholder}` : "（未選擇）";
    const prev = sel.value;
    sel.innerHTML = `<option value="">${escapeHtml(placeholder)}</option>` + rest;
    if (prev && [...sel.options].some((o) => o.value === prev)) sel.value = prev;
  }
}

async function loadUnitMaster() {
  const box = document.querySelector("#unitmaster-result");
  if (!box) return;
  try {
    const data = (await api("/api/unit-master")).data || {};
    const masters = data.masters || [];
    unitMasterCache = masters;
    populateUnitSelects();
    if (!masters.length) { box.innerHTML = `<p class="muted">還沒有裁決過的單位。上面裁決後會出現在這裡，或用下面「＋新增單位」直接登記。</p>`; return; }
    box.innerHTML = `<div class="grid-scroll"><table class="grid-table">
      <thead><tr><th>主單位（以此為準）</th><th>代號</th><th>別名（代號／名稱）</th></tr></thead>
      <tbody>${masters.map((m) => `<tr>
        <td><strong>${escapeHtml(m.canonical_name || "-")}</strong></td>
        <td>${escapeHtml(valueOrDash(m.canonical_code))}</td>
        <td>${(m.aliases || []).map((a) => `<span class="alias-chip">${escapeHtml(a.alias_name || "(無名)")}${a.alias_code ? "／" + escapeHtml(a.alias_code) : ""}
          <button type="button" class="alias-unlink" data-unlink="${a.id}" title="解除這筆裁決">✕</button></span>`).join(" ")}</td>
      </tr>`).join("")}</tbody></table></div>`;
  } catch (error) {
    box.innerHTML = `<p class="muted">單位主檔載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

// 人員下拉：案件/簽呈/預算/付款/專案表單的「負責人/申請人/核銷者…」只能選人員主檔已登記的名字。
let personnelMasterCache = [];
function populatePersonnelSelects() {
  const rest = (personnelMasterCache || []).map((p) => `<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}</option>`).join("");
  for (const sel of document.querySelectorAll("select.personnel-select")) {
    // 第一個選項文字各表單各自標記（用 data-placeholder），不要整批蓋成同一句「（未選擇）」
    const placeholder = sel.dataset.placeholder ? `（未選擇）${sel.dataset.placeholder}` : "（未選擇）";
    const prev = sel.value;
    sel.innerHTML = `<option value="">${escapeHtml(placeholder)}</option>` + rest;
    if (prev && [...sel.options].some((o) => o.value === prev)) sel.value = prev;
  }
}

// 年度下拉：作業年度前後幾年的合理範圍，不用另外維護清單（年度是封閉、可預期的小集合）。
function populateFiscalYearSelects() {
  const now = new Date();
  const base = now.getFullYear();
  const years = [];
  for (let y = base - 1; y <= base + 3; y++) years.push(y);
  for (const sel of document.querySelectorAll("select.fiscal-year-select")) {
    const placeholder = sel.dataset.placeholder || "";
    const prev = sel.value;
    sel.innerHTML = [`<option value="">${escapeHtml(placeholder)}</option>`]
      .concat(years.map((y) => `<option value="${y}">${y} 年度</option>`))
      .join("");
    if (prev && [...sel.options].some((o) => o.value === prev)) sel.value = prev;
  }
}

async function loadPersonnelMaster() {
  const box = document.querySelector("#personnelmaster-result");
  try {
    const data = (await api("/api/personnel-master")).data || {};
    const masters = data.masters || [];
    personnelMasterCache = masters;
    populatePersonnelSelects();
    if (!box) return;
    box.innerHTML = masters.length
      ? `<div class="grid-scroll"><table class="grid-table">
          <thead><tr><th>姓名</th><th>備註</th></tr></thead>
          <tbody>${masters.map((p) => `<tr><td><strong>${escapeHtml(p.name)}</strong></td><td class="muted">${escapeHtml(valueOrDash(p.note))}</td></tr>`).join("")}</tbody>
        </table></div>`
      : `<p class="muted">還沒有登記過人員，用上面「＋新增人員」登記。</p>`;
  } catch (error) {
    if (box) box.innerHTML = `<p class="muted">人員名單載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

// 影響預覽：這些變體現在佔幾筆分攤、金額多少
async function unitImpactLine(variants) {
  try {
    const imp = (await api("/api/unit-impact", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ variants }) })).data || {};
    return `影響：${imp.rows} 筆分攤、合計 ${money(imp.amount)} 元會受這次裁決影響。`;
  } catch (_e) { return ""; }
}

// 逐筆改派：某筆代號打錯、其實屬別的單位 → 掛到指定/正確單位
function groupFromCard(card) {
  const kind = card.getAttribute("data-ckind");
  const index = Number(card.getAttribute("data-cindex"));
  return (unitConflictCache[kind] || [])[index];
}
function renderReassignBox(card, vi) {
  const group = groupFromCard(card);
  const v = group?.variants?.[vi];
  const box = card.querySelector(".reassign-box");
  if (!v || !box) return;
  const masterOpts = unitMasterCache
    .map((m) => `<option value="m:${m.id}">${escapeHtml(m.canonical_name || "")}（${escapeHtml(m.canonical_code || "無碼")}）</option>`).join("");
  box.innerHTML = `
    <div class="reassign-title">把「<strong>${escapeHtml(v.unit_name || "")}${v.unit_code ? "（" + escapeHtml(v.unit_code) + "）" : ""}</strong>」改派到：</div>
    <div class="reassign-row">
      <select class="reassign-target">
        ${masterOpts}
        <option value="custom">＋ 自訂正確代號／名稱…</option>
      </select>
      <input type="text" class="reassign-code" placeholder="正確代號" hidden />
      <input type="text" class="reassign-name" placeholder="正確名稱" hidden />
      <input type="text" class="reassign-reason" placeholder="理由（必填）" />
      <button type="button" class="btn-sm" data-reassign-go="${vi}">確定改派</button>
      <button type="button" class="secondary btn-sm" data-reassign-cancel>取消</button>
    </div>`;
  box.hidden = false;
  // 沒有任何現有單位時，直接進自訂模式
  const sel = box.querySelector(".reassign-target");
  if (!unitMasterCache.length) { sel.value = "custom"; }
  const toggleCustom = () => {
    const custom = sel.value === "custom";
    box.querySelector(".reassign-code").hidden = !custom;
    box.querySelector(".reassign-name").hidden = !custom;
  };
  sel.addEventListener("change", toggleCustom);
  toggleCustom();
  box.scrollIntoView({ block: "nearest" });
}

// 裁決：合併 / 分開 / 改派（含理由必填、影響預覽、重複裁決提醒）
document.querySelector("#unitconf-result")?.addEventListener("click", async (event) => {
  // 改派：開啟 / 取消 / 送出
  const openBtn = event.target.closest("[data-reassign]");
  if (openBtn) { renderReassignBox(openBtn.closest(".unit-conflict-card"), Number(openBtn.getAttribute("data-reassign"))); return; }
  if (event.target.closest("[data-reassign-cancel]")) {
    const box = event.target.closest(".reassign-box"); if (box) { box.hidden = true; box.innerHTML = ""; } return;
  }
  const goBtn = event.target.closest("[data-reassign-go]");
  if (goBtn) {
    const card = goBtn.closest(".unit-conflict-card");
    const box = goBtn.closest(".reassign-box");
    const group = groupFromCard(card);
    const v = group?.variants?.[Number(goBtn.getAttribute("data-reassign-go"))];
    if (!v) return;
    const sel = box.querySelector(".reassign-target");
    const reason = (box.querySelector(".reassign-reason")?.value || "").trim();
    if (!reason) { window.alert("請先填『理由』：為什麼這筆該改派？"); box.querySelector(".reassign-reason")?.focus(); return; }
    let code = "", name = "";
    if (sel.value === "custom") {
      code = (box.querySelector(".reassign-code")?.value || "").trim();
      name = (box.querySelector(".reassign-name")?.value || "").trim();
      if (!code && !name) { window.alert("請填正確的代號或名稱。"); return; }
    } else {
      const m = unitMasterCache.find((x) => `m:${x.id}` === sel.value);
      if (!m) { window.alert("請選擇要改派到哪個單位。"); return; }
      code = m.canonical_code || ""; name = m.canonical_name || "";
    }
    if (!window.confirm(`把「${v.unit_name}（${v.unit_code || "無碼"}）」改派到「${name}（${code || "無碼"}）」？\n（這筆的分攤金額會改算到目標單位，可復原）`)) return;
    try {
      await api("/api/unit-reassign", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ variant: { unit_code: v.unit_code, unit_name: v.unit_name }, canonical_code: code, canonical_name: name, reason }) });
      await loadUnitConflicts();
      if (document.querySelector("#budget-alloc")?.innerHTML) loadBudgetUnitRollup();
    } catch (error) { window.alert(`改派失敗：${error.message}`); }
    return;
  }

  const wrap = event.target.closest(".conflict-actions");
  if (!wrap) return;
  const isMerge = !!event.target.closest("[data-merge]");
  const isSplit = !!event.target.closest("[data-split]");
  if (!isMerge && !isSplit) return;
  const kind = wrap.getAttribute("data-conflict-kind");
  const index = Number(wrap.getAttribute("data-conflict-index"));
  const group = (unitConflictCache[kind] || [])[index];
  if (!group) return;
  const variants = group.variants.map((v) => ({ unit_code: v.unit_code, unit_name: v.unit_name }));
  const reason = (wrap.querySelector(".conflict-reason")?.value || "").trim();
  if (!reason) { window.alert("請先填『理由』：為什麼這樣判斷？（留個依據，之後查得到）"); wrap.querySelector(".conflict-reason")?.focus(); return; }
  const dupNote = group.variants.some((v) => v.master) ? "\n\n⚠ 這組先前已裁決過，這次會覆蓋。" : "";
  const impact = await unitImpactLine(variants);
  try {
    if (isMerge) {
      const sel = wrap.querySelector(".conflict-canonical");
      const canon = group.variants[Number(sel.value)] || group.variants[0];
      if (!window.confirm(`把這 ${variants.length} 筆視為同一單位，以「${canon.unit_name}（${canon.unit_code || "無碼"}）」為準？\n${impact}\n（帳不會不見，只是認到同一單位，可復原）${dupNote}`)) return;
      await api("/api/unit-merge", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ variants, canonical_code: canon.unit_code || "", canonical_name: canon.unit_name || "", reason }) });
    } else {
      if (!window.confirm(`把這 ${variants.length} 筆當成不同單位、分開保留？\n${impact}${dupNote}`)) return;
      await api("/api/unit-split", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ variants, reason }) });
    }
    await loadUnitConflicts();
    if (document.querySelector("#budget-alloc")?.innerHTML) loadBudgetUnitRollup();
  } catch (error) {
    window.alert(`裁決失敗：${error.message}`);
  }
});

document.querySelector("#unitmaster-result")?.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-unlink]");
  if (!btn) return;
  if (!window.confirm("解除這筆裁決？（該別名會脫離主單位，可能重新變成待確認）")) return;
  try {
    await api(`/api/unit-alias/${btn.getAttribute("data-unlink")}/unlink`, { method: "POST" });
    await loadUnitConflicts();
  } catch (error) {
    window.alert(`解除失敗：${error.message}`);
  }
});

// 決策紀錄：逐筆復原
document.querySelector("#unitdecisions-result")?.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-undo]");
  if (!btn) return;
  if (!window.confirm("復原這筆裁決？系統會把相關單位還原到裁決前的狀態。")) return;
  try {
    await api(`/api/unit-decisions/${btn.getAttribute("data-undo")}/undo`, { method: "POST" });
    await loadUnitConflicts();
    if (document.querySelector("#budget-alloc")?.innerHTML) loadBudgetUnitRollup();
  } catch (error) {
    window.alert(`復原失敗：${error.message}`);
  }
});

// 一鍵還原到原始匯入（終極後悔藥）
document.querySelector("#unit-reset")?.addEventListener("click", async () => {
  if (!window.confirm("一鍵還原：清掉所有合併/分開裁決，回到剛匯入的原始狀態。\n（原始 Excel 資料本就沒被改過，這只是把裁決層清空。確定？）")) return;
  try {
    const r = (await api("/api/unit-reset", { method: "POST" })).data || {};
    window.alert(`已還原：清掉 ${r.removed_masters} 個主單位、${r.removed_aliases} 筆別名。`);
    await loadUnitConflicts();
    if (document.querySelector("#budget-alloc")?.innerHTML) loadBudgetUnitRollup();
  } catch (error) {
    window.alert(`還原失敗：${error.message}`);
  }
});

document.querySelector("#unitconf-rescan")?.addEventListener("click", () => loadUnitConflicts());

document.querySelector("#unit-create-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const statusEl = document.querySelector("#unit-create-status");
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    await api("/api/unit-master", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    if (statusEl) statusEl.textContent = `已新增「${data.canonical_name}」`;
    form.reset();
    await loadUnitMaster();
  } catch (error) {
    if (statusEl) statusEl.textContent = `失敗：${error.message}`;
  }
});

document.querySelector("#personnel-create-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const statusEl = document.querySelector("#personnel-create-status");
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    await api("/api/personnel-master", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    if (statusEl) statusEl.textContent = `已新增「${data.name}」`;
    form.reset();
    await loadPersonnelMaster();
  } catch (error) {
    if (statusEl) statusEl.textContent = `失敗：${error.message}`;
  }
});

// ===== 名稱歸納（案件名/專案名/廠商名）：相近名稱分群→裁決合併/分開 =====
let nameKind = "vendor";
let nameClusterCache = [];  // 供裁決按鈕依 index 取回該群名稱
const NAME_KIND_LABEL = { vendor: "廠商名", case: "案件名", project: "專案名" };

// 名稱分群用「包含關係」判斷（比 namesLookSame 嚴，避免中華電信/中華資安因共用「中華」被誤併）：
// 一個是另一個的子字串就算同一實體（中華電⊂中華電信⊂中華電信股份有限公司；奧義⊂奧義智慧）。
function isSubsequence(short, long) {  // short 的字元是否依序出現在 long 裡
  let i = 0;
  for (const ch of long) { if (ch === short[i]) i++; if (i >= short.length) return true; }
  return i >= short.length;
}
function namesClusterSame(a, b) {
  a = String(a || "").trim(); b = String(b || "").trim();
  if (!a || !b) return false;
  if (a === b || a.includes(b) || b.includes(a)) return true;
  const ca = unitNameCore(a), cb = unitNameCore(b);  // 去通用字尾(公司/部/處…)後再看包含
  if (ca && cb && ca !== cb && (ca.includes(cb) || cb.includes(ca))) return true;
  // 插入字元型（少林科技 ⊂ 少林寺科技）：短的是長的子序列、且共用前兩字、長度足夠
  const [s, l] = a.length <= b.length ? [a, b] : [b, a];
  return s.length >= 3 && s.slice(0, 2) === l.slice(0, 2) && isSubsequence(s, l);
}

// 用 union-find 把相近名稱分群
function clusterNames(values) {
  const parent = values.map((_, i) => i);
  const find = (i) => { while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i]; } return i; };
  for (let i = 0; i < values.length; i++)
    for (let j = i + 1; j < values.length; j++)
      if (namesClusterSame(values[i].name, values[j].name)) parent[find(i)] = find(j);
  const groups = {};
  values.forEach((v, i) => { const r = find(i); (groups[r] = groups[r] || []).push(v); });
  // 只留「≥2 個名、且尚未全部歸到同一主名」的群
  return Object.values(groups).filter((g) => {
    if (g.length < 2) return false;
    const canons = new Set(g.map((v) => v.canonical || "＿" + v.name));
    return canons.size > 1;
  });
}

async function loadNameCleaning() {
  const box = document.querySelector("#name-result");
  const sum = document.querySelector("#name-summary");
  if (!box) return;
  box.innerHTML = `<p class="muted">掃描中…</p>`;
  try {
    const data = (await api(`/api/name-values?kind=${nameKind}`)).data || {};
    const values = data.values || [];
    const clusters = clusterNames(values);
    nameClusterCache = clusters;
    if (sum) {
      sum.innerHTML = clusters.length
        ? `<p class="warn-line">⚠ ${NAME_KIND_LABEL[nameKind]}：找到 <strong>${clusters.length}</strong> 組相近名稱要你裁決。系統只挑相近的、不自動合併。</p>`
        : `<p class="ok-line">✓ ${NAME_KIND_LABEL[nameKind]}：沒有待裁決的相近名稱。</p>`;
    }
    box.innerHTML = clusters.length
      ? clusters.map((g, idx) => nameClusterCardHtml(g, idx)).join("")
      : `<p class="muted">沒有相近名稱。有新資料進來可再按分頁重掃。</p>`;
    loadNameMaster();
    loadNameDecisions();
  } catch (error) {
    box.innerHTML = `<p class="muted">掃描失敗：${escapeHtml(error.message)}</p>`;
    if (sum) sum.innerHTML = "";
  }
}

function nameClusterCardHtml(group, idx) {
  const longest = [...group].sort((a, b) => (b.name || "").length - (a.name || "").length || b.count - a.count)[0];
  const opts = group.map((v) => `<option value="${escapeHtml(v.name)}"${v.name === longest.name ? " selected" : ""}>${escapeHtml(v.name)}（${v.count} 筆）</option>`).join("");
  const rows = group.map((v) => `<tr><td>${escapeHtml(v.name)}</td><td class="num">${Number(v.count || 0)}</td><td>${v.canonical ? "→ " + escapeHtml(v.canonical) : "<span class='muted'>未歸納</span>"}</td></tr>`).join("");
  return `<div class="unit-conflict-card" data-name-index="${idx}">
    <div class="unit-conflict-key">${group.length} 個相近名稱</div>
    <div class="grid-scroll"><table class="grid-table">
      <thead><tr><th>名稱</th><th>筆數</th><th>目前歸納</th></tr></thead>
      <tbody>${rows}</tbody></table></div>
    <div class="conflict-hint">💡 <strong>建議：合併</strong>${helpIcon("名稱相近，多半是同一實體的不同寫法，傾向合併。（僅供參考，你決定）")}</div>
    <div class="conflict-actions" data-name-actions="${idx}">
      <label class="conflict-canon">以誰為準<select class="name-canonical">${opts}</select></label>
      <input type="text" class="name-reason" maxlength="120" placeholder="理由（必填）" />
      <button type="button" class="btn-sm" data-name-merge>合併</button>
      <button type="button" class="secondary btn-sm" data-name-split>分開</button>
    </div></div>`;
}

async function loadNameMaster() {
  const box = document.querySelector("#namemaster-result");
  if (!box) return;
  try {
    const list = (await api(`/api/name-values?kind=${nameKind}`)).data.values || [];
    const byCanon = {};
    list.filter((v) => v.canonical).forEach((v) => { (byCanon[v.canonical] = byCanon[v.canonical] || []).push(v); });
    const canons = Object.keys(byCanon);
    if (!canons.length) { box.innerHTML = `<p class="muted">還沒有歸納過的名稱。</p>`; return; }
    box.innerHTML = `<div class="grid-scroll"><table class="grid-table">
      <thead><tr><th>主名（以此為準）</th><th>別名</th></tr></thead>
      <tbody>${canons.map((c) => `<tr><td><strong>${escapeHtml(c)}</strong></td>
        <td>${byCanon[c].filter((v) => v.name !== c).map((v) => `<span class="alias-chip">${escapeHtml(v.name)}</span>`).join(" ") || "<span class='muted'>—</span>"}</td></tr>`).join("")}</tbody></table></div>`;
  } catch (error) {
    box.innerHTML = `<p class="muted">載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

async function loadNameDecisions() {
  const box = document.querySelector("#namedecisions-result");
  if (!box) return;
  try {
    const list = (await api(`/api/name-decisions?kind=${nameKind}`)).data.decisions || [];
    if (!list.length) { box.innerHTML = `<p class="muted">還沒有裁決紀錄。</p>`; return; }
    box.innerHTML = `<div class="grid-scroll"><table class="grid-table">
      <thead><tr><th>時間</th><th>動作</th><th>內容</th><th>理由</th><th>操作者</th><th class="col-actions">復原</th></tr></thead>
      <tbody>${list.map((d) => {
        const content = d.action === "merge" ? `${escapeHtml((d.names || []).join("、"))} → 「${escapeHtml(d.canonical_name)}」` : `${escapeHtml((d.names || []).join("、"))}（分開）`;
        return `<tr class="${d.undone ? "decision-undone" : ""}">
          <td class="muted">${escapeHtml((d.created_at || "").replace("T", " ").slice(0, 16))}</td>
          <td><span class="badge">${d.action === "merge" ? "合併" : "分開"}</span></td>
          <td>${content}</td><td>${escapeHtml(d.reason || "-")}</td><td class="muted">${escapeHtml(d.actor || "-")}</td>
          <td class="col-actions">${d.undone ? `<span class="muted">已復原</span>` : `<button type="button" class="secondary btn-sm" data-name-undo="${d.id}">復原</button>`}</td></tr>`;
      }).join("")}</tbody></table></div>`;
  } catch (error) {
    box.innerHTML = `<p class="muted">載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

document.querySelector("#name-kind-tabs")?.addEventListener("click", (event) => {
  const t = event.target.closest("[data-name-kind]");
  if (!t) return;
  nameKind = t.getAttribute("data-name-kind");
  document.querySelectorAll("#name-kind-tabs .tab").forEach((x) => x.classList.toggle("active", x === t));
  loadNameCleaning();
});
document.querySelector("#name-result")?.addEventListener("click", async (event) => {
  const wrap = event.target.closest("[data-name-actions]");
  if (!wrap) return;
  const isMerge = !!event.target.closest("[data-name-merge]");
  const isSplit = !!event.target.closest("[data-name-split]");
  if (!isMerge && !isSplit) return;
  const group = nameClusterCache[Number(wrap.getAttribute("data-name-actions"))];
  if (!group) return;
  const names = group.map((v) => v.name);
  const reason = (wrap.querySelector(".name-reason")?.value || "").trim();
  if (!reason) { window.alert("請先填『理由』：為什麼這樣判斷？"); wrap.querySelector(".name-reason")?.focus(); return; }
  try {
    if (isMerge) {
      const canon = wrap.querySelector(".name-canonical").value;
      if (!window.confirm(`把「${names.join("、")}」視為同一個，以「${canon}」為準？\n（原始資料不動、可復原）`)) return;
      await api("/api/name-merge", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind: nameKind, names, canonical_name: canon, reason }) });
    } else {
      if (!window.confirm(`把「${names.join("、")}」當成不同的、分開保留？`)) return;
      await api("/api/name-split", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind: nameKind, names, reason }) });
    }
    await loadNameCleaning();
  } catch (error) { window.alert(`裁決失敗：${error.message}`); }
});
document.querySelector("#namedecisions-result")?.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-name-undo]");
  if (!btn) return;
  if (!window.confirm("復原這筆裁決？")) return;
  try { await api(`/api/name-decisions/${btn.getAttribute("data-name-undo")}/undo`, { method: "POST" }); await loadNameCleaning(); }
  catch (error) { window.alert(`復原失敗：${error.message}`); }
});
document.querySelector("#name-reset")?.addEventListener("click", async () => {
  if (!window.confirm(`一鍵還原「${NAME_KIND_LABEL[nameKind]}」的所有歸納，回到原始？（原始資料本就沒動過）`)) return;
  try {
    const r = (await api(`/api/name-reset?kind=${nameKind}`, { method: "POST" })).data || {};
    window.alert(`已還原：清掉 ${r.removed_masters} 個主名、${r.removed_aliases} 筆別名。`);
    await loadNameCleaning();
  } catch (error) { window.alert(`還原失敗：${error.message}`); }
});

// 一鍵套用建議：依每組💡建議一次處理完，理由自動帶，事後可在決策紀錄複核/復原
// 合併時挑「以誰為準」：同代號多名→取最長名稱(通常是全名)；同名多代號→取筆數最多的代號
function suggestedCanonical(group, kind) {
  const vs = group.variants;
  if (kind === "code") {
    const best = [...vs].sort((a, b) => (b.unit_name || "").length - (a.unit_name || "").length || (b.count || 0) - (a.count || 0))[0];
    return { code: group.unit_code, name: best.unit_name };
  }
  const best = [...vs].sort((a, b) => (b.count || 0) - (a.count || 0))[0];
  return { code: best.unit_code, name: group.unit_name };
}
document.querySelector("#unit-apply-suggest")?.addEventListener("click", async (event) => {
  const groups = [
    ...unitConflictCache.code.map((g) => ({ g, kind: "code" })),
    ...unitConflictCache.name.map((g) => ({ g, kind: "name" })),
  ];
  if (!groups.length) { window.alert("目前沒有待處理的撞名。"); return; }
  let mergeN = 0, splitN = 0;
  for (const { g, kind } of groups) (mergeHint(g, kind).lean === "merge" ? mergeN++ : splitN++);
  if (!window.confirm(`將依系統建議一次處理 ${groups.length} 組：合併 ${mergeN} 組、分開 ${splitN} 組。\n全部會記進決策紀錄、可逐筆復原或一鍵還原。確定？`)) return;
  const btn = event.currentTarget;
  btn.disabled = true; const label = btn.textContent; btn.textContent = "套用中…";
  let ok = 0, fail = 0;
  for (const { g, kind } of groups) {
    const variants = g.variants.map((v) => ({ unit_code: v.unit_code, unit_name: v.unit_name }));
    const hint = mergeHint(g, kind);
    try {
      if (hint.lean === "merge") {
        const canon = suggestedCanonical(g, kind);
        await api("/api/unit-merge", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ variants, canonical_code: canon.code || "", canonical_name: canon.name || "", reason: "系統建議：名稱相近，視為同一單位" }) });
      } else {
        await api("/api/unit-split", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ variants, reason: "系統建議：名稱差異大，視為不同單位" }) });
      }
      ok++;
    } catch (_e) { fail++; }
  }
  btn.disabled = false; btn.textContent = label;
  await loadUnitConflicts();
  if (document.querySelector("#budget-alloc")?.innerHTML) loadBudgetUnitRollup();
  window.alert(`套用完成：成功 ${ok} 組${fail ? `、失敗 ${fail} 組` : ""}。\n請往下拉到「決策紀錄」複核，不對的按「復原」即可。`);
});

// 人數基準表：匯入 + 檢視
async function hcXlsx(commit) {
  const file = document.querySelector("#hc-xlsx-file")?.files?.[0];
  const el = document.querySelector("#hc-xlsx-status");
  const commitBtn = document.querySelector("#hc-xlsx-commit");
  if (!file) { if (el) el.textContent = "請先選一個 .xlsx 檔"; return; }
  if (commit && !window.confirm("確定匯入人數表？同代號更新。")) return;
  if (el) el.textContent = commit ? "匯入中…" : "解析中…";
  try {
    const res = (await api(`/api/budget-headcounts/import-xlsx?commit=${commit}&filename=${encodeURIComponent(file.name)}`, { method: "POST", body: file })).data || {};
    if (commit) {
      if (el) el.textContent = `匯入完成：新增 ${res.created_count} 筆、更新 ${res.updated_count} 筆。`;
    } else {
      if (el) el.textContent = res.count ? `預覽：共 ${res.count} 個單位` : "共 0 個——這個檔不像人數表，請確認選了「費用分攤表NEW…(人數).xlsx」。";
      if (commitBtn) commitBtn.disabled = !res.count;
    }
  } catch (error) {
    if (el) el.textContent = `失敗：${error.message}`;
  }
}
async function loadHeadcountsView() {
  const box = document.querySelector("#io-result");
  if (!box) return;
  box.innerHTML = `<p class="muted">載入人數表…</p>`;
  try {
    const hc = (await api("/api/budget-headcounts")).data || [];
    const totalHc = hc.reduce((s, h) => s + Number(h.headcount || 0), 0);
    const rows = hc.length
      ? hc.map((h) => `<tr><td>${escapeHtml(valueOrDash(h.unit_code))}</td><td>${escapeHtml(h.unit_name)}</td><td class="num">${Number(h.headcount || 0)}</td><td class="num">${totalHc ? (Number(h.headcount || 0) / totalHc * 100).toFixed(2) : 0}%</td></tr>`).join("")
      : `<tr><td colspan="4" class="muted">尚無人數資料。請先匯入人數表。</td></tr>`;
    box.innerHTML = `
      <div class="budget-alloc-head"><strong>人數基準表</strong>
        <span class="muted">共 ${hc.length} 個單位，總人數 ${totalHc} 人</span>
        <button type="button" class="secondary btn-sm" data-alloc-close>關閉</button></div>
      <div class="grid-scroll"><table class="grid-table">
        <thead><tr><th>代號</th><th>部門</th><th>人數</th><th>占比</th></tr></thead>
        <tbody>${rows}</tbody></table></div>`;
    box.scrollIntoView({ block: "nearest" });
  } catch (error) {
    box.innerHTML = `<p class="muted">人數表載入失敗：${escapeHtml(error.message)}</p>`;
  }
}
document.querySelector("#hc-xlsx-preview")?.addEventListener("click", () => hcXlsx(false));
document.querySelector("#hc-xlsx-commit")?.addEventListener("click", () => hcXlsx(true));
document.querySelector("#hc-view-btn")?.addEventListener("click", () => loadHeadcountsView());

// 類別基準表（對照表）匯入：供「按類別分攤」用
async function catXlsx(commit) {
  const file = document.querySelector("#cat-xlsx-file")?.files?.[0];
  const el = document.querySelector("#cat-xlsx-status");
  const commitBtn = document.querySelector("#cat-xlsx-commit");
  if (!file) { if (el) el.textContent = "請先選一個 .xlsx 檔"; return; }
  if (commit && !window.confirm("確定匯入類別基準表？同類別同單位會更新。")) return;
  if (el) el.textContent = commit ? "匯入中…" : "解析中…";
  try {
    const res = (await api(`/api/category-shares/import-xlsx?commit=${commit}&filename=${encodeURIComponent(file.name)}`, { method: "POST", body: file })).data || {};
    if (commit) {
      if (el) el.textContent = `匯入完成：共 ${res.written} 筆，類別：${(res.categories || []).join("、")}。`;
    } else {
      if (el) el.textContent = res.count
        ? `預覽：共 ${res.count} 筆，類別：${(res.categories || []).join("、")}`
        : "共 0 筆——這個檔裡找不到「對照」表，請確認選了資訊架構部費用分攤表。";
      if (commitBtn) commitBtn.disabled = !res.count;
    }
  } catch (error) {
    if (el) el.textContent = `失敗：${error.message}`;
  }
}
document.querySelector("#cat-xlsx-preview")?.addEventListener("click", () => catXlsx(false));
document.querySelector("#cat-xlsx-commit")?.addEventListener("click", () => catXlsx(true));
// 匯入/匯出專區：「前往某模組」按鈕 → 切到該模組
document.querySelector("#io-center")?.addEventListener("click", (event) => {
  const g = event.target.closest("[data-goto-module]");
  if (g) navigateToPanel(g.getAttribute("data-goto-module"));
});

// 資料管理後台：磚塊 → 開對應工具；工具頁「← 資料管理」→ 回後台首頁
document.querySelector("#data-admin")?.addEventListener("click", (event) => {
  const tile = event.target.closest("[data-open-panel]");
  if (tile) openBackofficeTool(tile.getAttribute("data-open-panel"));
});
document.addEventListener("click", (event) => {
  if (event.target.closest(".back-to-admin")) {
    document.querySelector('a.module-card[href="#data-admin"]')?.click();
  }
});
// 改「尾數承擔單位」→ 存進該預算、重載分攤（尾數即時改歸新單位）。document 委派＝兩個容器都適用
document.addEventListener("change", async (event) => {
  const sel = event.target.closest("[data-rem-budget]");
  if (sel) {
    const budgetId = sel.getAttribute("data-rem-budget");
    try {
      await api(`/api/budgets/${budgetId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ remainder_unit_code: sel.value }) });
      await loadBudgetAllocations(budgetId);
    } catch (error) { window.alert(`設定尾數承擔單位失敗：${error.message}`); }
    return;
  }
  // 改分攤方法：存進該預算，重載（按類別會再出類別下拉）
  const mSel = event.target.closest("[data-alloc-method]");
  if (mSel) {
    const budgetId = mSel.getAttribute("data-alloc-method");
    try {
      await api(`/api/budgets/${budgetId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ alloc_method: mSel.value }) });
      await loadResource("budget");
      await loadBudgetAllocations(budgetId);
    } catch (error) { window.alert(`設定分攤方法失敗：${error.message}`); }
    return;
  }
  // 改分攤類別：存進該預算，並立即重算分攤
  const cSel = event.target.closest("[data-alloc-category]");
  if (cSel) {
    const budgetId = cSel.getAttribute("data-alloc-category");
    try {
      await api(`/api/budgets/${budgetId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ alloc_category: cSel.value }) });
      await loadResource("budget");
      if (cSel.value) await api(`/api/budgets/${budgetId}/recompute`, { method: "POST" });
      await loadBudgetAllocations(budgetId);
    } catch (error) { window.alert(`設定分攤類別失敗：${error.message}`); }
    return;
  }
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
  if (action === "trace") {
    loadCaseTrace(id);
    return;
  }
  try {
    if (action === "submit") {
      await api(`/api/cases/${id}/submit`, { method: "POST" });
    }
    if (action === "approve") {
      await api(`/api/cases/${id}/approve`, { method: "POST" });
    }
    if (action === "cancel-review") {
      await api(`/api/cases/${id}/cancel-review`, { method: "POST" });
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

async function runTestDataClear() {
  if (!testDataStatus) return;
  testDataStatus.textContent = "清除中…";
  if (testDataClear) testDataClear.disabled = true;
  try {
    const res = await api("/api/dev-console/test-data/clear", { method: "POST" });
    const counts = res.data || {};
    const total = Object.values(counts).reduce((sum, n) => sum + (Number(n) || 0), 0);
    testDataStatus.textContent = `已清除 ${total} 筆 AI 測試資料`;
    await refresh();
  } catch (error) {
    testDataStatus.textContent = `失敗：${error.message}`;
  } finally {
    if (testDataClear) testDataClear.disabled = false;
  }
}
testDataClear?.addEventListener("click", () => {
  if (!window.confirm("確定清除所有 AI 測試資料？不影響真實資料，此動作無法復原。")) return;
  runTestDataClear();
});

async function loadBackfillStatus() {
  if (!backfillStatusEl) return;
  try {
    const res = await api("/api/dev-console/backfill/status");
    const d = res.data || {};
    const total = (Number(d.cases_missing) || 0) + (Number(d.settle_missing) || 0) + (Number(d.case_link_missing) || 0);
    backfillStatusEl.textContent = total
      ? `待補：案件系統編號 ${d.cases_missing} 筆、付款核銷編號 ${d.settle_missing} 筆、預算/專案未掛案件 ${d.case_link_missing} 筆`
      : "全部已有編號、已掛案件，無需補號。";
  } catch (error) {
    backfillStatusEl.textContent = `狀態載入失敗：${error.message}`;
  }
}

backfillRun?.addEventListener("click", async () => {
  if (!window.confirm("將替缺號的舊資料補上系統編號／核銷編號，並替沒掛案件的舊預算/專案自動配一個同名案件（只補缺的、不覆蓋既有）。確定執行？")) return;
  backfillRun.disabled = true;
  if (backfillStatusEl) backfillStatusEl.textContent = "補號中…";
  try {
    const res = await api("/api/dev-console/backfill/run", { method: "POST" });
    const d = res.data || {};
    if (backfillStatusEl) {
      backfillStatusEl.textContent = `已補：案件編號 ${d.cases_filled || 0} 筆、付款核銷 ${d.settle_filled || 0} 筆、預算/專案掛案件 ${d.case_links_filled || 0} 筆`;
    }
    await refresh();
  } catch (error) {
    if (backfillStatusEl) backfillStatusEl.textContent = `失敗：${error.message}`;
  } finally {
    backfillRun.disabled = false;
  }
});

// 匯出 CSV 已集中到「匯入/匯出」專區（不再逐模組注入按鈕）。
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
const searchScope = document.querySelector("#search-scope");           // 縮小範圍：只看某個模組
const searchResults = document.querySelector("#search-results");      // 側欄小提示
const searchPanel = document.querySelector("#search-panel");           // 中間大結果區
const searchResultsMain = document.querySelector("#search-results-main");
const SEARCH_LABEL = { case: "案件", contract: "合約", payment: "付款", document: "文件", budget: "預算", project: "專案", signoff: "簽呈", purchase: "請購", project_item: "專案子項" };
// 每種類型 → 對應模組 nav + 開啟該筆的動作（開編輯表單、顯示細節）
const SEARCH_NAV = {
  case: { href: "#cases-module", open: (id) => startEdit(id) },
  contract: { href: "#contracts-module", open: (id) => startResourceEdit("contract", id) },
  payment: { href: "#payments-module", open: (id) => startResourceEdit("payment", id) },
  document: { href: "#data-review", open: (id) => startResourceEdit("document", id) },
  budget: { href: "#budget", open: (id) => startResourceEdit("budget", id) },
  project: { href: "#projects", open: (id) => startResourceEdit("project", id) },
  signoff: { href: "#signoff", open: (id) => startResourceEdit("signoff", id) },
  purchase: { href: "#purchases", open: (id) => startResourceEdit("purchase", id) },
  project_item: { href: "#cases-module", open: (id) => openProjectItem(id) },
};
let searchTimer = null;

function closeSearchPanel() {
  if (searchPanel) searchPanel.hidden = true;
  if (lastPanelId) showModulePanel(lastPanelId);  // 還原搜尋前顯示的面板（含後台工具）
  else document.querySelector(".module-card.active") && activateModuleCard(document.querySelector(".module-card.active"));
}

async function openSearchHit(type, id) {
  const nav = SEARCH_NAV[type];
  if (!nav) return;
  if (searchPanel) searchPanel.hidden = true;
  navigateToPanel(nav.href.replace("#", ""));  // 後台工具(如文件→資料檢核)也能正確開啟
  try { await nav.open(id); } catch (_error) { /* 找不到就算了 */ }
  const targetForm = type === "case" ? form : resourceForms[type];
  targetForm?.scrollIntoView({ block: "center", behavior: "smooth" });
}

function renderSearchResults(rows, q, errMsg) {
  if (!searchPanel || !searchResultsMain) return;
  document.querySelectorAll(".module-panel, .module-extra").forEach((el) => { el.hidden = true; });
  searchPanel.hidden = false;
  const title = document.querySelector("#search-panel-title");
  if (errMsg) {
    if (title) title.textContent = "搜尋結果";
    searchResultsMain.innerHTML = `<p class="muted">搜尋失敗：${escapeHtml(errMsg)}</p>`;
    return;
  }
  if (title) title.textContent = `搜尋「${q}」（${rows.length} 筆）`;
  searchResultsMain.innerHTML = rows.length
    ? `<div class="grid-scroll"><table class="grid-table">
         <thead><tr><th>類型</th><th>編號</th><th>名稱</th><th>明細</th><th class="col-actions">操作</th></tr></thead>
         <tbody>${rows.map((r) => `<tr class="search-hit-row" data-hit-type="${r.type}" data-hit-id="${r.id}" title="點此開啟">
           <td><span class="badge">${escapeHtml(SEARCH_LABEL[r.type] || r.type)}</span></td>
           <td><strong>${escapeHtml(valueOrDash(r.code))}</strong></td>
           <td>${escapeHtml(r.title || "")}</td>
           <td class="muted">${escapeHtml(valueOrDash(r.detail))}</td>
           <td class="col-actions"><span class="search-go">開啟 →</span></td>
         </tr>`).join("")}</tbody>
       </table></div>`
    : `<p class="muted">找不到「${escapeHtml(q)}」。換個關鍵字試試。</p>`;
}

function runGlobalSearch() {
  clearTimeout(searchTimer);
  const q = globalSearch.value.trim();
  if (q.length < 2) {
    if (searchResults) { searchResults.hidden = true; searchResults.innerHTML = ""; }
    closeSearchPanel();
    return;
  }
  searchTimer = setTimeout(async () => {
    try {
      let rows = (await api(`/api/search?q=${encodeURIComponent(q)}`)).data || [];
      const scope = searchScope?.value;
      // 縮小範圍：只看選定的模組；選「專案」時工作項子項(project_item)也算在內，概念上同一個模組
      if (scope) rows = rows.filter((r) => r.type === scope || (scope === "project" && r.type === "project_item"));
      if (searchResults) { searchResults.hidden = false; searchResults.innerHTML = `<small class="muted">找到 ${rows.length} 筆，見中間結果 →</small>`; }
      renderSearchResults(rows, q);
    } catch (error) {
      renderSearchResults(null, q, error.message);
    }
  }, 250);
}
globalSearch?.addEventListener("input", runGlobalSearch);
searchScope?.addEventListener("change", runGlobalSearch);

document.querySelector("#search-results-main")?.addEventListener("click", (event) => {
  const row = event.target.closest("[data-hit-type]");
  if (row) openSearchHit(row.getAttribute("data-hit-type"), row.getAttribute("data-hit-id"));
});
document.querySelector("#search-close")?.addEventListener("click", () => {
  if (globalSearch) globalSearch.value = "";
  if (searchResults) { searchResults.hidden = true; searchResults.innerHTML = ""; }
  closeSearchPanel();
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

// 一條龍新案精靈：checkbox 開關各步驟必填欄位＋顯示/隱藏；付款需先勾⑤合約才能勾選。
// 用 data-wizard-step 範圍讀值，不用 FormData(form) 整支表單讀——多個步驟共用同樣的
// name（amount/note/vendor_name…），FormData.get() 只會拿到第一個，會互相蓋掉。
(() => {
  const wizardForm = document.querySelector("#wizard-form");
  if (!wizardForm) return;
  const contractToggle = wizardForm.querySelector('[data-wizard-toggle="contract"]');
  const paymentToggle = wizardForm.querySelector('[data-wizard-toggle="payment"]');
  const REQUIRED_BY_STEP = {
    budget: ["budget_code"],
    signoff: ["signoff_code", "subject"],
    purchase: ["purchase_code", "item_name"],
    contract: ["contract_code", "contract_name"],
    payment: ["payment_month", "payment_amount"],
  };

  function stepScope(step) {
    return wizardForm.querySelector(`[data-wizard-step="${step}"]`);
  }
  function setStepEnabled(step, on) {
    const scope = stepScope(step);
    const body = scope?.querySelector(".wizard-step-body");
    if (body) body.hidden = !on;
    for (const name of REQUIRED_BY_STEP[step] || []) {
      const el = scope?.querySelector(`[name="${name}"]`);
      if (el) el.required = on;
    }
  }
  function readStep(step, fields) {
    const scope = stepScope(step);
    if (!scope) return {};
    const out = {};
    for (const f of fields) {
      const el = scope.querySelector(`[name="${f}"]`);
      out[f] = el ? el.value.trim() : "";
    }
    return out;
  }
  const num = (v) => (v === "" || v == null ? 0 : Number(v));

  // 案名沿用（精靈版）：勾選簽呈/合約步驟時，若該步驟「名稱」欄位還空著，帶入①案件名稱當預設值
  // （仍可改，不鎖死）。跟獨立表單版同一個道理：合約正式名稱常跟案子暱稱有出入。
  const WIZARD_NAME_AUTOFILL_FIELD = { signoff: "subject", contract: "contract_name" };
  for (const toggle of wizardForm.querySelectorAll("[data-wizard-toggle]")) {
    toggle.addEventListener("change", () => {
      const step = toggle.getAttribute("data-wizard-toggle");
      setStepEnabled(step, toggle.checked);
      if (toggle.checked) {
        const fieldName = WIZARD_NAME_AUTOFILL_FIELD[step];
        const nameEl = fieldName && stepScope(step)?.querySelector(`[name="${fieldName}"]`);
        const titleEl = stepScope("case")?.querySelector('[name="title"]');
        if (nameEl && !nameEl.value.trim() && titleEl && titleEl.value.trim()) nameEl.value = titleEl.value.trim();
      }
      if (step === "contract") {
        if (!toggle.checked && paymentToggle) {
          paymentToggle.checked = false;
          paymentToggle.disabled = true;
          setStepEnabled("payment", false);
        } else if (toggle.checked && paymentToggle) {
          paymentToggle.disabled = false;
        }
      }
    });
  }

  wizardForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const statusEl = document.querySelector("#wizard-status");
    const resultEl = document.querySelector("#wizard-result");
    const c = readStep("case", ["case_code", "title", "owner", "amount", "fiscal_year", "note", "next_step", "due_date"]);
    const body = {
      case: {
        case_code: c.case_code, title: c.title, owner: c.owner, amount: num(c.amount),
        fiscal_year: c.fiscal_year, note: c.note, next_step: c.next_step, due_date: c.due_date,
      },
    };
    if (wizardForm.querySelector('[data-wizard-toggle="budget"]').checked) {
      const b = readStep("budget", ["budget_code", "category", "unit_name", "amount", "note"]);
      body.budget = { budget_code: b.budget_code, category: b.category, unit_name: b.unit_name, amount: num(b.amount), note: b.note };
    }
    if (wizardForm.querySelector('[data-wizard-toggle="signoff"]').checked) {
      const s = readStep("signoff", ["signoff_code", "subject", "applicant", "amount", "sign_date", "note"]);
      body.signoff = { signoff_code: s.signoff_code, subject: s.subject, applicant: s.applicant, amount: num(s.amount), sign_date: s.sign_date, note: s.note };
    }
    if (wizardForm.querySelector('[data-wizard-toggle="purchase"]').checked) {
      const p = readStep("purchase", ["purchase_code", "item_name", "vendor_name", "quantity", "amount", "note"]);
      body.purchase = { purchase_code: p.purchase_code, item_name: p.item_name, vendor_name: p.vendor_name, quantity: num(p.quantity), amount: num(p.amount), note: p.note };
    }
    if (contractToggle.checked) {
      const k = readStep("contract", ["contract_code", "contract_name", "vendor_name", "amount", "end_date"]);
      body.contract = { contract_code: k.contract_code, contract_name: k.contract_name, vendor_name: k.vendor_name, amount: num(k.amount), end_date: k.end_date };
    }
    if (paymentToggle.checked) {
      const pay = readStep("payment", ["payment_month", "payment_amount", "item", "net_amount", "tax_amount"]);
      body.payment = { payment_month: pay.payment_month, payment_amount: num(pay.payment_amount), item: pay.item, net_amount: num(pay.net_amount), tax_amount: num(pay.tax_amount) };
    }

    if (statusEl) statusEl.textContent = "送出中…";
    if (resultEl) resultEl.innerHTML = "";
    try {
      const created = (await api("/api/case-wizard", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })).data || {};
      if (statusEl) statusEl.textContent = "全部建立成功！";
      const lines = [`案件 ${escapeHtml(created.case.case_code)}（案號 ${escapeHtml(caseNumber(created.case) || "—")}）`];
      if (created.budget) lines.push(`預算 ${escapeHtml(created.budget.budget_code)}`);
      if (created.signoff) lines.push(`簽呈 ${escapeHtml(created.signoff.signoff_code)}`);
      if (created.purchase) lines.push(`請購 ${escapeHtml(created.purchase.purchase_code)}`);
      if (created.contract) lines.push(`合約 ${escapeHtml(created.contract.contract_code)}`);
      if (created.payment) lines.push(`付款 ${escapeHtml(created.payment.settle_no || "")}（${escapeHtml(created.payment.payment_month)}）`);
      if (resultEl) resultEl.innerHTML = `<div class="callout">${lines.join("<br/>")}</div>`;
      wizardForm.reset();
      for (const step of ["budget", "signoff", "purchase", "contract", "payment"]) setStepEnabled(step, false);
      if (paymentToggle) paymentToggle.disabled = true;
      await refresh();
    } catch (error) {
      if (statusEl) statusEl.textContent = `失敗：${error.message}`;
    }
  });
})();

populateFiscalYearSelects();
loadLoginOptions();
initializeSession().catch((error) => {
  cases.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  contracts.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  payments.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  documents.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
});
