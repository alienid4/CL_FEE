// 前端建置版本（單一來源）。每次改前端就 bump 版本號＋index.html 的 ?v=。
// 版本號「vX.Y.Z」永遠往上加、永不重複——同一天更新多次也分得出第幾版；號碼大＝新。
// 徽章顯示前後端版本號，對不上＝後端沒重啟，會亮警告。格式「vX.Y.Z · 日期 · 摘要」。
const BUILD_TAG = "v0.82.1 · 2026-08-28 · 修好固定Label造成的版面破圖、精靈①欄位全數補標籤";
(async () => {
  const badge = document.querySelector("#build-badge");
  if (!badge) return;
  const verOf = (s) => (String(s).split("·")[0] || "?").trim();  // 取「vX.Y.Z」那段（比對用）
  const stampOf = (s) => (String(s).split("·").slice(0, 2).join("·").trim() || "?");  // 「vX.Y.Z · 日期 時間」（顯示用）
  const front = verOf(BUILD_TAG);
  badge.textContent = `前端 ${stampOf(BUILD_TAG)} ｜ 後端 …`;
  try {
    const h = await fetch("/health", { credentials: "same-origin", cache: "no-store" }).then((r) => r.json());
    const back = verOf(h.build || "");
    const mismatch = front !== back;
    badge.textContent = `前端 ${stampOf(BUILD_TAG)} ｜ 後端 ${stampOf(h.build || "")}`;
    badge.classList.toggle("mismatch", mismatch);
    badge.title = mismatch
      ? `前後端版本不一致：前端 ${BUILD_TAG}、後端 ${h.build || "未知"}。請重啟 uvicorn 後端。`
      : `版本一致（${BUILD_TAG}）`;
  } catch (_e) {
    badge.textContent = `前端 ${stampOf(BUILD_TAG)} ｜ 後端 ?`;
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
const dashTabs = [...document.querySelectorAll("[data-dash-tab]")];
const dashPanels = [...document.querySelectorAll("[data-dash-panel]")];
const ioTabs = [...document.querySelectorAll("[data-io-tab]")];
const ioPanels = [...document.querySelectorAll("[data-io-panel]")];
const moduleCards = [...document.querySelectorAll(".module-card")];
const modulePanels = [...document.querySelectorAll(".module-panel")];
if (modulePanels.length && !document.querySelector("#module-unbuilt")) {
  const ph = document.createElement("section");
  ph.className = "module-panel";
  ph.id = "module-unbuilt";
  ph.hidden = true;
  ph.innerHTML =
    '<div class="watch-list"><div class="section-heading compact"><h2>此功能尚未啟用</h2></div>' +
    '<p class="muted">此模組（預算 / 專案 / 簽呈 / 費用）仍在規劃中，pilot 階段先不開放。核心流程請用「案件管理」。</p></div>';
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
// 誰能做審核決定（核准/退件/併案/駁回）：組長、部長、助理（使用者拍板 2026-07-30）。
// 唯一鐵則仍是「不能核准自己建立的案件」，所以組長自己送的案由部長或助理核。
const REVIEWER_ROLES = ["manager_assistant", "group_leader", "department_head"];
function isReviewer(user) {
  return !!user && REVIEWER_ROLES.includes(user.role_code);
}
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
    fields: ["contract_code", "contract_name", "vendor_name", "amount", "case_id", "purchase_id", "status", "end_date",
             "contract_type", "start_date", "warranty_end_date", "maintenance_end_date", "relation_type", "parent_contract_id",
             "vendor_tax_id", "owner", "group_name", "locations", "external_code", "progress_note", "end_reason",
             "signoff_ref", "signoff_no"],
    numberFields: ["amount", "case_id", "purchase_id", "parent_contract_id"],
    canDisable: true,
    columns: [
      { label: "系統編號", cell: (i) => systemCodeCell(SYS_PREFIX.contract, i.case_id) },
      { label: "系統識別碼", cell: (i) => `<span class="sys-code">${escapeHtml(valueOrDash(i.system_code))}</span>${relationTag(i)}` },
      { label: "合約編號", cell: (i) => `${escapeHtml(i.contract_code)}${contractSystemLink(i.external_code)}` },
      { label: "到期警示", cell: (i) => expiryLightCell(i) },
      { label: "合約名稱", cell: (i) => `<strong>${escapeHtml(i.contract_name)}</strong>` },
      { label: "類型", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.contract_type))}</span>` },
      { label: "廠商", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.vendor_name))}</span>` },
      { label: "金額", cls: "num", cell: (i) => `${money(i.amount)} 元` },
      { label: "合約期間", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.start_date))} ~ ${escapeHtml(valueOrDash(i.end_date))}</span>` },
      { label: "保固/維護到期", cell: (i) => warrantyCell(i) },
      { label: "狀態", cell: (i) => statusChip(i.status) },
      { label: "付款排程", cell: (i) => `<button type="button" class="secondary btn-sm" data-schedule="${i.id}">預計/實際</button>` },
      { label: "費用調整", cell: (i) => `<button type="button" class="secondary btn-sm" data-adjust="${i.id}">調整紀錄</button>` },
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
             "level", "progress_planned", "rag_status", "start_date", "end_date", "involves_procurement"],
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
      { label: "子項目", cls: "num", cell: (i) => {
          const t = Number(i.item_count || 0), d = Number(i.item_done || 0);
          // 還沒有工作項時直接給一鍵排標準流程（0803 之前建的專案沒有「涉及請購或合約」這個勾選）
          if (!t) {
            return `<button type="button" class="link-btn" data-standard-wbs="${i.id}"`
              + ` title="排入標準採購流程的工作項：需求確認→廠商報價→上簽申請與核准→議價→合約簽訂→執行／建置→驗收">＋標準流程</button>`;
          }
          return `<span title="完成 ${d} / 共 ${t} 個工作項">${d}/${t}</span>`;
        } },
      { label: "進度", cls: "num", cell: (i) => progressBarOnly(i.progress_planned, i.progress) },
      { label: "預計", cls: "num", cell: (i) => `${Number(i.progress_planned || 0)}%` },
      { label: "實際", cls: "num", cell: (i) => `${Number(i.progress || 0)}%` },
      // 燈號改自動判定：原本讀人工欄位 rag_status，沒人填就整欄都是「—」，等於白佔一欄。
      // 現在依起訖日與完成度即時算，跟工作項、線性圖同一套規則。
      { label: "燈號", cell: (i) => ragCell(ragOf(i)) },
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
      { label: "主旨", cell: (i) => `<strong>${escapeHtml(i.subject)}</strong>` },
      { label: "附件", cell: (i) => attachmentLink(i.attachment_ref) },
      { label: "簽核日", cell: (i) => `<span class="muted">${escapeHtml(valueOrDash(i.sign_date))}</span>` },
      { label: "金額", cls: "num", cell: (i) => `${money(i.amount)} 元` },
      { label: "狀態", cell: (i) => statusChip(i.status) },
    ],
  },
  purchase: {
    plural: "purchases", idAttr: "purchase-id", idField: "purchaseId", api: "/api/purchases",
    navCount: "nav-count-purchases", navLabel: "費用",
    fields: ["purchase_code", "item_name", "vendor_name", "quantity", "amount", "status", "case_id", "signoff_id", "note"],
    numberFields: ["quantity", "amount", "case_id", "signoff_id"], canDisable: true,
    columns: [
      { label: "系統編號", cell: (i) => systemCodeCell(SYS_PREFIX.purchase, i.case_id) },
      { label: "費用編號", cell: (i) => `<strong>${escapeHtml(i.purchase_code)}</strong>` },
      { label: "品項", cell: (i) => `<strong>${escapeHtml(i.item_name)}</strong>` },
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

// 系統編號：案件領「西元年+四位流水號」，各階段用同尾碼＋功能碼組成(12碼無連字號)，做跨階段勾稽
// 系統編號＝功能碼(4)＋西元年(4)＋流水號(4)，12 碼無連字號，例 Cont20260001（主管指定格式）。
// 同一案件底下各模組共用案件的「年+流水號」，差在功能碼，故查 20260001 可找到同案全部。
const SYS_PREFIX = { case: "Case", budget: "Budg", project: "Proj", signoff: "Sign", contract: "Cont", purchase: "Purc", payment: "Paym" };
function caseNumber(c) {
  return (c && c.fiscal_year && c.seq) ? `${c.fiscal_year}${String(c.seq).padStart(4, "0")}` : "";
}
// 使用者拍板 A 案：核准前只有暫時號（TMP+年+四位），核准當下才配正式號。
// 這樣被駁回／被併走的申請不會吃掉正式號，年度編號不跳號。
// 主管 2026-08-03 交代：系統配的號一律純英數，不用連字號／底線／中文，所以是 TMP20260001。
function caseTempNumber(c) {
  return (c && c.fiscal_year && c.temp_seq) ? `TMP${c.fiscal_year}${String(c.temp_seq).padStart(4, "0")}` : "";
}
// 使用者 2026-08-28 拍板：核准前不顯示任何編號，只顯示狀態，核准後才浮現正式案號。
// 原因是 TMP20260037 這種號碼卡在案名前面，對業務端是看不懂的亂碼，還壓過真正要看的案名。
// 暫時號沒有廢除（後端照配、稽核查得到、審核佇列那欄仍刻意顯示），只是不在一般清單搶版面。
// 用格式判斷而不是查案件狀態：進度列表這類 API 回的欄位不一定帶得到 status。
const TEMP_CODE_RE = /^TMP\d+$/;
function isTempCaseCode(code) {
  return TEMP_CODE_RE.test(String(code || ""));
}
// 各種「案號」欄共用：核准後給正式案號；核准前若只有暫時號就留白，
// 但匯入帶進來的真實舊編號要照顯示（那不是系統配的暫時號）。
function caseNumberCell(item) {
  const n = caseNumber(item);
  if (n) return `<strong>${escapeHtml(n)}</strong>`;
  if (isTempCaseCode(item.case_code)) {
    return `<span class="muted" title="尚未核准，核准後才配正式案號">—</span>`;
  }
  return `<strong>${escapeHtml(item.case_code || "—")}</strong>`;
}
// AC-11：系統自動配發的編號是給勾稽用的，不是業務人員要看的重點，版面上不該比業務名稱／狀態搶眼
function systemCodeCell(prefix, caseId) {
  const c = (caseCache || []).find((x) => String(x.id) === String(caseId));
  const n = caseNumber(c);
  if (n) return `<span class="sys-code">${escapeHtml(prefix + n)}</span>`;
  const tmp = caseTempNumber(c);
  if (tmp) return `<span class="temp-code" title="案件尚未核准，這是暫時號；核准後才會配正式編號">${escapeHtml(tmp)}</span>`;
  return `<span class="muted" title="尚未關聯案件，無系統編號">—</span>`;
}
// 付款經「合約」再回溯到案件（付款掛合約、合約掛案件）
function systemCodeCellPayment(payment) {
  const k = (resourceCaches.contract || []).find((x) => String(x.id) === String(payment.contract_id));
  return systemCodeCell(SYS_PREFIX.payment, k ? k.case_id : null);
}

// 合約細項不在本系統（使用者拍板 A4）：公司的合約都是 PDF，細項本來就在合約系統裡查，
// 這裡只留合約編號，清單上給一個「查合約系統」的連結直接跳過去，不做匯入也不重存一份。
// 樣板由後台設定：含 {code} 就把合約編號代進去，只填首頁網址就純粹開首頁。
// 帶過去的是「公司內部合約系統編號」(external_code)，不是本系統的合約編號——
// 助理 0803 明確要求兩者分開，拿本系統的號去查對方系統只會查不到。
let contractSystemUrl = "";
function contractSystemHref(code) {
  const base = String(contractSystemUrl || "").trim();
  if (!base) return "";
  const c = String(code || "").trim();
  if (!base.includes("{code}")) return base;
  return c ? base.replace("{code}", encodeURIComponent(c)) : "";
}
function contractSystemLink(code) {
  const href = contractSystemHref(code);
  if (!href) return "";
  return ` <a class="ext-link" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer"`
    + ` title="到公司合約系統查這份合約的細項">🔗 合約系統</a>`;
}

// 合約到期警示（助理 0803）：紅=已到期、黃=3 個月內、綠=還早、灰=已整併或不續約。
// 「沒填到期日」不併進綠燈——那是「不知道」不是「還早」，混在一起會讓人以為查過了。
const EXPIRY_LIGHT = {
  red: { dot: "🔴", label: "已到期" },
  yellow: { dot: "🟡", label: "3個月內到期" },
  green: { dot: "🟢", label: "尚未接近到期" },
  gray: { dot: "⚪", label: "已整併／不續約" },
  none: { dot: "—", label: "未設到期日" },
};
function expiryLightCell(k) {
  const s = EXPIRY_LIGHT[k.expiry_light] || EXPIRY_LIGHT.none;
  const warn = k.needs_progress_note
    ? ` <span class="badge danger" title="快到期或已到期卻沒寫處理到哪：到期追蹤還不能算完成，請補『合約進度說明』">缺進度說明</span>` : "";
  const note = String(k.progress_note || "").trim();
  return `<span title="${escapeHtml(s.label)}${note ? "｜" + escapeHtml(note) : ""}">${s.dot} ${escapeHtml(s.label)}</span>${warn}`;
}

// 合約與舊約的關係：續約/增購/整併都指向同一個「來源合約」欄位，清單上直接標出來源編號，
// 免得看到兩份相似的約以為重複建檔。
const RELATION_LABEL = { renew: "續約自", addon: "增購自", merge: "整併自" };
function relationTag(k) {
  const label = RELATION_LABEL[k.relation_type];
  if (!label) return "";
  const parent = (resourceCaches.contract || []).find((x) => String(x.id) === String(k.parent_contract_id));
  const code = parent ? parent.contract_code : (k.parent_contract_code || (k.parent_contract_id ? `#${k.parent_contract_id}` : "?"));
  return ` <span class="relation-tag" title="本約${label} ${escapeHtml(code)}">${label} ${escapeHtml(code)}</span>`;
}

// 保固/維護到期：跟合約到期日是兩回事（合約結束後保固常還在跑），過期的標紅提醒
function warrantyCell(k) {
  const today = new Date().toISOString().slice(0, 10);
  const part = (label, value) => {
    const v = String(value || "").trim();
    if (!v) return "";
    const cls = v < today ? "overdue" : "";
    return `<span class="warranty-part ${cls}">${label} ${escapeHtml(v)}</span>`;
  };
  const out = [part("保固", k.warranty_end_date), part("維護", k.maintenance_end_date)].filter(Boolean).join(" ");
  return out || `<span class="muted">-</span>`;
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
  // 線性進度圖併進案件清單、優先矩陣併進主管儀表板（助理 2026-08-03 回饋），兩邊都吃同一份資料
  if (tabName === "list" || tabName === "dashboard") loadCaseProgress();
  if (tabName === "dashboard") loadManagerFocus();
  if (tabName === "todo") loadTodoCards();
}

// 新案申請：常用動作，從頁籤列移到案件管理右上角常駐（助理回饋 2026-07-29）
document.querySelector("#new-case-apply")?.addEventListener("click", () => {
  activateCaseTab("wizard");
  document.querySelector("#wizard-form")?.scrollIntoView({ block: "nearest", behavior: "smooth" });
});

// 主管儀表板底下再分子頁籤（總覽/月度支出/單位別預算/廠商別合約/系統工具）——
// 使用者反饋一頁塞太多區塊要一直往下拉，改成一次只顯示一個子功能。
function activateDashTab(tabName) {
  for (const tab of dashTabs) {
    tab.classList.toggle("active", tab.dataset.dashTab === tabName);
  }
  for (const panel of dashPanels) {
    const isActive = panel.dataset.dashPanel === tabName;
    panel.hidden = !isActive;
    panel.classList.toggle("active", isActive);
  }
  if (tabName === "category") loadExpenseCategories();  // 切到才載，不拖慢首頁
}

// 匯入／匯出（資料管理）底下依模組分子頁籤，順序＝案件→預算→專案→簽呈→合約→請購→文件→付款，
// 使用者反饋 8 個模組塞成一整排卡片要一直往下滑，改成一次只顯示一個模組。
function activateIoTab(tabName) {
  for (const tab of ioTabs) {
    tab.classList.toggle("active", tab.dataset.ioTab === tabName);
  }
  for (const panel of ioPanels) {
    const isActive = panel.dataset.ioPanel === tabName;
    panel.hidden = !isActive;
    panel.classList.toggle("active", isActive);
  }
}

// ══ 全站統一燈號 ══════════════════════════════════════════════════════════
// 線性進度圖、工作項、專案清單共用同一套語意，避免同一個顏色在不同畫面代表不同事。
// 燈號定義以助理提供的文件為準（2026-07-29）：
//   綠＝如期執行中   黃＝有延遲風險，但目前不影響整體完成日
//   紅＝已延遲，且影響整體完成日   白＝未開始   灰＝已完成
//   （na 虛線空心＝這階段不適用，是本系統流程圖才有的第六種，助理文件未涉及）
// 原則：有顏色的才需要看。完成的東西淡出，不跟「正常」搶注意力。
const RAG_LABEL = {
  done: "已完成", todo: "未開始", live: "如期執行",
  soon: "有延遲風險", over: "已延遲", na: "不適用",
};

// 後端階段燈號沿用舊名（green＝該階段已完成…）。在這裡集中轉成統一語意，
// 就不必動後端契約，也不會弄壞既有測試。
const STAGE_TONE_TO_RAG = { green: "done", white: "todo", orange: "soon", red: "over", na: "na" };

// 依「開始日／結束日／完成度／今天」判定燈號；工作項與專案共用同一套判斷。
// 完成度 100 一律回 done，不看日期——做完的東西不該再被標成逾期。
function ragOf({ progress, start_date, end_date }) {
  const pct = Number(progress || 0);
  if (pct >= 100) return "done";

  const DAY = 86400000;
  const parse = (d) => { const t = d ? new Date(d).getTime() : NaN; return Number.isNaN(t) ? null : t; };
  const start = parse(start_date), end = parse(end_date), now = Date.now();

  // 未開始：一點進度都沒有，而且還沒到開始日（或根本沒排程）
  if (pct === 0 && ((start !== null && now < start) || (start === null && end === null))) return "todo";
  if (end !== null && now > end) return "over";     // 過了結束日還沒完成

  const nearDue = end !== null && (end - now) >= 0 && (end - now) <= 14 * DAY;
  let behind = false;
  if (start !== null && end !== null && end > start) {
    const expected = Math.max(0, Math.min(100, ((now - start) / (end - start)) * 100));
    behind = (expected - pct) > 10;                 // 落後時間軸推算的預期進度
  }
  return (nearDue || behind) ? "soon" : "live";
}

// 圓點＋文字，供清單欄位直接使用
function ragCell(rag) {
  const label = RAG_LABEL[rag] || rag;
  return `<span class="rag ${rag}" title="${label}"><span class="case-dot ${rag}"></span>${label}</span>`;
}

// ── 線性進度圖／處理優先矩陣：讀 /api/cases/progress，系統自動推導、唯讀 ──
const TONE_LABEL = { green: "完成", white: "還沒輪到", orange: "有延遲風險", red: "已延遲", na: "不適用" };
let lastProgressItems = [];  // 快取最近一次進度資料，供矩陣過濾器不重打 API 重繪
// 矩陣依狀態分類：可自由選要看哪一類（單看或組合看）
const PHASE_META = [
  { key: "active", label: "進行中／有風險" },
  { key: "done", label: "已完成" },
  { key: "not_started", label: "未開始" },
];
let matrixPhaseFilter = new Set(["active"]);  // 預設看進行中；點分類 chip 可切換
// 使用者拍板（2026-07-29）：矩陣只用時間軸，金額不代表優先，也不切四象限。
// 排序純看急迫度：逾期越久排越前、沒有期限可判斷的排最後。
function urgencyRank(it) {
  const d = it.urgency_days;
  return d == null ? Number.MAX_SAFE_INTEGER : d;
}

function urgencyText(days) {
  if (days == null) return "待確認";
  if (days < 0) return `逾期 ${-days} 天`;
  return `${days} 天`;
}

function renderProgressRow(it) {
  const dots = (it.stages || []).map((s) => {
    const rag = STAGE_TONE_TO_RAG[s.tone] || s.tone;   // 後端舊名 → 統一語意
    // data-stage：點這一站直接跳到追溯鏈裡對應的模組卡片（使用者 2026-08-28：
    // 「對預算 1 有疑問，點預算就要看得到預算 1」），不用自己回清單再翻。
    return `<span class="case-step ${rag}" data-stage="${escapeHtml(s.key || "")}" role="button" tabindex="0"`
      + ` title="${escapeHtml(s.label)}：${RAG_LABEL[rag] || s.tone}${s.days != null ? "（" + urgencyText(s.days) + "）" : ""}｜點此查看本案的${escapeHtml(s.label)}">`
      + `<span class="case-dot ${rag}"></span><span>${escapeHtml(s.label)}</span></span>`;
  }).join("");
  const amt = it.amount ? `${money(it.amount)} 元` : "—";
  const code = isTempCaseCode(it.case_code) ? "" : `${escapeHtml(it.case_code)}　`;
  return `<div class="case-progress-row" data-case-id="${it.case_id}">
    <div class="case-progress-name"><b>${code}${escapeHtml(it.title)}</b>
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
      el.className = `matrix-item tone-${m.tone || "white"}`;
      el.style.left = `${m.x}%`;
      el.style.top = `${m.y}%`;
      el.dataset.caseId = it.case_id;  // 點散佈點直接開這個案子的追溯鏈
      el.title = `${escapeHtml(it.title)}｜${urgencyText(it.urgency_days)}（點擊看細項）`;
      el.innerHTML = `<b>${escapeHtml(it.title.slice(0, 8))}</b><span>${escapeHtml(urgencyText(it.urgency_days))}</span>`;
      box.appendChild(el);
    }
  }
  if (body) {
    const sorted = [...items].sort((a, b) => urgencyRank(a) - urgencyRank(b));
    body.innerHTML = sorted.length
      ? sorted.map((it, i) => `<tr data-case-id="${it.case_id}">
          <td>${i + 1}</td>
          <td>${escapeHtml(it.title)}</td>
          <td class="num">${it.amount ? money(it.amount) + " 元" : "—"}</td>
          <td>${urgencyText(it.urgency_days)}</td>
          <td>${escapeHtml(it.matrix.reason || "")}</td>
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
// 進度圖／矩陣點擊直達細項：在總覽看到「這件要立即處理」之後，原本得自己回案件清單再翻一次；
// 現在點那一列（或矩陣上那個點）就切回清單並展開它的追溯鏈，一頁看完花多少、欠多少。
// 進度列的階段名稱 → 追溯鏈裡的卡片。發票沒有自己的卡片（發票狀態記在付款上），導到付款。
const STAGE_TO_TRACE_CARD = {
  budget: "budget", project: "project", signoff: "signoff",
  contract: "contract", purchase: "purchase", payment: "payment", invoice: "payment",
};
function openCaseFromOverview(caseId, stage) {
  if (!caseId) return;
  activateCaseTab("list");
  loadCaseTrace(caseId, STAGE_TO_TRACE_CARD[stage] || "");
}
for (const sel of ["#case-progress-list", "#case-matrix", "#case-matrix-body"]) {
  document.querySelector(sel)?.addEventListener("click", (event) => {
    const el = event.target.closest("[data-case-id]");
    if (!el) return;
    const step = event.target.closest("[data-stage]");
    openCaseFromOverview(el.getAttribute("data-case-id"), step?.getAttribute("data-stage"));
  });
  // 階段點是 role="button"，鍵盤也要能用（不然只有滑鼠使用者享受得到）
  document.querySelector(sel)?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const step = event.target.closest("[data-stage]");
    const el = event.target.closest("[data-case-id]");
    if (!step || !el) return;
    event.preventDefault();
    openCaseFromOverview(el.getAttribute("data-case-id"), step.getAttribute("data-stage"));
  });
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
// 一鍵排標準採購流程（助理 0803）：七個工作項一次建好，承辦只要往下填日期與進度。
// 同名的跳過，所以重複按不會長出兩套，也不會蓋掉已經填好的內容。
document.querySelector("#projects-list")?.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-standard-wbs]");
  if (!btn) return;
  const id = btn.getAttribute("data-standard-wbs");
  btn.disabled = true;
  btn.textContent = "排入中…";
  try {
    const r = (await api(`/api/projects/${id}/standard-wbs`, { method: "POST" })).data;
    // 先讓人看到結果再重繪（重繪會把這顆按鈕換成「0/7」，不先講一聲會不知道發生什麼事）
    const skipped = r.skipped_count ? `，跳過 ${r.skipped_count} 個已有的` : "";
    btn.textContent = `已排入 ${r.created_count} 項${skipped}`;
    setTimeout(() => loadResource("project"), 900);
  } catch (error) {
    btn.disabled = false;
    btn.textContent = "＋標準流程";
    window.alert(`排入標準流程失敗：${error.message}`);
  }
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

// ── 費用模組三層（助理 0803 附件一）：主檔 → 費用區段＋排程 → (第三層核銷之後做) ──
// 第一層清單 → 點「費用排程」展開該筆的費用區段 → 產生排程 → 放大預覽逐期修正 → 確認排程。
const EXPENSE_MODES = [
  { key: "milestone", label: "里程碑" },
  { key: "periodic", label: "定期費用" },
  { key: "commitment", label: "最低承諾金額" },
];
const FREQ_LABEL = { monthly: "每月", quarterly: "每季", semi: "每半年", yearly: "每年" };
let expenseCache = [];

async function loadExpenses() {
  const box = document.querySelector("#expense-list");
  if (!box) return;
  try {
    expenseCache = (await api("/api/expenses")).data || [];
  } catch (_e) { return; }
  if (!expenseCache.length) {
    box.innerHTML = `<p class="muted">還沒有費用主檔。點右上「＋ 新增費用主檔」建立：
      選好合約（或勾無合約）→ 選費用排程模式 → 再到下面設定各期費用。</p>`;
    return;
  }
  const rows = expenseCache.map((e) => {
    const modes = String(e.modes || "").split(",").filter(Boolean)
      .map((m) => (EXPENSE_MODES.find((x) => x.key === m) || {}).label || m).join("、");
    const k = (resourceCaches.contract || []).find((c) => String(c.id) === String(e.contract_id));
    return `<tr data-expense-id="${e.id}">
      <td><strong>${escapeHtml(e.expense_name || "")}</strong></td>
      <td>${k ? escapeHtml(k.contract_code) : '<span class="muted">無合約</span>'}</td>
      <td>${escapeHtml(valueOrDash(e.vendor_name))}</td>
      <td class="num">${money(e.total_amount)} 元</td>
      <td>${escapeHtml(modes)}</td>
      <td>${escapeHtml(valueOrDash(e.owner))}</td>
      <td><button type="button" class="secondary btn-sm" data-exp-sections="${e.id}">費用排程</button>
          <button type="button" class="secondary btn-sm" data-exp-edit="${e.id}">編輯</button></td>
    </tr>`;
  }).join("");
  box.innerHTML = `<div class="grid-scroll"><table class="grid-table">
    <thead><tr><th>費用名稱</th><th>合約</th><th>廠商</th><th class="num">合約總費用</th>
    <th>排程模式</th><th>承辦人</th><th class="col-actions">操作</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

async function loadExpenseSections(expenseId) {
  const box = document.querySelector("#expense-section-panel");
  if (!box) return;
  box.hidden = false;
  box.dataset.expenseId = expenseId;
  box.innerHTML = `<p class="muted">載入費用區段…</p>`;
  try {
    const [sections, check] = await Promise.all([
      api(`/api/expenses/${expenseId}/sections`).then((r) => r.data || []),
      api(`/api/expenses/${expenseId}/check`).then((r) => r.data),
    ]);
    box.innerHTML = renderExpenseSections(expenseId, sections, check);
  } catch (e) {
    box.innerHTML = `<p class="error">費用區段載入失敗：${escapeHtml(e.message)}</p>`;
  }
}

function renderExpenseSections(expenseId, sections, check) {
  const exp = expenseCache.find((x) => String(x.id) === String(expenseId)) || {};
  // 總費用 vs 各區段加總：對不上就講差多少，別讓人自己算
  const balance = check.balanced
    ? `<span class="chip done">各區段合計 ${money(check.section_total)} 元＝合約總費用</span>`
    : `<span class="chip todo">各區段合計 ${money(check.section_total)} 元，`
      + `與合約總費用 ${money(check.total_amount)} 元差 ${money(Math.abs(check.diff))} 元`
      + `（${check.diff > 0 ? "還少" : "多"}了）</span>`;
  const missing = (check.missing_sections || []).length
    ? `<p class="muted">還沒建立的模式：${escapeHtml(check.missing_sections.join("、"))}</p>` : "";
  const list = sections.length ? sections.map((s) => {
    const mode = (EXPENSE_MODES.find((m) => m.key === s.mode) || {}).label || s.mode;
    const confirmed = s.status === "confirmed";
    const detail = s.mode === "periodic"
      ? `${FREQ_LABEL[s.frequency] || s.frequency || "—"}．${s.periods} 期．首期 ${money(s.first_amount)} 元（${escapeHtml(s.first_month || "—")}）`
      : `${s.periods} 期．${s.price_method === "percent" ? "依比例計算" : s.price_method === "fixed" ? "固定金額" : "—"}`;
    return `<tr${s.archived ? ' class="row-archived"' : ""}>
      <td><strong>${escapeHtml(mode)}</strong>${s.version > 1 ? ` <span class="muted">v${s.version}</span>` : ""}
        ${s.archived ? ' <span class="badge" title="重新編輯前的版本，只供查閱，金額不計入加總">舊版</span>' : ""}</td>
      <td>${escapeHtml(valueOrDash(s.section_name))}</td>
      <td class="num">${money(s.section_amount)} 元</td>
      <td>${escapeHtml(detail)}</td>
      <td class="num">${s.schedule_count}</td>
      <td>${confirmed
        ? `<span class="chip done">已確認</span><br /><small class="muted">${escapeHtml(s.confirmed_by || "")} ${escapeHtml((s.confirmed_at || "").slice(0, 16))}</small>`
        : '<span class="chip todo">草稿</span>'}</td>
      <td>
        ${confirmed
          ? `<button type="button" class="secondary btn-sm" data-exp-reopen="${s.id}" title="已確認的排程要改：系統會建立新版本並保留原版">重新編輯</button>`
          : `<button type="button" class="secondary btn-sm" data-exp-generate="${s.id}" title="依上面的設定產生各期排程；重產會蓋掉目前的明細">產生排程</button>`}
        <button type="button" class="btn-sm" data-exp-preview="${s.id}">預覽費用排程</button>
        ${s.mode === "commitment"
          ? `<button type="button" class="secondary btn-sm" data-exp-achievement="${s.id}"
               title="各承諾期的承諾額、實際認列、達成率、未達差額與超額轉入">承諾達成</button>` : ""}
      </td></tr>`;
  }).join("") : `<tr><td colspan="7" class="muted">這筆費用還沒有費用區段——用下面的表單依模式建立。</td></tr>`;

  const modes = String(exp.modes || "").split(",").filter(Boolean);
  const modeOptions = modes.map((m) =>
    `<option value="${m}">${escapeHtml((EXPENSE_MODES.find((x) => x.key === m) || {}).label || m)}</option>`).join("");
  return `<div class="sched-head">
      <h3>${escapeHtml(exp.expense_name || "")}　費用區段</h3>
      <button type="button" class="secondary btn-sm" data-exp-close>收合</button>
    </div>
    <p>${balance}</p>${missing}
    <div class="grid-scroll"><table class="grid-table">
      <thead><tr><th>模式</th><th>區段名稱</th><th class="num">區段金額</th><th>設定</th>
      <th class="num">期數</th><th>狀態</th><th class="col-actions">操作</th></tr></thead>
      <tbody>${list}</tbody></table></div>
    <form class="resource-form" data-exp-section-form>
      <select data-sec-mode required>${modeOptions}</select>
      <input data-sec-name placeholder="費用區段名稱（例：軟體授權及專業服務費）" />
      <input data-sec-amount type="number" min="0" step="1" placeholder="費用區段金額 *" required />
      <input data-sec-periods type="number" min="1" step="1" placeholder="總期數／承諾期數 *" required />
      <select data-sec-price title="里程碑計價方式" data-when="milestone">
        <option value="percent">依比例計算</option>
        <option value="fixed">固定金額</option>
      </select>
      <select data-sec-freq title="費用頻率" data-when="periodic commitment">
        <option value="">（選）費用頻率</option>
        <option value="monthly">每月</option><option value="quarterly">每季</option>
        <option value="semi">每半年</option><option value="yearly">每年</option>
      </select>
      <input data-sec-first-amount type="number" min="0" step="1" data-when="periodic commitment"
             placeholder="第一期費用／第一期承諾金額" />
      <input data-sec-first-month type="month" data-when="periodic" placeholder="第一期費用年月" />
      <input data-sec-first-due type="date" data-when="periodic" placeholder="第一期預計應付日" />
      <input data-sec-period-start type="date" data-when="commitment" placeholder="第一期承諾起日" />
      <input data-sec-span type="number" min="1" step="1" data-when="commitment"
             placeholder="每期期間長度（月）" title="例如 12 個月；要能被費用頻率整除，否則同一期會被切一半" />
      <select data-sec-next-rule data-when="commitment" title="後續各期承諾金額怎麼來">
        <option value="same">後續同第一期金額</option>
        <option value="growth">依固定比例增減</option>
        <option value="manual">預覽後逐期調整</option>
      </select>
      <input data-sec-growth type="number" step="0.1" data-when="commitment" placeholder="增減比例 %" />
      <select data-sec-basis data-when="commitment" title="達成金額認列基礎">
        <option value="usage">達成認列：使用金額</option>
        <option value="payable">達成認列：應付金額</option>
      </select>
      <label class="check-inline" data-when="commitment">
        <input type="checkbox" data-sec-carry /> 超額轉入次期
      </label>
      <input data-sec-shortfall data-when="commitment" placeholder="期末未達處理方式（差額補繳／另案處理…）" />
      <button type="submit">新增費用區段</button>
    </form>`;
}

async function loadExpensePreview(sectionId) {
  const box = document.querySelector("#expense-preview-panel");
  if (!box) return;
  box.hidden = false;
  box.dataset.sectionId = sectionId;
  box.innerHTML = `<p class="muted">載入排程…</p>`;
  try {
    box.innerHTML = renderExpensePreview((await api(`/api/expense-sections/${sectionId}/preview`)).data);
  } catch (e) {
    box.innerHTML = `<p class="error">排程預覽載入失敗：${escapeHtml(e.message)}</p>`;
  }
}

function renderExpensePreview(res) {
  const sec = res.section || {};
  const isMilestone = sec.mode === "milestone";
  const confirmed = sec.status === "confirmed";
  const rows = (res.schedules || []).map((s) => `<tr>
    <td>第 ${s.seq} 期</td>
    <td>${isMilestone ? `<select data-sched-field="milestone_name" data-sched-id="${s.id}"${confirmed ? " disabled" : ""}>
          <option value="">（未選）</option>
          ${["簽約款", "交付款", "驗收款", "自訂"].map((n) =>
            `<option value="${n}"${s.milestone_name === n ? " selected" : ""}>${n}</option>`).join("")}
        </select>
        <input data-sched-field="custom_name" data-sched-id="${s.id}" value="${escapeHtml(s.custom_name || "")}"
               placeholder="自訂名稱" class="w-note"${confirmed ? " disabled" : ""} />`
      : '<span class="muted">不適用</span>'}</td>
    <td class="num">${isMilestone && sec.price_method === "percent"
      ? `<input data-sched-field="percent" data-sched-id="${s.id}" type="number" min="0" max="100" step="0.01"
                value="${Number(s.percent || 0)}" class="w-seq"${confirmed ? " disabled" : ""} /> %`
      : '<span class="muted">—</span>'}</td>
    <td class="num"><input data-sched-field="planned_amount" data-sched-id="${s.id}" type="number" min="0" step="1"
        value="${Number(s.planned_amount || 0)}"${confirmed ? " disabled" : ""} /></td>
    <td><input data-sched-field="expense_month" data-sched-id="${s.id}" type="month"
        value="${escapeHtml(s.expense_month || "")}"${confirmed ? " disabled" : ""} /></td>
    <td><input data-sched-field="due_date" data-sched-id="${s.id}" type="date"
        value="${escapeHtml(s.due_date || "")}"${confirmed ? " disabled" : ""} /></td>
    <td><input data-sched-field="note" data-sched-id="${s.id}" value="${escapeHtml(s.note || "")}"
        placeholder="備註" class="w-note"${confirmed ? " disabled" : ""} />
        ${s.manual_adjusted ? '<span class="badge" title="這一期被人工調整過">人工調整</span>' : ""}</td>
  </tr>`).join("");

  const problems = (res.problems || []).length
    ? `<ul class="note-list">${res.problems.map((p) => `<li class="error">${escapeHtml(p)}</li>`).join("")}</ul>`
    : `<p class="chip done">檢核通過：各期合計 ${money(res.scheduled_total)} 元＝費用區段金額</p>`;

  return `<div class="sched-head">
      <h3>費用排程預覽　<span class="muted">${escapeHtml((EXPENSE_MODES.find((m) => m.key === sec.mode) || {}).label || "")}
        ${sec.version > 1 ? `· 第 ${sec.version} 版` : ""}</span></h3>
      <button type="button" class="secondary btn-sm" data-exp-preview-close>收合</button>
    </div>
    ${problems}
    <div class="grid-scroll"><table class="grid-table">
      <thead><tr><th>期別</th><th>里程碑名稱</th><th class="num">比例</th><th class="num">應付費用</th>
      <th>費用年月</th><th>預計應付日</th><th>備註</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="7" class="muted">還沒有排程明細，先按「產生排程」。</td></tr>'}</tbody>
    </table></div>
    ${confirmed
      ? `<p class="muted">這一版已確認（${escapeHtml(sec.confirmed_by || "")} ${escapeHtml((sec.confirmed_at || "").slice(0, 16))}），
         要改請回上面按「重新編輯」。收到帳單或發票時，點下面那一期的「請款／核銷」登錄。</p>
         <div class="grid-scroll"><table class="grid-table">
           <thead><tr><th>期別</th><th class="num">應付費用</th><th>費用年月</th><th class="col-actions">第三層</th></tr></thead>
           <tbody>${(res.schedules || []).map((s) => `<tr>
             <td>第 ${s.seq} 期${s.commit_period ? `（第 ${s.commit_period} 承諾期）` : ""}</td>
             <td class="num">${money(s.planned_amount)} 元</td>
             <td>${escapeHtml(valueOrDash(s.expense_month))}</td>
             <td><button type="button" class="secondary btn-sm" data-exp-settle="${s.id}">請款／核銷</button>
                 ${sec.mode === "commitment"
                   ? `<button type="button" class="secondary btn-sm" data-exp-actual="${s.id}"
                        title="登錄這一期實際用了多少，系統才算得出承諾達成率">登錄實際費用</button>` : ""}</td>
           </tr>`).join("")}</tbody></table></div>`
      : `<button type="button" data-exp-confirm="${sec.id}"${res.can_confirm ? "" : " disabled"}
           title="${res.can_confirm ? "檢核通過，確認後會記下確認人與時間" : "檢核未通過，先修正上面列出的問題"}">確認排程</button>`}`;
}

// 費用模組的互動：清單、區段、預覽三塊都掛在「費用」模組頁底下，用事件委派接。
document.addEventListener("click", async (event) => {
  const t = event.target;
  const sections = t.closest("[data-exp-sections]");
  if (sections) {
    await loadExpenseSections(sections.getAttribute("data-exp-sections"));
    document.querySelector("#expense-section-panel")?.scrollIntoView({ block: "nearest" });
    return;
  }
  if (t.closest("[data-exp-close]")) {
    document.querySelector("#expense-section-panel").hidden = true;
    document.querySelector("#expense-preview-panel").hidden = true;
    return;
  }
  if (t.closest("[data-exp-preview-close]")) {
    document.querySelector("#expense-preview-panel").hidden = true;
    return;
  }
  const preview = t.closest("[data-exp-preview]");
  if (preview) {
    await loadExpensePreview(preview.getAttribute("data-exp-preview"));
    document.querySelector("#expense-preview-panel")?.scrollIntoView({ block: "nearest" });
    return;
  }
  const gen = t.closest("[data-exp-generate]");
  if (gen) {
    const id = gen.getAttribute("data-exp-generate");
    gen.disabled = true;
    gen.textContent = "產生中…";
    try {
      await api(`/api/expense-sections/${id}/generate`, { method: "POST" });
      await loadExpenseSections(document.querySelector("#expense-section-panel").dataset.expenseId);
      await loadExpensePreview(id);   // 產完直接打開預覽，接著就能逐期填
    } catch (e) {
      gen.disabled = false;
      gen.textContent = "產生排程";
      window.alert(`產生排程失敗：${e.message}`);
    }
    return;
  }
  const confirmBtn = t.closest("[data-exp-confirm]");
  if (confirmBtn) {
    const id = confirmBtn.getAttribute("data-exp-confirm");
    confirmBtn.disabled = true;
    confirmBtn.textContent = "確認中…";
    try {
      await api(`/api/expense-sections/${id}/confirm`, { method: "POST" });
      await loadExpenseSections(document.querySelector("#expense-section-panel").dataset.expenseId);
      await loadExpensePreview(id);
    } catch (e) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = "確認排程";
      window.alert(`確認排程失敗：${e.message}`);
    }
    return;
  }
  const reopen = t.closest("[data-exp-reopen]");
  if (reopen) {
    if (!window.confirm("重新編輯會建立新版本，原本已確認的那一版連明細會完整保留。要繼續嗎？")) return;
    const id = reopen.getAttribute("data-exp-reopen");
    try {
      await api(`/api/expense-sections/${id}/reopen`, { method: "POST" });
      await loadExpenseSections(document.querySelector("#expense-section-panel").dataset.expenseId);
      await loadExpensePreview(id);
    } catch (e) { window.alert(`重新編輯失敗：${e.message}`); }
    return;
  }
  const ach = t.closest("[data-exp-achievement]");
  if (ach) {
    await loadCommitmentAchievement(ach.getAttribute("data-exp-achievement"));
    return;
  }
  const settle = t.closest("[data-exp-settle]");
  if (settle) {
    openSettlementForm(settle.getAttribute("data-exp-settle"));
    return;
  }
  const actual = t.closest("[data-exp-actual]");
  if (actual) {
    openActualForm(actual.getAttribute("data-exp-actual"));
    return;
  }
  const prog = t.closest("[data-settle-progress]");
  if (prog) {
    const [id, next] = prog.getAttribute("data-settle-progress").split(":");
    try {
      const r = (await api(`/api/settlements/${id}/progress`, {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(next === "confirm" ? { confirmed: true } : { progress: next }),
      })).data;
      await loadSettlements(document.querySelector("#expense-section-panel").dataset.expenseId);
      if (r.notify) {
        window.alert(r.notify === "settler" ? "已標記完成，系統會通知核銷者。" : "已標記可預備上簽，系統會通知承辦確認。");
      }
    } catch (e) { window.alert(`更新進度失敗：${e.message}`); }
    return;
  }
  const edit = t.closest("[data-exp-edit]");
  if (edit) startExpenseEdit(edit.getAttribute("data-exp-edit"));
});

// 新增費用區段的表單：依選到的模式只顯示該模式要填的欄位（助理：選了模式只顯示適用欄位）
document.addEventListener("change", (event) => {
  const sel = event.target.closest("[data-sec-mode]");
  if (!sel) return;
  const form = sel.closest("[data-exp-section-form]");
  for (const el of form.querySelectorAll("[data-when]")) {
    const on = el.getAttribute("data-when").split(" ").includes(sel.value);
    el.style.display = on ? "" : "none";
  }
});

// 第三層：請款／核銷。助理明訂一次作業只對一筆排程＋一張發票，所以入口是「某一期」的按鈕，
// 廠商、統編、計費期間、核銷月份都由系統帶，人只填發票與請款金額。
function openSettlementForm(scheduleId) {
  const box = document.querySelector("#expense-preview-panel");
  box.hidden = false;
  box.innerHTML = `<div class="sched-head">
      <h3>請款／核銷（第 ${escapeHtml(scheduleId)} 期排程）</h3>
      <button type="button" class="secondary btn-sm" data-exp-preview-close>收合</button>
    </div>
    <form class="resource-form" data-settle-form data-schedule-id="${scheduleId}">
      <input name="invoice_date" type="date" placeholder="發票日期" required />
      <input name="invoice_no" placeholder="發票號碼 *" required />
      <input name="claim_amount" type="number" min="0" step="1" placeholder="請款金額 *" required />
      <select name="settler" class="personnel-select" data-placeholder="核銷者"></select>
      <input name="signoff_no" placeholder="費用核銷簽呈編號（上簽後填）" />
      <input name="doc_ref" placeholder="請款文件（核銷申請書／付款憑證／請購簽呈…）" />
      <input name="diff_reason" placeholder="差異原因（請款金額與排程不同時必填）" />
      <input name="note" placeholder="備註（退件、差異或特殊情形）" />
      <button type="submit">建立請款／核銷</button>
    </form>
    <div id="settlement-list"></div>`;
  populatePersonnelSelects();
  loadSettlements(document.querySelector("#expense-section-panel").dataset.expenseId);
}

function openActualForm(scheduleId) {
  const box = document.querySelector("#expense-preview-panel");
  box.hidden = false;
  box.innerHTML = `<div class="sched-head">
      <h3>登錄實際費用（最低承諾金額）</h3>
      <button type="button" class="secondary btn-sm" data-exp-preview-close>收合</button>
    </div>
    <p class="muted">承諾金額只是門檻，這裡登錄的是這一期實際用了多少；系統再回頭算承諾達成率。
      認列金額＝使用金額＋調整金額，由系統算，不用自己填。</p>
    <form class="resource-form" data-actual-form data-schedule-id="${scheduleId}">
      <input name="usage_amount" type="number" min="0" step="1" placeholder="當期使用／應付金額 *" required />
      <input name="description" placeholder="費用說明" />
      <input name="adjust_amount" type="number" step="1" placeholder="調整金額（折讓／退款，可為負）" />
      <input name="adjust_reason" placeholder="調整原因（調整金額不為 0 時必填）" />
      <button type="submit">登錄</button>
    </form>`;
}

document.addEventListener("submit", async (event) => {
  const sf = event.target.closest("[data-settle-form]");
  const af = event.target.closest("[data-actual-form]");
  if (!sf && !af) return;
  event.preventDefault();
  const form = sf || af;
  const sid = form.getAttribute("data-schedule-id");
  const data = Object.fromEntries(new FormData(form).entries());
  for (const k of ["claim_amount", "usage_amount", "adjust_amount"]) {
    if (k in data) data[k] = Number(data[k] || 0);
  }
  try {
    await api(`/api/expense-schedules/${sid}/${sf ? "settlements" : "actuals"}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
    });
    const expenseId = document.querySelector("#expense-section-panel").dataset.expenseId;
    if (sf) { openSettlementForm(sid); } else { await loadExpenseSections(expenseId); }
  } catch (e) { window.alert(`儲存失敗：${e.message}`); }
});

// 某費用主檔底下的請款／核銷清單＋累計、待請款（助理 0803 第七節的自動計算）
async function loadSettlements(expenseId) {
  const box = document.querySelector("#settlement-list");
  if (!box || !expenseId) return;
  try {
    const res = (await api(`/api/expenses/${expenseId}/settlements`)).data;
    const NEXT = { invoice_pending: ["ready_to_sign", "改為可預備上簽"], ready_to_sign: ["confirm", "確認完成"],
                   signing: ["approved", "款項已核准"], approved: ["submitted", "提交會計（結案）"] };
    const rows = (res.settlements || []).map((s) => {
      const step = s.progress === "ready_to_sign" && s.confirmed ? ["signing", "送出簽核"] : NEXT[s.progress];
      return `<tr>
        <td>${escapeHtml(valueOrDash(s.invoice_no))}<br /><small class="muted">${escapeHtml(valueOrDash(s.invoice_date))}</small></td>
        <td>${escapeHtml(valueOrDash(s.settle_month))}</td>
        <td class="num">${money(s.claim_amount)} 元</td>
        <td>${escapeHtml(s.progress_label)}${s.confirmed ? ' <span class="chip done">已確認完成</span>' : ""}</td>
        <td>${escapeHtml(valueOrDash(s.settler))}</td>
        <td>${step ? `<button type="button" class="secondary btn-sm" data-settle-progress="${s.id}:${step[0]}">${escapeHtml(step[1])}</button>` : '<span class="muted">已結案</span>'}</td>
      </tr>`;
    }).join("");
    box.innerHTML = `<h4>這筆費用的請款／核銷</h4>
      <p><span class="chip">排程總額 ${money(res.scheduled_total)} 元</span>
         <span class="chip">累計請款 ${money(res.claimed_total)} 元</span>
         <span class="chip ${res.unclaimed_total > 0 ? "todo" : "done"}">待請款 ${money(res.unclaimed_total)} 元</span></p>
      <div class="grid-scroll"><table class="grid-table">
        <thead><tr><th>發票</th><th>核銷月份</th><th class="num">請款金額</th><th>處理進度</th>
        <th>核銷者</th><th class="col-actions">下一步</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="6" class="muted">還沒有請款／核銷紀錄。</td></tr>'}</tbody>
      </table></div>`;
  } catch (e) {
    box.innerHTML = `<p class="error">請款／核銷載入失敗：${escapeHtml(e.message)}</p>`;
  }
}

// 最低承諾金額：各承諾期的達成情形（承諾額／實際認列／達成率／未達差額／超額轉入）
async function loadCommitmentAchievement(sectionId) {
  const box = document.querySelector("#expense-preview-panel");
  if (!box) return;
  box.hidden = false;
  box.innerHTML = `<p class="muted">計算承諾達成情形…</p>`;
  try {
    const res = (await api(`/api/expense-sections/${sectionId}/achievement`)).data;
    const rows = (res.periods || []).map((p) => `<tr>
      <td>第 ${p.commit_period} 承諾期</td>
      <td class="num">${money(p.committed)} 元</td>
      <td class="num">${p.logged ? `${money(p.recognized)} 元` : '<span class="muted">尚未登錄</span>'}</td>
      <td class="num">${p.rate === null ? '<span class="muted" title="這一期還沒有任何實際費用登錄，不是達成率 0%">—</span>' : `${p.rate}%`}</td>
      <td class="num">${p.shortfall ? `<b class="owe">${money(p.shortfall)} 元</b>` : "—"}</td>
      <td class="num">${p.excess ? `${money(p.excess)} 元` : "—"}</td>
      <td class="num">${res.carry_over && p.carry_in_next ? `${money(p.carry_in_next)} 元` : "—"}</td>
    </tr>`).join("");
    box.innerHTML = `<div class="sched-head">
        <h3>承諾達成情形</h3>
        <button type="button" class="secondary btn-sm" data-exp-preview-close>收合</button>
      </div>
      <p class="muted">認列基礎：${res.basis === "payable" ? "應付金額" : "使用金額"}
        ｜超額${res.carry_over ? "轉入次期" : "不轉入次期"}
        ${res.shortfall_action ? `｜期末未達：${escapeHtml(res.shortfall_action)}` : ""}</p>
      <div class="grid-scroll"><table class="grid-table">
        <thead><tr><th>承諾期</th><th class="num">承諾金額</th><th class="num">實際認列</th>
        <th class="num">達成率</th><th class="num">未達差額</th><th class="num">超額</th>
        <th class="num">轉入次期</th></tr></thead>
        <tbody>${rows}</tbody></table></div>
      <p class="muted">「尚未登錄」跟「達成率 0%」是兩回事——沒有任何一期實際費用進來時，這裡不會顯示 0%。</p>`;
  } catch (e) {
    box.innerHTML = `<p class="error">達成情形載入失敗：${escapeHtml(e.message)}</p>`;
  }
}

// 預覽畫面逐期修正：改完就存，並標記為人工調整（助理 0803 要求留痕）。
document.addEventListener("change", async (event) => {
  const el = event.target.closest("[data-sched-field]");
  if (!el) return;
  const id = el.getAttribute("data-sched-id");
  const field = el.getAttribute("data-sched-field");
  const value = el.type === "number" ? Number(el.value || 0) : el.value;
  try {
    await api(`/api/expense-schedules/${id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [field]: value }),
    });
    await loadExpensePreview(document.querySelector("#expense-preview-panel").dataset.sectionId);
  } catch (e) { window.alert(`儲存失敗：${e.message}`); }
});

// 新增費用區段
document.addEventListener("submit", async (event) => {
  const form = event.target.closest("[data-exp-section-form]");
  if (!form) return;
  event.preventDefault();
  const expenseId = document.querySelector("#expense-section-panel").dataset.expenseId;
  const v = (sel) => form.querySelector(sel)?.value || "";
  try {
    await api(`/api/expenses/${expenseId}/sections`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: v("[data-sec-mode]"),
        section_name: v("[data-sec-name]"),
        section_amount: Number(v("[data-sec-amount]") || 0),
        periods: Number(v("[data-sec-periods]") || 0),
        price_method: v("[data-sec-price]"),
        frequency: v("[data-sec-freq]"),
        first_amount: Number(v("[data-sec-first-amount]") || 0),
        first_month: v("[data-sec-first-month]"),
        first_due_date: v("[data-sec-first-due]"),
        period_start: v("[data-sec-period-start]"),
        commit_span_months: Number(v("[data-sec-span]") || 0),
        next_amount_rule: v("[data-sec-next-rule]"),
        growth_pct: Number(v("[data-sec-growth]") || 0),
        carry_over: f.querySelector("[data-sec-carry]")?.checked ? 1 : 0,
        achievement_basis: v("[data-sec-basis]"),
        shortfall_action: v("[data-sec-shortfall]"),
      }),
    });
    await loadExpenseSections(expenseId);
  } catch (e) { window.alert(`新增費用區段失敗：${e.message}`); }
});

// 費用主檔表單：有合約時廠商/統編/期間/總費用由合約帶入，總費用反灰不給改（助理 0803）
async function syncExpenseContractFields() {
  const form = document.querySelector("#expense-form");
  if (!form) return;
  const cid = form.elements.contract_id.value;
  const total = form.elements.total_amount;
  const dates = [form.elements.start_date, form.elements.end_date];
  if (!cid) {
    total.readOnly = false;
    total.classList.remove("readonly-field");
    for (const d of dates) { d.value = ""; d.disabled = true; }   // 無合約：期間停用、不得輸入
    return;
  }
  const k = (resourceCaches.contract || []).find((c) => String(c.id) === String(cid));
  if (!k) return;
  for (const d of dates) d.disabled = false;
  form.elements.start_date.value = k.start_date || "";
  form.elements.end_date.value = k.end_date || "";
  form.elements.vendor_name.value = k.vendor_name || "";
  form.elements.vendor_tax_id.value = k.vendor_tax_id || "";
  form.elements.total_amount.value = Number(k.amount || 0);
  total.readOnly = true;                       // 助理明講：有合約時唯讀反灰
  total.classList.add("readonly-field");
  if (!form.elements.expense_name.value.trim()) form.elements.expense_name.value = k.contract_name || "";
  if (!form.elements.owner.value) form.elements.owner.value = k.owner || "";
}

document.addEventListener("change", (event) => {
  if (event.target.closest(".expense-contract-picker")) syncExpenseContractFields();
  if (event.target.matches("#expense-form .case-picker")) {
    loadExpenseContractOptions();
    syncExpenseContractFields();
  }
});

function startExpenseEdit(id) {
  const form = document.querySelector("#expense-form");
  const item = expenseCache.find((x) => String(x.id) === String(id));
  if (!form || !item) return;
  setManualForm(form, true);
  form.elements.id.value = item.id;
  for (const f of ["expense_name", "vendor_name", "vendor_tax_id", "start_date", "end_date",
                   "total_amount", "signoff_ref", "signoff_none_reason", "owner", "note"]) {
    if (form.elements[f]) form.elements[f].value = item[f] ?? "";
  }
  form.elements.case_id.value = item.case_id || "";
  loadExpenseContractOptions();          // AC-10：合約下拉先依這筆的案件重新過濾，再帶入原本選的合約
  form.elements.contract_id.value = item.contract_id || "";
  const modes = String(item.modes || "").split(",");
  for (const m of EXPENSE_MODES) {
    if (form.elements[`mode_${m.key}`]) form.elements[`mode_${m.key}`].checked = modes.includes(m.key);
  }
  syncExpenseContractFields();
  form.querySelector('button[type="submit"]').textContent = "儲存";
  form.querySelector("[data-cancel]").hidden = false;
  form.scrollIntoView({ block: "nearest" });
}

document.querySelector("#expense-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const id = form.elements.id.value;
  const modes = EXPENSE_MODES.filter((m) => form.elements[`mode_${m.key}`]?.checked).map((m) => m.key);
  const body = {
    contract_id: form.elements.contract_id.value ? Number(form.elements.contract_id.value) : null,
    case_id: form.elements.case_id.value ? Number(form.elements.case_id.value) : null,
    expense_name: form.elements.expense_name.value,
    vendor_name: form.elements.vendor_name.value,
    vendor_tax_id: form.elements.vendor_tax_id.value,
    start_date: form.elements.start_date.value,
    end_date: form.elements.end_date.value,
    total_amount: Number(form.elements.total_amount.value || 0),
    modes: modes.join(","),
    signoff_ref: form.elements.signoff_ref.value,
    signoff_none_reason: form.elements.signoff_none_reason.value,
    owner: form.elements.owner.value,
    note: form.elements.note.value,
  };
  try {
    await api(id ? `/api/expenses/${id}` : "/api/expenses", {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    form.reset();
    form.elements.id.value = "";
    form.querySelector('button[type="submit"]').textContent = "新增";
    form.querySelector("[data-cancel]").hidden = true;
    setManualForm(form, false);
    await loadExpenses();
  } catch (e) { window.alert(`儲存失敗：${e.message}`); }
});

// 費用頁籤：新的三層費用排程 vs 既有的單筆費用（purchases）
document.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-exp-tab]");
  if (!tab) return;
  const which = tab.getAttribute("data-exp-tab");
  for (const b of document.querySelectorAll("[data-exp-tab]")) b.classList.toggle("active", b === tab);
  document.querySelector("[data-exp-panel='schedule']").hidden = which !== "schedule";
  for (const el of document.querySelectorAll("[data-legacy-only]")) el.hidden = which !== "legacy";
  for (const el of document.querySelectorAll("[data-exp-only]")) el.hidden = which !== "schedule";
});

// AC-10：選了案件之後，合約下拉只能選同一個 Case 底下的合約，避免掛錯合約
function loadExpenseContractOptions() {
  const sel = document.querySelector(".expense-contract-picker");
  if (!sel) return;
  const form = sel.closest("form");
  const caseId = form?.elements.case_id?.value || "";
  const cur = sel.value;
  const pool = (resourceCaches.contract || [])
    .filter((k) => !caseId || String(k.case_id || "") === String(caseId));
  sel.innerHTML = `<option value="">（無合約費用）</option>`
    + pool.map((k) =>
        `<option value="${k.id}">${escapeHtml(k.contract_code)}｜${escapeHtml(k.contract_name || "")}</option>`).join("");
  if (cur && pool.some((k) => String(k.id) === String(cur))) sel.value = cur;
}

// ── §8 付款排程面板：預計付款排程 vs 實際核銷，一頁看「還欠多少」 ──
// 合約列點「付款排程」→ 就地展開：選付款方式→產生排程→逐期可改→標已付→底下顯示 預計/已付/還欠。
async function loadPaymentSchedules(cid) {
  const box = document.querySelector("#contract-schedule-panel");
  if (!box) return;
  box.hidden = false;
  box.dataset.cid = cid;
  box.innerHTML = `<p class="muted">載入付款排程…</p>`;
  try {
    const res = (await api(`/api/contracts/${cid}/payment-schedules`)).data;
    const ct = (resourceCaches.contract || []).find((c) => String(c.id) === String(cid)) || {};
    box.innerHTML = renderSchedulePanel(cid, ct, res);
    syncSchedMethodUI(box);
    suggestPeriodCount(box, ct);  // 期數依合約起訖日先算好，使用者仍可改
  } catch (e) {
    box.innerHTML = `<p class="error">付款排程載入失敗：${escapeHtml(e.message)}</p>`;
  }
}

function syncSchedMethodUI(box) {
  const sel = box.querySelector("[data-sched-method]");
  if (!sel) return;
  const m = sel.value;
  box.querySelectorAll("[data-when]").forEach((el) => {
    el.style.display = el.getAttribute("data-when").split(" ").includes(m) ? "" : "none";
  });
}

// 合約起訖日跨幾個月（含頭尾）。2026-08 ~ 2027-07 → 12。算不出來回 0。
function monthSpan(startDate, endDate) {
  const p = (v) => {
    const m = /^(\d{4})-(\d{2})/.exec(String(v || "").trim());
    return m ? Number(m[1]) * 12 + Number(m[2]) - 1 : null;
  };
  const a = p(startDate), b = p(endDate);
  if (a === null || b === null || b < a) return 0;
  return b - a + 1;
}

// 週期月租接合約起訖日：期數不用自己數——月租 12 個月＝12 期、季付＝4 期、年繳＝1 期。
const FREQ_MONTHS = { monthly: 1, quarterly: 3, yearly: 12 };
function suggestPeriodCount(box, ct) {
  const span = monthSpan(ct.start_date, ct.end_date);
  if (!span) return;  // 沒填起訖日就不動使用者輸入的期數
  const freq = box.querySelector("[data-sched-freq]")?.value || "monthly";
  const countEl = box.querySelector("[data-sched-count]");
  if (countEl) countEl.value = Math.max(1, Math.ceil(span / (FREQ_MONTHS[freq] || 1)));
}

function renderSchedulePanel(cid, ct, res) {
  const editable = currentUser && (currentUser.allowed_actions || []).includes("edit");
  const canSettle = isReviewer(currentUser) || (currentUser && currentUser.role_code === "admin");
  const scheds = res.schedules || [];
  const sum = res.summary || { planned: 0, paid: 0, unpaid_planned: 0 };
  const locked = !!res.locked;
  const total = Number(ct.amount || 0);
  const schedTotal = scheds.reduce((s, x) => s + Number(x.planned_amount || 0), 0);
  const mismatch = scheds.length > 0 && Math.round(schedTotal) !== Math.round(total);

  const gen = editable ? `
    <div class="sched-gen">
      <label>付款方式 <select data-sched-method>
        <option value="installment">分期付款</option>
        <option value="periodic">週期（月租/季租）</option>
        <option value="milestone">里程碑 %</option>
        <option value="fixed">一次付清</option></select></label>
      <label data-when="installment periodic">期數 <input type="number" min="1" value="4" data-sched-count></label>
      <label data-when="periodic">週期 <select data-sched-freq>
        <option value="monthly">每月</option><option value="quarterly">每季</option><option value="yearly">每年</option></select></label>
      <label data-when="milestone">各期%（逗號分隔）<input type="text" placeholder="30,30,40" data-sched-pcts></label>
      <label>起始月 <input type="month" data-sched-start value="${escapeHtml(String(ct.start_date || "").slice(0, 7))}"></label>
      <label data-when="installment periodic milestone">零頭 <select data-sched-rem>
        <option value="last">放最後期</option><option value="first">放第一期</option></select></label>
      <button type="button" class="btn-sm" data-sched-gen="${cid}"${locked ? " disabled title='已有核銷回填，不能整個重產'" : ""}>產生排程</button>
    </div>` : "";

  const rows = scheds.length ? scheds.map((s) => {
    const paid = s.status === "paid";
    const amt = editable && !paid
      ? `<input class="sched-in num" type="number" value="${Number(s.planned_amount || 0)}" data-sched-edit="planned_amount" data-sid="${s.id}">`
      : `${money(s.planned_amount)} 元`;
    const due = editable && !paid
      ? `<input class="sched-in" type="month" value="${escapeHtml(s.due_date || "")}" data-sched-edit="due_date" data-sid="${s.id}">`
      : escapeHtml(valueOrDash(s.due_date));
    const label = editable && !paid
      ? `<input class="sched-in sched-label" type="text" value="${escapeHtml(s.label || "")}" data-sched-edit="label" data-sid="${s.id}">`
      : escapeHtml(s.label);
    const settle = (canSettle && !paid) ? `<button type="button" class="btn-sm" data-sched-settle="${s.id}">標已付</button>` : "";
    const del = (editable && !paid) ? `<button type="button" class="btn-sm danger" data-sched-del="${s.id}">刪</button>` : "";
    return `<tr class="${paid ? "sched-paid" : ""}"><td>${label}</td><td class="num">${amt}</td><td>${due}</td>`
      + `<td>${paid ? '<span class="chip done">已付</span>' : '<span class="chip todo">待付</span>'}</td>`
      + `<td class="sched-ops">${settle} ${del}</td></tr>`;
  }).join("") : `<tr><td colspan="5" class="muted">尚無排程——選付款方式按「產生排程」，或手動加列。</td></tr>`;

  const extra = editable ? `
    <div class="sched-extra">
      <button type="button" class="btn-sm" data-sched-add="${cid}">＋ 手動加一列</button>
      <span class="sched-split">把剩餘分 <input type="number" min="1" value="1" data-sched-split-n> 期
        <button type="button" class="btn-sm" data-sched-split="${cid}">分配</button></span>
    </div>` : "";

  const span = (ct.start_date || ct.end_date)
    ? `　合約期間 ${escapeHtml(valueOrDash(ct.start_date))} ~ ${escapeHtml(valueOrDash(ct.end_date))}` : "";
  return `<div class="sched-head"><strong>付款排程</strong>　<span class="muted">${escapeHtml(ct.contract_name || "")}　合約總額 ${money(total)} 元${span}</span>`
    + `<button type="button" class="btn-sm secondary sched-close" data-sched-close>收起</button></div>`
    + gen
    + `<table class="grid-table sched-table"><thead><tr><th>期別/名目</th><th class="num">預計金額</th><th>預計付款日</th><th>狀態</th><th>操作</th></tr></thead><tbody>${rows}</tbody></table>`
    + extra
    + `<div class="sched-check ${mismatch ? "bad" : "ok"}">各期加總 ${money(schedTotal)} 元 ${mismatch ? `≠ 合約總額 ${money(total)} 元 ⚠ 對不上` : "＝ 合約總額 ✓"}</div>`
    + `<div class="sched-summary">預計 <b>${money(sum.planned)}</b> 元　｜　已付 <b class="paid">${money(sum.paid)}</b> 元　｜　還欠 <b class="owe">${money(sum.unpaid_planned)}</b> 元</div>`;
}

// ── §10 費用調整面板：同一份合約中途改金額（機櫃增減、電費調價）留下歷史 ──
// 合約金額欄永遠是「現在多少錢」，這裡回答「什麼時候、為什麼、從多少調到多少、誰調的」。
// 調整紀錄不給刪（稽核）：填錯就再調一次回去，兩筆都留著才看得出經過。
async function loadContractAdjustments(cid) {
  const box = document.querySelector("#contract-adjust-panel");
  if (!box) return;
  box.hidden = false;
  box.dataset.cid = cid;
  box.innerHTML = `<p class="muted">載入費用調整紀錄…</p>`;
  try {
    const res = (await api(`/api/contracts/${cid}/adjustments`)).data;
    const ct = (resourceCaches.contract || []).find((c) => String(c.id) === String(cid)) || {};
    box.innerHTML = renderAdjustPanel(cid, ct, res);
  } catch (e) {
    box.innerHTML = `<p class="error">費用調整紀錄載入失敗：${escapeHtml(e.message)}</p>`;
  }
}

function renderAdjustPanel(cid, ct, res) {
  const editable = currentUser && (currentUser.allowed_actions || []).includes("edit");
  const items = res.items || [];
  const current = Number(ct.amount || 0);

  const rows = items.length ? items.map((a) => {
    const up = Number(a.delta) > 0;
    return `<tr><td>${escapeHtml(valueOrDash(a.effective_date))}</td>`
      + `<td>${escapeHtml(valueOrDash(a.reason))}</td>`
      + `<td class="num">${money(a.old_amount)} → ${money(a.new_amount)}</td>`
      + `<td class="num ${up ? "adj-up" : "adj-down"}">${up ? "＋" : "－"}${money(Math.abs(a.delta))}</td>`
      + `<td class="muted">${escapeHtml(valueOrDash(a.created_by))}</td></tr>`;
  }).join("") : `<tr><td colspan="5" class="muted">還沒有費用調整——合約金額就是原始金額。</td></tr>`;

  const form = editable ? `
    <div class="adj-form">
      <label>調整後金額 <input type="number" min="0" step="1" data-adj-amount placeholder="${current}"></label>
      <label>生效日 <input type="date" data-adj-date></label>
      <label class="adj-reason">原因 <input type="text" data-adj-reason placeholder="如：機櫃增加 2 台 / 電價調漲"></label>
      <button type="button" class="btn-sm" data-adj-add="${cid}">記一筆調整</button>
    </div>
    <p class="muted adj-hint">調整後付款排程可能跟新金額對不上——回付款排程面板看「各期加總」那行，用「把剩餘分 N 期」補差額。</p>` : "";

  const summary = res.count
    ? `<div class="sched-summary">最初 <b>${money(res.original_amount)}</b> 元　｜　調整 <b>${res.count}</b> 次`
      + `　｜　累計 <b class="${res.total_delta >= 0 ? "adj-up" : "adj-down"}">${res.total_delta >= 0 ? "＋" : "－"}${money(Math.abs(res.total_delta))}</b> 元`
      + `　｜　現值 <b>${money(current)}</b> 元</div>`
    : `<div class="sched-summary">目前金額 <b>${money(current)}</b> 元（未曾調整）</div>`;

  return `<div class="sched-head"><strong>費用調整紀錄</strong>　<span class="muted">${escapeHtml(ct.contract_name || "")}</span>`
    + `<button type="button" class="btn-sm secondary sched-close" data-adj-close>收起</button></div>`
    + `<table class="grid-table sched-table"><thead><tr><th>生效日</th><th>原因</th><th class="num">金額變動</th>`
    + `<th class="num">增減</th><th>記錄者</th></tr></thead><tbody>${rows}</tbody></table>`
    + form + summary;
}

// 合約列「調整紀錄」按鈕 → 展開面板
document.querySelector("#contracts")?.addEventListener("click", (event) => {
  const b = event.target.closest("[data-adjust]");
  if (b) loadContractAdjustments(b.getAttribute("data-adjust"));
});

document.querySelector("#contract-adjust-panel")?.addEventListener("click", async (event) => {
  const box = document.querySelector("#contract-adjust-panel");
  const t = event.target.closest("button");
  if (!t) return;
  if (t.hasAttribute("data-adj-close")) { box.hidden = true; return; }
  if (!t.hasAttribute("data-adj-add")) return;
  const cid = box.dataset.cid;
  const amountEl = box.querySelector("[data-adj-amount]");
  const amount = Number(amountEl.value);
  if (!amountEl.value.trim() || Number.isNaN(amount)) { window.alert("請先填調整後金額。"); return; }
  try {
    await api(`/api/contracts/${cid}/adjustments`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        new_amount: amount,
        effective_date: box.querySelector("[data-adj-date]").value || "",
        reason: box.querySelector("[data-adj-reason]").value || "",
      }),
    });
    await loadResource("contract");   // 合約金額已被調成新值，清單要跟著更新
    await loadContractAdjustments(cid);
    const sched = document.querySelector("#contract-schedule-panel");
    if (sched && !sched.hidden && sched.dataset.cid === cid) loadPaymentSchedules(cid);  // 重算「對不對得上」
  } catch (e) { window.alert(e.message); }
});

function readSchedGen(box) {
  const method = box.querySelector("[data-sched-method]").value;
  const body = { method, remainder_on: (box.querySelector("[data-sched-rem]")?.value) || "last",
                 start_month: box.querySelector("[data-sched-start]").value || "" };
  if (method === "milestone") {
    body.percents = (box.querySelector("[data-sched-pcts]").value || "")
      .split(",").map((x) => Number(x.trim())).filter((x) => !Number.isNaN(x));
  } else {
    body.count = Number(box.querySelector("[data-sched-count]")?.value || 1);
    if (method === "periodic") body.frequency = box.querySelector("[data-sched-freq]").value;
  }
  return body;
}

// 合約列「付款排程」按鈕 → 展開面板
document.querySelector("#contracts")?.addEventListener("click", (event) => {
  const b = event.target.closest("[data-schedule]");
  if (b) loadPaymentSchedules(b.getAttribute("data-schedule"));
});

// 面板內所有操作（產生/標已付/刪/加列/分剩餘/收起）
document.querySelector("#contract-schedule-panel")?.addEventListener("click", async (event) => {
  const box = document.querySelector("#contract-schedule-panel");
  const cid = box.dataset.cid;
  const t = event.target.closest("button");
  if (!t) return;
  try {
    if (t.hasAttribute("data-sched-close")) { box.hidden = true; return; }
    if (t.hasAttribute("data-sched-gen")) {
      await api(`/api/contracts/${cid}/payment-schedules/generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...readSchedGen(box), clear: true }) });
      return loadPaymentSchedules(cid);
    }
    if (t.hasAttribute("data-sched-settle")) {
      await api(`/api/settle-schedule/${t.getAttribute("data-sched-settle")}`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      return loadPaymentSchedules(cid);
    }
    if (t.hasAttribute("data-sched-del")) {
      await api(`/api/payment-schedules/${t.getAttribute("data-sched-del")}`, { method: "DELETE" });
      return loadPaymentSchedules(cid);
    }
    if (t.hasAttribute("data-sched-add")) {
      await api(`/api/payment-schedules`, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contract_id: Number(cid), label: "新項目", planned_amount: 0 }) });
      return loadPaymentSchedules(cid);
    }
    if (t.hasAttribute("data-sched-split")) {
      const res = (await api(`/api/contracts/${cid}/payment-schedules`)).data;
      const schedTotal = (res.schedules || []).reduce((s, x) => s + Number(x.planned_amount || 0), 0);
      const ct = (resourceCaches.contract || []).find((c) => String(c.id) === String(cid)) || {};
      const residual = Number(ct.amount || 0) - schedTotal;
      const n = Number(box.querySelector("[data-sched-split-n]").value || 1);
      if (residual <= 0) { window.alert("沒有剩餘可分配（各期加總已達或超過合約總額）。"); return; }
      await api(`/api/contracts/${cid}/payment-schedules/generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method: "installment", count: n, base_amount: residual, clear: false,
                               start_month: box.querySelector("[data-sched-start]").value || "" }) });
      return loadPaymentSchedules(cid);
    }
  } catch (e) { window.alert(e.message); }
});

// 面板內：付款方式切換（顯示對應欄位）、逐期就地改（金額/日期/名目）
document.querySelector("#contract-schedule-panel")?.addEventListener("change", async (event) => {
  const box = document.querySelector("#contract-schedule-panel");
  const ctOf = () => (resourceCaches.contract || []).find((c) => String(c.id) === String(box.dataset.cid)) || {};
  if (event.target.matches("[data-sched-method]")) { syncSchedMethodUI(box); suggestPeriodCount(box, ctOf()); return; }
  // 換週期(月/季/年)→ 期數跟著合約起訖重算：12 個月的約，月租 12 期、季付 4 期
  if (event.target.matches("[data-sched-freq]")) { suggestPeriodCount(box, ctOf()); return; }
  const edit = event.target.closest("[data-sched-edit]");
  if (edit) {
    const field = edit.getAttribute("data-sched-edit");
    let val = edit.value;
    if (field === "planned_amount") val = Number(val);
    try {
      await api(`/api/payment-schedules/${edit.getAttribute("data-sid")}`, {
        method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ [field]: val }) });
      loadPaymentSchedules(box.dataset.cid);  // 重載→更新加總檢查與還欠
    } catch (e) { window.alert(e.message); }
  }
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
    const roles = extra.getAttribute("data-roles");
    const roleAllowed = !roles || (currentUser && roles.split(/\s+/).includes(currentUser.role_code));
    extra.hidden = extra.dataset.moduleParent !== targetId || !roleAllowed;
  }
  lastPanelId = targetId;
  // 進度總表隨助理 2026-08-03 回饋搬到「專案」模組底下，切過去才載入（它要打好幾支 API）
  if (targetId === "projects") loadPortfolio();
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
  return (card.dataset.roles || "cio manager_assistant handler group_leader department_head").split(/\s+/).filter(Boolean);
}

function applyRoleVisibility(user) {
  const allowedModules = new Set(user.allowed_modules || []);
  applySearchScopeByRole(user);  // 搜尋範圍也依角色收斂（CIO 只有決策總覽 → 停用搜尋）
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
  // 主管儀表板底下的子頁籤：「系統工具」（示範資料/AI測試資料/舊資料補號）只給主管/助理，
  // CIO 能看主管儀表板但看不到這個維運用子頁籤。
  let dashToolsTabHidden = false;
  for (const tab of dashTabs) {
    const roles = tab.getAttribute("data-roles");
    if (!roles) continue;
    const allowed = roles.split(/\s+/).includes(user.role_code);
    tab.hidden = !allowed;
    if (tab.dataset.dashTab === "tools" && !allowed) dashToolsTabHidden = true;
  }
  if (dashToolsTabHidden && document.querySelector('[data-dash-tab="tools"]')?.classList.contains("active")) {
    activateDashTab("overview");
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
  // 四格計數（案件/合約/付款/文件）已隨主管儀表板改版移除：那是「有多少資料」不是「要處理什麼」。
  // 各模組的筆數改在左側選單各自顯示。
  if (metrics) {
    metrics.innerHTML = [
      metric("案件", data.counts.cases),
      metric("合約", data.counts.contracts),
      metric("付款", data.counts.payments),
      metric("文件", data.counts.documents),
    ].join("");
  }
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
  const statusClass = item.status === "approved" || item.status === "in_progress" ? "ok"
    : item.status === "pending_review" || item.status === "returned" || item.status === "paused" ? "warn"
    : item.status === "rejected" || item.status === "cancelled" ? "danger"
    : ["disabled", "merged", "closed"].includes(item.status) ? "neutral" : "";
  // 「案號」與「案件編號」原本是兩欄，但核准後兩者是同一個值（store 把 年+流水 同時寫進
  // case_code），核准前又變成一欄「草稿」一欄「—」，兩欄都沒資訊。使用者 2026-08-28
  // 拍板合併成一欄：核准後給案號、核准前給狀態；匯入帶進來的原始編號跟系統案號不同時
  // 附在下面小字，才追溯得回原始 Excel。
  const n = caseNumber(item);
  const rawCode = String(item.case_code || "");
  const keepsOwnCode = rawCode && rawCode !== n && !isTempCaseCode(rawCode);
  const num = (n
    ? `<span class="badge" title="案號（年度＋流水號）＝這個案的身分證，各階段共用">${escapeHtml(n)}</span>`
    // 未核准時留「—」而不是寫狀態：合併後右邊本來就有獨立的「狀態」欄，
    // 兩欄都寫「草稿」等於同一個字佔兩次版面（合併時實測才看出來）。
    : `<span class="muted" title="尚未核准，核准後才配正式案號（目前狀態見右邊狀態欄）">—</span>`)
    + (keepsOwnCode
      ? `<div class="review-note" title="原始編號（匯入帶進來的，不是系統配的）">${escapeHtml(rawCode)}</div>`
      : "")
    + sourceTag(item);
  // 退件原因/駁回理由/併到哪一件：直接顯示在狀態底下，不用點進去才知道為什麼
  const mergedInto = item.merged_into_case_id
    ? (caseCache || []).find((c) => String(c.id) === String(item.merged_into_case_id))
    : null;
  const noteBits = [];
  if (mergedInto) noteBits.push(`併入 ${mergedInto.case_code}`);
  // 只在還停在該狀態時顯示；補件後重新送出就不再掛著舊退件原因（歷史仍在稽核軌跡查得到）
  if (item.review_note && ["returned", "rejected", "merged"].includes(item.status)) noteBits.push(item.review_note);
  // 暫停/取消原因，以及重開紀錄（需求書 §4 要求記錄重開人與時間）
  if (item.status_note && ["paused", "cancelled"].includes(item.status)) noteBits.push(item.status_note);
  if (item.reopened_by && item.status === "in_progress") {
    noteBits.push(`${item.reopened_at ? item.reopened_at.slice(0, 10) + " " : ""}由 ${item.reopened_by} 重開：${item.reopen_reason || ""}`);
  }
  const note = noteBits.length
    ? `<div class="review-note" title="${escapeHtml(noteBits.join("｜"))}">${escapeHtml(noteBits.join("｜"))}</div>` : "";
  return `<tr data-case-id="${item.id}"${caseSelection.has(String(item.id)) ? ' class="picked"' : ""}>
    <td class="col-pick"><input type="checkbox" data-case-pick="${item.id}"${caseSelection.has(String(item.id)) ? " checked" : ""} aria-label="選取 ${escapeHtml(item.case_code)}" /></td>
    <td class="col-narrow">${num}</td>
    <td><strong>${escapeHtml(item.title)}</strong></td>
    <td class="col-narrow muted">${escapeHtml(item.owner || "未指派")}</td>
    <td class="col-narrow"><span class="badge ${statusClass}">${escapeHtml(STATUS_LABELS[item.status] || item.status)}</span>${note}</td>
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
  // 勾選狀態只保留還在畫面上的案件（重載後被過濾掉的就不該還算在選取裡）
  const visible = new Set(caseCache.map((c) => String(c.id)));
  caseSelection = new Set([...caseSelection].filter((id) => visible.has(id)));
  cases.innerHTML = caseCache.length
    ? `${renderBatchBar()}<div class="grid-scroll"><table class="grid-table">
        <thead><tr>
          <th class="col-pick"><input type="checkbox" id="case-pick-all" title="全選／取消全選" aria-label="全選案件" /></th>
          <th class="col-narrow">案號</th><th>案件名稱</th><th class="col-narrow">負責人</th><th class="col-narrow">狀態</th><th class="col-actions">操作</th></tr></thead>
        <tbody>${caseCache.map(renderCaseRow).join("")}</tbody>
      </table></div>`
    : `<p class="muted">目前沒有案件資料。</p>`;
  syncPickAll();
}

// ── 批次處理：第一次上線有幾十筆匯入資料要一起送審，一筆一筆按不現實 ──
let caseSelection = new Set();

// 哪些批次動作對「目前選到的這些案件」有意義：只列出至少有一筆走得過去的動作，
// 免得按下去整批都失敗還要看錯誤訊息才知道。
const BATCH_ACTION_META = [
  { act: "submit", label: "送出複核", from: ["draft", "reviewing", "returned"] },
  { act: "approve", label: "核准", from: ["pending_review"], reviewer: true },
  { act: "return", label: "退回補件", from: ["pending_review", "draft", "returned"], reviewer: true, ask: "退件原因（所有選取的案件都會用這個原因）：" },
  { act: "reject", label: "駁回", from: ["pending_review", "draft", "returned"], reviewer: true, ask: "駁回原因（所有選取的案件都會用這個原因）：" },
  { act: "start", label: "開始執行", from: ["approved"] },
  { act: "close", label: "結案", from: ["in_progress"] },
];

function renderBatchBar() {
  const n = caseSelection.size;
  if (!n) {
    return `<p class="batch-hint muted">勾選左邊的框可以一次處理多筆（例如剛匯入的一批一起送審）。</p>`;
  }
  const picked = caseCache.filter((c) => caseSelection.has(String(c.id)));
  const btns = BATCH_ACTION_META
    .filter((a) => (!a.reviewer || isReviewer(currentUser)) && picked.some((c) => a.from.includes(c.status)))
    .map((a) => {
      const hit = picked.filter((c) => a.from.includes(c.status)).length;
      return `<button type="button" class="btn-sm${a.act === "reject" ? " danger" : ""}" data-batch-act="${a.act}">`
        + `${a.label}<span class="batch-n">${hit}</span></button>`;
    }).join(" ");
  return `<div class="batch-bar">
    <strong>已選 ${n} 筆</strong>
    ${btns || '<span class="muted">選取的案件目前沒有可一起執行的動作。</span>'}
    <button type="button" class="secondary btn-sm" data-batch-clear>清除選取</button>
  </div>`;
}

function syncPickAll() {
  const all = document.querySelector("#case-pick-all");
  if (!all) return;
  const total = caseCache.length;
  const n = caseSelection.size;
  all.checked = n > 0 && n === total;
  all.indeterminate = n > 0 && n < total;   // 部分選取時顯示成「半選」，不要假裝全選
}

cases.addEventListener("change", (event) => {
  const all = event.target.closest("#case-pick-all");
  if (all) {
    caseSelection = all.checked ? new Set(caseCache.map((c) => String(c.id))) : new Set();
    loadCases();
    return;
  }
  const box = event.target.closest("[data-case-pick]");
  if (!box) return;
  const id = box.getAttribute("data-case-pick");
  if (box.checked) caseSelection.add(id); else caseSelection.delete(id);
  // 只重畫批次列與全選狀態，不重載整表（重載會把勾選的視覺閃掉）
  const bar = cases.querySelector(".batch-bar, .batch-hint");
  if (bar) bar.outerHTML = renderBatchBar();
  syncPickAll();
});

cases.addEventListener("click", async (event) => {
  if (event.target.closest("[data-batch-clear]")) {
    caseSelection = new Set();
    loadCases();
    return;
  }
  const btn = event.target.closest("[data-batch-act]");
  if (!btn) return;
  const act = btn.getAttribute("data-batch-act");
  const meta = BATCH_ACTION_META.find((a) => a.act === act);
  const ids = caseCache.filter((c) => caseSelection.has(String(c.id)) && meta.from.includes(c.status))
                       .map((c) => c.id);
  if (!ids.length) return;
  let reason = "";
  if (meta.ask) {
    const input = window.prompt(`${meta.label}（${ids.length} 筆）：${meta.ask}`, "");
    if (input === null) return;
    if (!input.trim()) { window.alert(`請填${meta.label}原因。`); return; }
    reason = input.trim();
  } else if (!window.confirm(`確定將 ${ids.length} 筆案件「${meta.label}」？`)) {
    return;
  }
  btn.disabled = true;
  const label = btn.innerHTML;
  btn.innerHTML = "處理中…";
  try {
    const res = (await api(`/api/case-batch/${act}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids, reason }) })).data || {};
    caseSelection = new Set();
    await refresh();
    if (res.failed_count) {
      // 逐筆回報失敗原因：最常見的是「不能核准自己建立的案件」，要讓人看得懂而不是只說失敗
      const lines = res.failed.slice(0, 8).map((f) => {
        const c = caseCache.find((x) => x.id === f.id);
        return `・${c ? c.case_code : "#" + f.id}：${f.reason}`;
      });
      const more = res.failed_count > 8 ? `\n（還有 ${res.failed_count - 8} 筆）` : "";
      window.alert(`${meta.label}完成 ${res.done_count} 筆，${res.failed_count} 筆沒過：\n${lines.join("\n")}${more}`);
    } else {
      window.alert(`${meta.label}完成 ${res.done_count} 筆。`);
    }
  } catch (error) {
    btn.disabled = false;
    btn.innerHTML = label;
    window.alert(error.message);
  }
});

// 作業年度：新案件「所屬年度」的預設；顯示＋可改
async function loadWorkingYear() {
  try {
    const y = (await api("/api/working-year")).data.working_year || "";
    setText("#working-year-label", y);
    const fy = document.querySelector('#case-form [name="fiscal_year"]');  // 已從表單移除，留著保護舊版
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

// 來源合約下拉（續約/增購/整併要指哪一份舊約）。編輯中的那份合約要從清單拿掉——
// 自己不能是自己的來源，後端也會擋，但這裡先不給選，免得使用者白填一次。
async function loadParentContractOptions() {
  const pickers = document.querySelectorAll(".parent-contract-picker");
  if (!pickers.length) return;
  let list = [];
  try { list = (await api("/api/contracts")).data || []; } catch (_e) { return; }
  for (const sel of pickers) {
    const form = sel.closest("form");
    const editingId = form && form.elements.id ? form.elements.id.value : "";
    const cur = sel.value;
    sel.innerHTML = `<option value="">（無來源合約）</option>`
      + list.filter((k) => String(k.id) !== String(editingId))
            .map((k) => `<option value="${k.id}">${escapeHtml(k.contract_code)}｜${escapeHtml(k.contract_name || "")}</option>`).join("");
    if (cur) sel.value = cur;
  }
}

// 增購／附屬只能掛在「同一個案件底下的既有合約」上（助理 0803）：
// 同案 0 份合約 → 這個選項直接停用（提示為什麼）；1 份 → 自動帶入且鎖住；2 份以上 → 要選。
// 判斷邏輯在後端（/api/cases/{id}/addon-options），前端只負責照 mode 呈現。
async function refreshAddonGate() {
  const form = resourceForms.contract;
  if (!form) return;
  const nature = form.querySelector(".contract-nature-picker");
  const parent = form.querySelector(".parent-contract-picker");
  const caseId = form.elements.case_id ? form.elements.case_id.value : "";
  const addonOpt = nature ? [...nature.options].find((o) => o.value === "addon") : null;
  if (!nature || !parent || !addonOpt) return;
  const hint = form.querySelector("[data-addon-hint]");
  if (!caseId) {                       // 還沒選案件：無從判斷，先停用增購
    addonOpt.disabled = true;
    if (hint) hint.textContent = "選好關聯案件後，才知道能不能建增購／附屬合約。";
    return;
  }
  let info;
  try { info = (await api(`/api/cases/${caseId}/addon-options`)).data; } catch (_e) { return; }
  addonOpt.disabled = info.mode === "disabled";
  if (addonOpt.disabled && nature.value === "addon") nature.value = "";
  if (hint) hint.textContent = info.hint;
  const isAddon = nature.value === "addon";
  // 只有一份既有合約時系統自動帶入並鎖住，避免有人手動改掛到別案的合約
  if (isAddon && info.mode === "auto" && info.contracts.length === 1) {
    parent.value = String(info.contracts[0].id);
    parent.disabled = true;
  } else {
    parent.disabled = false;
  }
  parent.required = isAddon && info.mode === "choose";
}

async function loadPurchaseOptions() {
  const pickers = document.querySelectorAll(".purchase-picker");
  if (!pickers.length) return;
  let list = [];
  try { list = (await api("/api/purchases")).data || []; } catch (_e) { return; }
  const opts = `<option value="">（不關聯費用）</option>` +
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

// 廠商清單（助理第三次回饋 §6）：換了案件就重抓這個 Case 已經填過的廠商，灌進共用 datalist——
// 只是「建議選項」，使用者仍可自己打新的，不強制覆寫任何欄位。
document.addEventListener("change", async (event) => {
  const picker = event.target.closest(".case-picker");
  if (!picker) return;
  const list = document.querySelector("#case-vendor-options");
  if (!list) return;
  if (!picker.value) { list.innerHTML = ""; return; }
  try {
    const vendors = (await api(`/api/cases/${picker.value}/vendors`)).data || [];
    list.innerHTML = vendors.map((v) => `<option value="${escapeHtml(v)}"></option>`).join("");
  } catch (_e) { /* 廠商建議清單抓不到不影響表單本身，安靜失敗即可 */ }
});

// 換案件或改合約性質 → 重新判斷「增購／附屬」能不能選、原合約要不要自動帶
document.addEventListener("change", (event) => {
  if (!event.target.closest("#contract-form")) return;
  if (event.target.matches(".case-picker, .contract-nature-picker")) refreshAddonGate();
});

// 追溯鏈：從案件一路看 簽呈 ▸ 請購 ▸ 合約 ▸ 付款（用 case_360 的聚合）。
// 編輯經理：每一筆都可點「編輯」直接開對應模組表單；缺的階段可點「＋新增」帶入本案／案名，
// 一段一段各自獨立送出（沿用各模組既有 PATCH/POST，不做整批 atomic 交易）。
let traceCaseId = null;
let traceLatestContractId = null;

// §8 向下鑽取：案件層的「花多少、欠多少」再拆到每一份合約——主管看得出是「哪一份」還欠，
// 再點「付款明細」就地展開該合約每一期（唯讀；要改排程仍走合約模組的排程面板，權限一致）。
function traceContractMoney(k) {
  const planned = Number(k.planned_total || 0);
  const paid = Number(k.paid_total || 0);
  const owe = Number(k.unpaid_planned || 0);
  const money3 = planned > 0
    ? `<span class="trace-ct-money">預計 ${money(planned)}｜已付 <b class="paid">${money(paid)}</b>｜還欠 <b class="owe">${money(owe)}</b> 元</span>`
    : `<span class="trace-ct-money muted">尚未排付款排程</span>`;
  return `${money3} <button type="button" class="link-btn" data-trace-sched="${k.id}">付款明細</button>`
    + `<div class="trace-sched" data-sched-box="${k.id}" hidden></div>`;
}

function renderTraceSchedule(res) {
  const scheds = res.schedules || [];
  const sum = res.summary || { planned: 0, paid: 0, unpaid_planned: 0 };
  if (!scheds.length) {
    return `<p class="muted">這份合約還沒有付款排程——到「合約」模組點該列的「付款排程」建立。</p>`;
  }
  const rows = scheds.map((s) => {
    const paid = s.status === "paid";
    return `<tr class="${paid ? "sched-paid" : ""}"><td>${escapeHtml(s.label || "")}</td>`
      + `<td class="num">${money(s.planned_amount)} 元</td>`
      + `<td>${escapeHtml(valueOrDash(s.due_date))}</td>`
      + `<td>${paid ? '<span class="chip done">已付</span>' : '<span class="chip todo">待付</span>'}</td></tr>`;
  }).join("");
  return `<table class="grid-table sched-table"><thead><tr><th>期別/名目</th><th class="num">預計金額</th>`
    + `<th>預計付款日</th><th>狀態</th></tr></thead><tbody>${rows}</tbody></table>`
    + `<div class="sched-summary">預計 <b>${money(sum.planned)}</b> 元　｜　已付 <b class="paid">${money(sum.paid)}</b> 元`
    + `　｜　還欠 <b class="owe">${money(sum.unpaid_planned)}</b> 元</div>`;
}
// focusCard：從進度列的某一站點進來時，把該模組的卡片捲到眼前並標記出來，
// 不然使用者點了「預算」還要自己在六張卡片裡找預算在哪。
async function loadCaseTrace(caseId, focusCard = "") {
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
        <div class="case-money">
          <div class="cm-item"><span class="cm-k">合約總額</span><span class="cm-v">${money(t.contract_amount)} 元</span></div>
          <div class="cm-item"><span class="cm-k">預計付款</span><span class="cm-v">${money(t.planned_total)} 元</span></div>
          <div class="cm-item"><span class="cm-k">已付</span><span class="cm-v paid">${money(t.paid_total)} 元</span></div>
          <div class="cm-item cm-owe"><span class="cm-k">還欠</span><span class="cm-v owe">${money(t.unpaid_planned)} 元</span></div>
        </div>
        <div class="trace-chain">
          ${chip("預算", n(d.budgets), t.budget_amount)}<span class="trace-arrow">▸</span>
          ${chip("專案", n(d.projects), null)}<span class="trace-arrow">▸</span>
          ${chip("簽呈", n(d.signoffs), t.signoff_amount)}<span class="trace-arrow">▸</span>
          ${chip("費用", n(d.purchases), t.purchase_amount)}<span class="trace-arrow">▸</span>
          ${chip("合約", n(d.contracts), t.contract_amount)}<span class="trace-arrow">▸</span>
          ${chip("付款", n(d.payments), t.payment_amount)}
        </div>
        <div class="trace-lists">
          <div class="trace-card" data-trace-card="budget"><h4>預算 <span class="trace-card-count">${n(d.budgets)}</span></h4><ul class="note-list">${listOf(d.budgets, "budget", (b) => `<strong>${escapeHtml(b.budget_code)}</strong> ${escapeHtml(valueOrDash(b.unit_name))}｜${money(b.amount)} 元`, "無關聯預算——在「預算」模組把它關聯到本案件")}</ul></div>
          <div class="trace-card" data-trace-card="project"><h4>專案 <span class="trace-card-count">${n(d.projects)}</span></h4><ul class="note-list">${listOf(d.projects, "project", (p) => `<strong>${escapeHtml(p.project_code)}</strong> ${escapeHtml(p.project_name || "")}｜${escapeHtml(labelStatus(p.status))}`, "無關聯專案")}</ul></div>
          <div class="trace-card" data-trace-card="signoff"><h4>簽呈 <span class="trace-card-count">${n(d.signoffs)}</span></h4><ul class="note-list">${listOf(d.signoffs, "signoff", (s) => `<strong>${escapeHtml(s.signoff_code)}</strong> ${escapeHtml(s.subject || "")}｜${money(s.amount)} 元｜${escapeHtml(labelStatus(s.status))}${s.attachment_ref ? "｜" + attachmentLink(s.attachment_ref) : ""}`, "無關聯簽呈——在「簽呈」模組把它關聯到本案件")}</ul></div>
          <div class="trace-card" data-trace-card="purchase"><h4>費用 <span class="trace-card-count">${n(d.purchases)}</span></h4><ul class="note-list">${listOf(d.purchases, "purchase", (p) => `<strong>${escapeHtml(p.purchase_code)}</strong> ${escapeHtml(p.item_name || "")}｜廠商 ${escapeHtml(valueOrDash(p.vendor_name))}｜${money(p.amount)} 元${sourceTag("簽呈", p.signoff_id, d.signoffs, "signoff_code")}`, "無關聯費用")}</ul></div>
          <div class="trace-card" data-trace-card="contract"><h4>合約 <span class="trace-card-count">${n(d.contracts)}</span></h4><ul class="note-list">${listOf(d.contracts, "contract", (k) => `<strong>${escapeHtml(k.contract_code)}</strong>${relationTag(k)}${contractSystemLink(k.contract_code)} ${escapeHtml(k.contract_name || "")}｜廠商 ${escapeHtml(valueOrDash(k.vendor_name))}｜${money(k.amount)} 元${sourceTag("費用", k.purchase_id, d.purchases, "purchase_code")}`
            + traceContractMoney(k), "無關聯合約")}</ul></div>
          <div class="trace-card" data-trace-card="payment"><h4>付款 <span class="trace-card-count">${n(d.payments)}</span></h4><ul class="note-list">${listOf(d.payments, "payment", (p) => `${escapeHtml(p.payment_month)}｜${money(p.payment_amount)} 元｜${escapeHtml(labelStatus(p.status))}`, traceLatestContractId ? "無付款紀錄" : "無付款紀錄（需先建立合約才能新增付款）")}</ul></div>
        </div>
      </div>`;
    const target = focusCard ? box.querySelector(`[data-trace-card="${focusCard}"]`) : null;
    if (target) {
      target.classList.add("trace-card-focus");
      target.scrollIntoView({ block: "center", behavior: "smooth" });
    } else {
      box.scrollIntoView({ block: "nearest" });
    }
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
  // 向下鑽取：合約列「付款明細」→ 就地展開/收起該合約的每期排程（唯讀，不離開 Case 360）
  const schedBtn = event.target.closest("[data-trace-sched]");
  if (schedBtn) {
    const cid = schedBtn.getAttribute("data-trace-sched");
    const panel = document.querySelector(`#case-trace [data-sched-box="${cid}"]`);
    if (!panel) return;
    if (!panel.hidden) { panel.hidden = true; schedBtn.textContent = "付款明細"; return; }
    panel.hidden = false;
    schedBtn.textContent = "收起明細";
    panel.innerHTML = `<p class="muted">載入付款明細…</p>`;
    try {
      panel.innerHTML = renderTraceSchedule((await api(`/api/contracts/${cid}/payment-schedules`)).data);
    } catch (e) {
      panel.innerHTML = `<p class="error">付款明細載入失敗：${escapeHtml(e.message)}</p>`;
    }
    return;
  }
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
      // 系統編號是跟著案件走的（同一案各模組共用案件的年+流水），所以單看某個模組
      // 一定會跳號。不講的話使用者會以為資料被刪了——這是設計，不是遺失。
      const hint = c.label === "系統編號"
        ? "系統編號跟著案件走：同一個案件的預算/專案/合約共用同一組年度＋流水號。單看這個模組會跳號，代表那些案件沒有這一段，不是資料遺失。｜點欄名可排序"
        : "點欄名可排序";
      return `<th class="sortable${c.cls ? " " + c.cls : ""}" data-sort-type="${type}" data-col-index="${i}" title="${escapeHtml(hint)}">${c.label}${arrow}</th>`;
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
  if (!type) return;  // 沒標型別的表頭不歸這裡管
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
  // readOnly 目前沒有模組在用（預算曾短暫設過，見 index.html 的回退說明）。
  // 保留這個開關是因為「某模組改成唯讀」是客戶反覆提過的需求，留著比每次重寫便宜。
  if (config.readOnly) return `<span class="muted">唯讀</span>`;
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

// 進度條（只出條，不帶文字）：預計/實際數字改各自獨立成欄，這裡只負責視覺化實際完成度。
// 顏色：實際≥預計綠、落後<20%黃、落後≥20%紅。
function progressBarOnly(planned, actual) {
  const p = Number(planned || 0);
  const a = Number(actual || 0);
  const tone = a >= p ? "ok" : (p - a) >= 20 ? "danger" : "warn";
  return `<span class="progress-bar"><i class="progress-fill ${tone}" style="width:${Math.min(100, Math.max(0, a))}%"></i></span>`;
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
const portfolioState = { g: 0, s: "ov", f: null };  // f＝六格統計列選中的 tone（null＝全部）
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

  // 燈號一律走統一的 ragOf()，確保專案清單、進度總表、工作項、線性圖顏色語意一致；
  // 但落後幅度只有這裡算得出來，所以文字標籤仍保留在本函式。
  let tone = ragOf(p);
  if (noBasis) tone = "todo";        // 沒有任何比對基準時當「還沒排」，不誤報成正常或落後
  // 期限還沒到但進度落後：最多升到橘燈「要注意」。純落後不該變紅燈——紅燈「已過期」
  // 的語意是「過了結束日」，只由 ragOf() 依結束日判定（真過期時它早已回 over，
  // 而 over !== "live"，不會進到這行）。gap>18 直接染紅是 v0.19.0 引入的自錯，畫面
  // 會把「8 月才到期、只是落後」的專案標成已過期＝說謊。
  else if (tone === "live" && gap > 2) tone = "soon";

  let label;
  if (actual >= 100) label = "完成";
  else if (noBasis) label = "未排程";
  else if (gap <= 2) label = actual > expected + 8 ? "超前" : "準時";
  else label = "落後 " + Math.round(gap) + "%";
  return { actual, planned, expected, gap, tone, label, hasDates, days, noBasis };
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

// 六格狀態統計：互斥且加總＝全部。tone 直接沿用 pfStatus 的五態（done/todo/live/
// soon/over），所以「怎麼分格」和「每列燈號什麼顏色」永遠是同一套判斷，不會兩邊對不上。
// 不設「落後」格：落後已經是變橘（soon）的原因之一，另立一格會跟 soon 重複計數、
// 加總對不起來。橘燈這裡叫「要注意」＝快到期或落後；紅燈「已過期」純看結束日（見 B3）。
const PF_BUCKETS = [
  { tone: "done", label: "已完成" },
  { tone: "todo", label: "未開始" },
  { tone: "live", label: "如期執行" },
  { tone: "soon", label: "有延遲風險" },
  { tone: "over", label: "已延遲" },
];

function pfOverview(group) {
  const ranked = group.projects
    .map((p) => ({ p, c: pfStatus(p) }))
    .sort((a, b) => pfSortKey(b.c) - pfSortKey(a.c));

  const counts = {};
  for (const { c } of ranked) counts[c.tone] = (counts[c.tone] || 0) + 1;
  const active = portfolioState.f;  // null＝全部；否則是某個 tone
  const stat = (tone, label, n) =>
    `<button type="button" class="pf-stat${tone ? " pf-stat-" + tone : " pf-stat-all"}${active === tone ? " active" : ""}" data-pf-filter="${tone || ""}"${!tone && n === 0 ? " disabled" : ""}>`
    + `${tone ? `<span class="pf-dot ${tone}"></span>` : ""}${label} <b>${n}</b></button>`;
  const stats = `<div class="pf-stats" role="group" aria-label="依狀態篩選">`
    + stat(null, "全部", ranked.length)
    + PF_BUCKETS.map((b) => stat(b.tone, b.label, counts[b.tone] || 0)).join("")
    + `</div>`;

  const shown = active ? ranked.filter(({ c }) => c.tone === active) : ranked;
  const rows = shown.length
    ? shown.map(({ p, c }) => `
      <div class="pf-row" data-pf-proj="${p.id}" title="點此看單一專案">
        <span class="pf-row-name"><span class="pf-dot ${c.tone}"></span><span class="pf-name-col"><span class="pf-name-txt">${escapeHtml(p.project_name)}</span>${pfDateLine(p, c)}</span></span>
        ${pfBar(p, c)}
        <span class="pf-row-tag"><span class="badge ${c.tone}">${escapeHtml(c.label)}</span></span>
      </div>`).join("")
    : `<p class="muted pf-empty">這個狀態目前沒有專案。<button type="button" class="linklike" data-pf-filter="">看全部</button></p>`;

  const legend = `<div class="pf-legend">
    <span><span class="pf-lg-fill"></span>填色＝實際完成度</span>
    <span><span class="pf-lg-today"></span>紅線▼＝今天在時間軸上的位置（填色在紅線左邊＝落後）</span>
    <span>條的左端＝開始日、右端＝結束日（名稱下方標出）</span>
  </div>`;
  const headText = active
    ? `${escapeHtml(group.name)}　篩選：${escapeHtml((PF_BUCKETS.find((b) => b.tone === active) || {}).label || "")}（${shown.length} / ${ranked.length} 個）`
    : `${escapeHtml(group.name)}　全部專案（共 ${ranked.length} 個）`;
  return `<div class="pf-card"><div class="muted pf-card-head">${headText}</div>${stats}${legend}${rows}</div>`;
}

function pfDetail(p) {
  const c = pfStatus(p);
  // 「剩餘」原本只拿結束日跟今天比，沒看完成度，所以 100% 做完的專案照樣被標紅
  // 「逾期 N 天」，跟旁邊綠色的「完成」自相矛盾。做完就顯示已完成，不再倒數。
  const isDone = Number(p.progress || 0) >= 100;
  const overdue = !isDone && c.hasDates && c.days < 0;
  const remainText = isDone
    ? "已完成"
    : (c.hasDates ? (c.days >= 0 ? c.days + " 天" : "逾期 " + (-c.days) + " 天") : "—");
  const metas = [
    ["負責人", valueOrDash(p.owner)],
    ["開始", valueOrDash(p.start_date)],
    ["結束", valueOrDash(p.end_date)],
    ["剩餘", remainText],
  ];
  const metaHtml = metas.map(([k, v]) =>
    `<div class="pf-meta"><span class="pf-meta-k">${k}</span><span class="pf-meta-v${k === "剩餘" && overdue ? " pf-danger" : ""}">${escapeHtml(v)}</span></div>`).join("");
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

const canEditPortfolio = () => currentUser && (currentUser.allowed_actions || []).includes("edit");

let pfItemsCache = [];       // 目前展開的專案的工作項；子項目面板要靠它顯示父工作項的名稱與數字
async function loadProjectItems(projectId) {
  const box = document.querySelector("#pf-items");
  if (!box) return;
  try {
    const items = (await api(`/api/projects/${projectId}/items`)).data || [];
    pfItemsCache = items;
    box.innerHTML = renderItemsSection(projectId, items);
  } catch (error) {
    box.innerHTML = `<p class="muted">工作項載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

// 子項目改動後重載工作項表：完成度／燈號是後端算的，要重抓才看得到新數字
async function reloadPfItems() {
  const pid = document.querySelector("#pf-items")?.getAttribute("data-project-id");
  if (pid) await loadProjectItems(pid);
}

// 工作項表格：開始日/結束日拆兩欄才能各自排序；預設依「結束日離今天的遠近」排，越急迫的越前面
// （跟處理優先矩陣「橫軸=急迫度」同一個邏輯，不是單純日期由小到大)。
// 助理文件的 WBS 欄位：人只填 子項目總數／完成數，進度%與燈號由系統算（都不給手改）。
const PF_ITEM_COLUMNS = [
  { label: "標號", key: "seq", cls: "num w-seq" },
  { label: "工作主項目", key: "item_name", cls: "w-name" },
  { label: "負責人", key: "owner", cls: "w-owner" },
  { label: "開始日", key: "start_date", cls: "num w-date" },
  { label: "結束日", key: "end_date", cls: "num w-date" },
  { label: "執行進度", key: "exec_status", cls: "w-status" },
  { label: "子項總數", key: "sub_total", cls: "num w-seq" },
  { label: "已完成", key: "sub_done", cls: "num w-seq" },
  { label: "完成度", key: "progress", cls: "num w-prog" },   // ＝已完成÷總數，系統算
  { label: "燈號", key: "rag", cls: "w-rag" },               // 系統依進度與起訖日判定
  { label: "關鍵風險點", key: "risk_note", cls: "w-note" },   // 紅/黃燈時必填
  { label: "決策", key: "decision_needed", cls: "w-note" },
  { label: "支援", key: "support_needed", cls: "w-note" },
];
// 系統算出來的欄位不給手改（改了也會被下一次彙總蓋掉，開放編輯只會誤導）
const PF_ITEM_READONLY = new Set(["seq", "progress", "rag"]);
let pfItemSort = null;  // {col, dir}；null＝用預設的「離今天近的先」排序
// 目前這個專案在畫面上的工作項快照，key=id。inline 編輯就地改一格時要用它重建那一格顯示，
// 不必整表重載（重載會重排、閃動、還會把焦點搶走）。
let pfItemCache = new Map();

// 單一欄的「顯示模式」HTML（非編輯狀態）。inline 存檔成功後用它把該格畫回唯讀樣子。
function pfCellHtml(field, it) {
  switch (field) {
    case "seq": return String(Number(it.seq || 0));
    case "item_name": return escapeHtml(valueOrDash(it.item_name));
    case "owner": return escapeHtml(valueOrDash(it.owner));
    case "start_date": return escapeHtml(valueOrDash(it.start_date));
    case "end_date": return escapeHtml(valueOrDash(it.end_date));
    case "exec_status": return escapeHtml(valueOrDash(it.exec_status));  // 純文字；燈號移到獨立的「燈號」欄（B1）
    case "sub_total": {
      // 子項總數可以再往下追：有子項就展開清單，只有數字（Excel 帶進來的）就給「拆成子項目」
      const n = Number(it.sub_total || 0);
      const hasList = Number(it.subitem_count || 0) > 0;
      if (hasList) {
        return `<button type="button" class="link-btn" data-subitems="${it.id}"
          title="展開子項目清單（這個數字是子項算出來的）">${n} ▸</button>`;
      }
      return n > 0
        ? `${n} <button type="button" class="link-btn" data-split-item="${it.id}"
             title="這個數字沒有對應的子項目清單（多半是 Excel 帶進來的）。拆開後可以逐項填內容與勾完成">拆開</button>`
        : `<button type="button" class="link-btn" data-subitems="${it.id}" title="新增子項目">＋子項</button>`;
    }
    case "sub_done": return String(Number(it[field] || 0));
    case "progress": {  // ＝已完成÷總數（後端算），標示出來讓人知道不是手填的
      const n = Number(it.progress || 0);
      return `<span title="＝已完成 ${Number(it.sub_done || 0)} ÷ 子項總數 ${Number(it.sub_total || 0)}，系統自動計算">${n}%</span>`;
    }
    case "rag": {  // 獨立燈號欄：圓點＋文字標籤
      const tone = pfItemRag(it);
      return `<span class="pf-dot ${tone}" title="依進度與起訖日自動判定（可在後端人工指定覆蓋）"></span> ${escapeHtml(RAG_LABEL[tone] || tone)}`;
    }
    default: return escapeHtml(valueOrDash(it[field]));  // 風險/決策/支援等純文字欄，各自獨立一欄
  }
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
    if (key === "rag") {  // 依急迫度排：已過期→要注意→執行中→未開始→已完成（asc＝最急的在前）
      const rank = { over: 0, soon: 1, live: 2, todo: 3, done: 4, na: 5 };
      r = (rank[pfItemRag(a)] ?? 9) - (rank[pfItemRag(b)] ?? 9);
    } else if (key === "progress" || key === "seq") {
      r = Number(a[key] || 0) - Number(b[key] || 0);
    } else if (key === "start_date" || key === "end_date") {
      const da = a[key] ? new Date(a[key]).getTime() : Infinity;
      const db = b[key] ? new Date(b[key]).getTime() : Infinity;
      r = da - db;
    } else {
      const va = String(a[key] || "");
      const vb = String(b[key] || "");
      r = va.localeCompare(vb, "zh-Hant");
    }
    return dir === "desc" ? -r : r;
  });
  return arr;
}

function renderItemsSection(projectId, items) {
  const editable = canEditPortfolio();
  pfItemCache = new Map(items.map((it) => [String(it.id), it]));  // inline 就地重建那一格要用
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
        const cells = PF_ITEM_COLUMNS.map((c) => {
          const canEditCell = editable && !PF_ITEM_READONLY.has(c.key);  // 標號/完成度/燈號都是系統算的
          const cls = [c.cls, canEditCell ? "editable" : ""].filter(Boolean).join(" ");
          const attrs = `${cls ? ` class="${cls}"` : ""}${canEditCell ? ` data-field="${c.key}" title="點一下即可修改"` : ""}`;
          return `<td${attrs}>${pfCellHtml(c.key, it)}</td>`;
        }).join("");
        const ops = editable
          ? `<button type="button" class="btn-sm" data-item-extend="${it.id}" title="展延結束日（保留原日期與展延歷程）">展延</button>`
            + ` <button type="button" class="danger btn-sm" data-item-del="${it.id}">刪除</button>`
          : "—";
        return `<tr data-item-id="${it.id}">${cells}<td class="col-actions">${ops}</td></tr>`;
      }).join("")
    : `<tr><td colspan="${PF_ITEM_COLUMNS.length + 1}" class="muted">尚無工作項${editable ? "，可按右上「新增工作項」建立。" : "。"}</td></tr>`;
  return `
    <div class="pf-items-head"><strong>工作項（${items.length}）</strong>${addBtn}</div>
    ${editable ? '<p class="pf-items-hint muted">直接點格子即可修改，改完按 Enter 或點別處自動儲存，按 Esc 取消；點欄名可排序；表格太寬可左右捲。</p>' : ""}
    <div class="grid-scroll">
      <table class="grid-table pf-items-table">
        <thead><tr>${head}<th class="col-actions">操作</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div id="pf-subitems" class="schedule-panel" hidden></div>
    <div id="pf-extend-panel" class="schedule-panel" hidden></div>
    <datalist id="pf-item-personnel-list">${personnelDatalistOptions()}</datalist>`;
}

// ── WBS 展延（第三次回饋 8.4）：跟 §10 合約調整同一套 UI pattern——現值＋歷程，不覆蓋原日期 ──
async function loadItemExtensions(itemId) {
  const box = document.querySelector("#pf-extend-panel");
  if (!box) return;
  box.hidden = false;
  box.dataset.itemId = itemId;
  box.innerHTML = `<p class="muted">載入展延紀錄…</p>`;
  try {
    const items = (await api(`/api/project-items/${itemId}/extensions`)).data || [];
    const it = (pfItemsCache || []).find((x) => String(x.id) === String(itemId)) || {};
    box.innerHTML = renderExtendPanel(itemId, it, items);
  } catch (e) {
    box.innerHTML = `<p class="error">展延紀錄載入失敗：${escapeHtml(e.message)}</p>`;
  }
}

function renderExtendPanel(itemId, it, items) {
  const editable = canEditPortfolio();
  const current = it.end_date || "";

  const rows = items.length ? items.map((a) => `<tr>`
      + `<td>${escapeHtml(valueOrDash(a.old_end_date))} → ${escapeHtml(valueOrDash(a.new_end_date))}</td>`
      + `<td>${escapeHtml(valueOrDash(a.reason))}</td>`
      + `<td class="muted">${escapeHtml(valueOrDash(a.created_by))}</td>`
      + `<td class="muted">${escapeHtml(valueOrDash(a.created_at))}</td></tr>`).join("")
    : `<tr><td colspan="4" class="muted">還沒展延過——結束日就是原訂日期。</td></tr>`;

  const form = editable ? `
    <div class="adj-form">
      <label>展延後結束日 <input type="date" data-ext-date value="${escapeHtml(current)}"></label>
      <label class="adj-reason">原因 <input type="text" data-ext-reason placeholder="如：廠商延遲交貨 / 驗收條件未到位"></label>
      <button type="button" class="btn-sm" data-ext-add="${itemId}">申請展延</button>
    </div>
    <p class="muted adj-hint">燈號是「有延遲風險」或「已延遲」時，關鍵風險點要先在工作項那格填清楚，才能送出展延。</p>` : "";

  return `<div class="sched-head"><strong>展延歷程</strong>　<span class="muted">${escapeHtml(it.item_name || "")}　原訂結束日 ${escapeHtml(valueOrDash(current))}</span>`
    + `<button type="button" class="btn-sm secondary sched-close" data-ext-close>收起</button></div>`
    + `<table class="grid-table sched-table"><thead><tr><th>結束日變動</th><th>原因</th><th>記錄者</th><th>時間</th></tr></thead><tbody>${rows}</tbody></table>`
    + form;
}

document.addEventListener("click", async (event) => {
  const box = document.querySelector("#pf-extend-panel");
  if (!box) return;
  if (event.target.closest("[data-ext-close]") && box.contains(event.target)) { box.hidden = true; return; }
  const addBtn = event.target.closest("[data-ext-add]");
  if (!addBtn || !box.contains(addBtn)) return;
  const itemId = box.dataset.itemId;
  const dateEl = box.querySelector("[data-ext-date]");
  const newEndDate = dateEl.value;
  if (!newEndDate) { window.alert("請先填展延後的結束日。"); return; }
  try {
    await api(`/api/project-items/${itemId}/extensions`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_end_date: newEndDate, reason: box.querySelector("[data-ext-reason]").value || "" }),
    });
    await reloadPfItems();
    await loadItemExtensions(itemId);
  } catch (e) { window.alert(e.message); }
});

// ── 子項目：工作項再往下一層（使用者 2026-08-12「子項總數怎不能繼續追下去」）──
// 拆開之後「子項總數／已完成／完成度／燈號」都由這裡算，工作項那兩欄不再手填。
async function loadSubitems(itemId) {
  const box = document.querySelector("#pf-subitems");
  if (!box || !itemId || itemId === "undefined") return;
  box.hidden = false;
  box.dataset.itemId = itemId;
  box.innerHTML = `<p class="muted">載入子項目…</p>`;
  try {
    const subs = (await api(`/api/project-items/${itemId}/subitems`)).data || [];
    const item = (pfItemsCache || []).find((x) => String(x.id) === String(itemId)) || {};
    const editable = currentUser && (currentUser.allowed_actions || []).includes("edit");
    const rows = subs.length ? subs.map((s) => `<tr>
        <td class="num">${s.seq}</td>
        <td><input class="cell-input" data-sub-field="name" data-sub-id="${s.id}"
              value="${escapeHtml(s.name || "")}"${editable ? "" : " disabled"} /></td>
        <td><input class="cell-input" data-sub-field="owner" data-sub-id="${s.id}" list="pf-item-personnel-list"
              value="${escapeHtml(s.owner || "")}"${editable ? "" : " disabled"} /></td>
        <td><input class="cell-input" type="date" data-sub-field="end_date" data-sub-id="${s.id}"
              value="${escapeHtml(s.end_date || "")}"${editable ? "" : " disabled"} /></td>
        <td class="num"><input type="checkbox" data-sub-field="done" data-sub-id="${s.id}"
              ${s.done ? "checked" : ""}${editable ? "" : " disabled"} title="勾了就算完成，完成度自動重算" /></td>
        <td><input class="cell-input" data-sub-field="note" data-sub-id="${s.id}"
              value="${escapeHtml(s.note || "")}" placeholder="備註"${editable ? "" : " disabled"} /></td>
        <td>${editable ? `<button type="button" class="danger btn-sm" data-sub-del="${s.id}">刪除</button>` : ""}</td>
      </tr>`).join("")
      : `<tr><td colspan="7" class="muted">還沒有子項目${editable ? "，用下面那列新增。" : "。"}</td></tr>`;
  box.innerHTML = `
      <div class="sched-head">
        <h3>${escapeHtml(item.item_name || "工作項")}　子項目
          <span class="muted">完成 ${Number(item.sub_done || 0)} / 共 ${Number(item.sub_total || 0)}
          （這兩個數字由子項目算出來，不用手填）</span></h3>
        <button type="button" class="secondary btn-sm" data-sub-close>收合</button>
      </div>
      <div class="grid-scroll"><table class="grid-table">
        <thead><tr><th class="w-seq">#</th><th>子項目名稱</th><th class="w-owner">負責人</th>
        <th class="w-date">完成日</th><th class="w-seq">完成</th><th>備註</th><th class="col-actions">操作</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
      ${editable ? `<form class="resource-form" data-sub-form="${itemId}">
        <input data-new-sub-name placeholder="子項目名稱 *" required />
        <input data-new-sub-owner placeholder="負責人" list="pf-item-personnel-list" />
        <input data-new-sub-end type="date" title="完成日" />
        <button type="submit">新增子項目</button>
      </form>` : ""}`;
    box.scrollIntoView({ block: "nearest" });
  } catch (e) {
    box.innerHTML = `<p class="error">子項目載入失敗：${escapeHtml(e.message)}</p>`;
  }
}

document.addEventListener("click", async (event) => {
  const open = event.target.closest("[data-subitems]");
  if (open) { await loadSubitems(open.getAttribute("data-subitems")); return; }
  if (event.target.closest("[data-sub-close]")) {
    document.querySelector("#pf-subitems").hidden = true;
    return;
  }
  const split = event.target.closest("[data-split-item]");
  if (split) {
    const id = split.getAttribute("data-split-item");
    split.disabled = true;
    split.textContent = "拆開中…";
    try {
      const r = (await api(`/api/project-items/${id}/split`, { method: "POST" })).data;
      await reloadPfItems();
      await loadSubitems(id);
      window.alert(`已拆成 ${r.created} 筆子項目（前 ${r.done} 筆先標成完成），名稱請自行改成實際內容。`);
    } catch (e) {
      split.disabled = false;
      split.textContent = "拆開";
      window.alert(`拆開失敗：${e.message}`);
    }
    return;
  }
  const del = event.target.closest("[data-sub-del]");
  if (del) {
    if (!window.confirm("刪掉這個子項目？完成度會跟著重算。")) return;
    // 先把 itemId 抓起來：reloadPfItems 會重畫整個工作項區塊（連帶換掉 #pf-subitems 這個元素），
    // 之後再讀它的 dataset 就是新的空元素，拿到 undefined。
    const itemId = document.querySelector("#pf-subitems")?.dataset.itemId;
    try {
      await api(`/api/project-subitems/${del.getAttribute("data-sub-del")}`, { method: "DELETE" });
      await reloadPfItems();
      await loadSubitems(itemId);
    } catch (e) { window.alert(`刪除失敗：${e.message}`); }
  }
});

document.addEventListener("change", async (event) => {
  const el = event.target.closest("[data-sub-field]");
  if (!el) return;
  const field = el.getAttribute("data-sub-field");
  const value = el.type === "checkbox" ? (el.checked ? 1 : 0) : el.value;
  const itemId = document.querySelector("#pf-subitems")?.dataset.itemId;   // reload 前先抓（見上面的註解）
  try {
    await api(`/api/project-subitems/${el.getAttribute("data-sub-id")}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [field]: value }),
    });
    await reloadPfItems();                     // 工作項的完成度／燈號跟著變
    await loadSubitems(itemId);
  } catch (e) { window.alert(`儲存失敗：${e.message}`); }
});

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("[data-sub-form]");
  if (!form) return;
  event.preventDefault();
  const itemId = form.getAttribute("data-sub-form");
  try {
    await api(`/api/project-items/${itemId}/subitems`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: form.querySelector("[data-new-sub-name]").value,
        owner: form.querySelector("[data-new-sub-owner]").value,
        end_date: form.querySelector("[data-new-sub-end]").value,
      }),
    });
    await reloadPfItems();
    await loadSubitems(itemId);
  } catch (e) { window.alert(`新增子項目失敗：${e.message}`); }
});

// 助理定義的五色燈號代碼（後端 WBS_RAG_ORDER）→ 本站既有的色調 class。
const WBS_RAG_TO_TONE = { gray: "done", white: "todo", green: "live", yellow: "soon", red: "over" };

// 工作項燈號：**以後端算好並存起來的 rag 為準**（同一套算法也用在專案彙總、匯入），
// 前端只做代碼轉色調。舊資料 rag 為空時才退回前端 ragOf() 自己判——
// 否則同一個判斷寫兩份，兩邊遲早會演化出不同結果（畫面說如期、彙總說落後）。
function pfItemRag(it) {
  return WBS_RAG_TO_TONE[it.rag] || ragOf(it);
}

// 負責人：跟其他表單一樣接人員主檔，但用 datalist（可選也可打）而非鎖死的 select——
// 工作項的負責人常是「吳承翰&楊凡」這種多人組合，硬性 select 只能選一個人會擋掉這種真實案例。
function personnelDatalistOptions() {
  return (personnelMasterCache || []).map((p) => `<option value="${escapeHtml(p.name)}"></option>`).join("");
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

// 工作項維護：新增用表單、既有項目用 inline 就地編輯、刪除；承辦也可，直接生效。
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
  // 點可編輯的格子＝就地進入 inline 編輯（Excel 式）。點在已編輯中的格子（輸入框上）不重進。
  const cell = event.target.closest("td.editable");
  if (cell) {
    if (!cell.classList.contains("editing")) pfBeginEdit(cell);
    return;
  }
  const add = event.target.closest("[data-item-add]");
  const del = event.target.closest("[data-item-del]");
  const extend = event.target.closest("[data-item-extend]");
  if (extend) { await loadItemExtensions(extend.getAttribute("data-item-extend")); return; }
  // 新增＝直接在表格多一列（帶預設名），再自動聚焦「工作主項目」讓使用者當場 inline 改，不開表單
  if (add) {
    const pid = Number(add.getAttribute("data-item-add"));
    try {
      const created = await api(`/api/projects/${pid}/items`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ item_name: "未命名工作項" }) });
      await loadProjectItems(pid);
      const newCell = [...document.querySelectorAll('#pf-items td.editable[data-field="item_name"]')]
        .find((td) => td.closest(`tr[data-item-id="${created.data.id}"]`));
      if (newCell) pfBeginEdit(newCell);
    } catch (error) { window.alert(`新增失敗：${error.message}`); }
    return;
  }
  if (del) {
    if (!window.confirm("確定刪除這個工作項？")) return;
    await api(`/api/project-items/${del.getAttribute("data-item-del")}`, { method: "DELETE" });
    const pid = document.querySelector("#pf-items")?.getAttribute("data-project-id");
    await loadProjectItems(Number(pid));
    return;
  }
});

// ── 工作項 inline 編輯（Excel 式：點格子就改，Enter/失焦自動存，Esc 取消）──────────────
// 後端 PATCH /api/project-items/{id} 支援單欄更新，所以每格只送有動到的欄位。
let pfEditingCell = null;  // { td, id, field } 或 null

// 各欄在「編輯模式」放什麼輸入元件；input 上用 data-k 標記對應的後端欄位。
function pfEditorHtml(field, it) {
  const v = (k) => escapeHtml(it[k] ?? "");
  const dateVal = (k) => escapeHtml(String(it[k] ?? "").replaceAll("/", "-"));  // 讓 <input type=date> 吃得下 2026/06/01
  switch (field) {
    case "item_name":
      return `<input class="cell-input" data-k="item_name" value="${v("item_name")}" />`;
    case "owner":
      return `<input class="cell-input" data-k="owner" list="pf-item-personnel-list" value="${v("owner")}" />`;
    case "start_date":
      return `<input class="cell-input" type="date" data-k="start_date" value="${dateVal("start_date")}" />`;
    case "end_date":
      return `<input class="cell-input" type="date" data-k="end_date" value="${dateVal("end_date")}" />`;
    case "sub_total": case "sub_done":  // 人只填這兩個數字，完成度由系統算
      return `<input class="cell-input" type="number" min="0" step="1" data-k="${field}" value="${Number(it[field] || 0)}" />`;
    case "exec_status":  // 只改執行進度文字；燈號改自動判定，不再手選
      return `<input class="cell-input" data-k="exec_status" value="${v("exec_status")}" placeholder="如：進行中/已完成" />`;
    default:  // 風險/決策/支援等純文字欄，各自一格單一輸入
      return `<input class="cell-input" data-k="${field}" value="${v(field)}" />`;
  }
}

function pfBeginEdit(td) {
  if (pfEditingCell && pfEditingCell.td === td) return;
  if (pfEditingCell) pfCommitEdit(pfEditingCell);  // 先把上一格存掉（非同步，內部會先釋放鎖）
  const field = td.getAttribute("data-field");
  const id = td.closest("tr[data-item-id]")?.getAttribute("data-item-id");
  const it = pfItemCache.get(String(id));
  if (!field || !it) return;
  pfEditingCell = { td, id, field };
  td.classList.add("editing");
  td.innerHTML = pfEditorHtml(field, it);
  const first = td.querySelector("input, select");
  if (first) { first.focus(); if (first.select) first.select(); }
}

async function pfCommitEdit(cell = pfEditingCell) {
  if (!cell) return;
  if (pfEditingCell === cell) pfEditingCell = null;  // 先釋放鎖，允許馬上編下一格
  const { td, id, field } = cell;
  const it = pfItemCache.get(String(id)) || {};
  const patch = {};
  td.querySelectorAll("[data-k]").forEach((el) => {
    const k = el.getAttribute("data-k");
    patch[k] = ["progress", "sub_total", "sub_done"].includes(k)
      ? (el.value === "" ? 0 : Number(el.value)) : el.value;
  });
  const changed = Object.keys(patch).some((k) => String(patch[k] ?? "") !== String(it[k] ?? ""));
  if (!changed) { td.classList.remove("editing"); td.innerHTML = pfCellHtml(field, it); return; }
  td.classList.add("saving");
  try {
    const saved = (await api(`/api/project-items/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch) })).data || {};
    // 用後端回傳的整列覆蓋快取：改了子項目數之後，完成度與燈號是後端重算的，
    // 只把使用者輸入的欄位塞回去會讓那兩格停在舊值（畫面說 20%、資料庫是 70%）。
    Object.assign(it, patch, saved);
    pfItemCache.set(String(id), it);
    td.classList.remove("editing", "saving");
    td.innerHTML = pfCellHtml(field, it);
    // 同一列的衍生欄（完成度／燈號）跟著重畫——欄位順序就是 PF_ITEM_COLUMNS 的順序
    const tr = td.closest("tr[data-item-id]");
    if (tr) {
      PF_ITEM_COLUMNS.forEach((c, i) => {
        if (PF_ITEM_READONLY.has(c.key) && tr.children[i]) tr.children[i].innerHTML = pfCellHtml(c.key, it);
      });
    }
    td.classList.add("saved");
    setTimeout(() => td.classList.remove("saved"), 900);
    if (["sub_total", "sub_done", "start_date", "end_date", "rag"].includes(field)) {
      loadPortfolio();   // 專案完成%/起訖日/總燈號由 WBS 彙總而來，要跟著刷新
    }
  } catch (error) {
    td.classList.remove("editing", "saving");
    td.innerHTML = pfCellHtml(field, it);  // 存失敗就還原成原值，不吃掉使用者的資料
    td.classList.add("save-error");
    td.setAttribute("title", `儲存失敗：${error.message}`);
    setTimeout(() => { td.classList.remove("save-error"); td.setAttribute("title", "點一下即可修改"); }, 2600);
  }
}

function pfCancelEdit() {
  if (!pfEditingCell) return;
  const { td, id, field } = pfEditingCell;
  pfEditingCell = null;
  const it = pfItemCache.get(String(id)) || {};
  td.classList.remove("editing");
  td.innerHTML = pfCellHtml(field, it);
}

// Enter 存、Esc 取消（多欄的追蹤事項也是 Enter 一次全存）
document.querySelector("#pf-view")?.addEventListener("keydown", (event) => {
  if (!pfEditingCell) return;
  if (event.key === "Enter") { event.preventDefault(); pfCommitEdit(); }
  else if (event.key === "Escape") { event.preventDefault(); pfCancelEdit(); }
});

// 失焦離開整個格子＝自動存；在同一格的多個輸入框之間跳不算（setTimeout 等焦點落定後再判斷）
document.querySelector("#pf-view")?.addEventListener("focusout", () => {
  const cell = pfEditingCell;
  if (!cell) return;
  setTimeout(() => {
    if (pfEditingCell === cell && !cell.td.contains(document.activeElement)) pfCommitEdit(cell);
  }, 0);
});


// 全文搜尋比對到專案「工作項」子項時，導去進度總表點開那個專案（子項細節在這裡才看得到，
// 不是專案模組的基本編輯表單）——找到所屬組別/子分頁後設定 portfolioState 再重繪。
async function openProjectItem(projectId) {
  navigateToPanel("projects");        // 進度總表已搬到「專案」模組（助理 2026-08-03 回饋）
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

const STATUS_LABELS = { draft: "草稿", pending_review: "待複核", reviewing: "審核中", approved: "已核准", disabled: "已停用",
                        returned: "退回補件", rejected: "已駁回", merged: "已併入他案",
                        // 需求書 §4 核准之後的生命週期
                        in_progress: "進行中", paused: "暫停", closed: "已結案", cancelled: "已取消" };

// 核准之後可以按的狀態動作：label／要不要填原因／是不是主管限定。
// 對照後端 CASE_FLOW，只在「現在的狀態走得過去」時才顯示按鈕。
const CASE_STATUS_ACTIONS = {
  approved: [{ act: "start", label: "開始執行" }],
  in_progress: [{ act: "pause", label: "暫停", ask: "暫停原因（等廠商／等預算…）：" },
                { act: "close", label: "結案" }],
  paused: [{ act: "resume", label: "復工" }],
  closed: [{ act: "reopen", label: "重新開啟", ask: "重開原因（會記錄重開人與時間）：", manager: true }],
};
const CASE_CANCEL_FROM = ["approved", "in_progress", "paused"];   // 這些狀態都還能撤案

// 併案時會一起搬過去的資料表 → 中文（tableLabels 只涵蓋四個模組，這裡六個都要有名字）
const MERGE_TABLE_LABEL = { budgets: "預算", projects: "專案", signoffs: "簽呈",
                            purchases: "費用", contracts: "合約", documents: "文件" };

// 併案挑目標：不能叫使用者自己去記案件 ID，開一個小面板列出既有案件、可打字過濾、點一列就選定。
// 已被併走／已駁回的不能當目標（併過去會接不下去）。回傳 null＝使用者取消。
function pickMergeTarget(caseId) {
  return new Promise((resolve) => {
    const candidates = (caseCache || []).filter(
      (c) => String(c.id) !== String(caseId) && !["merged", "rejected"].includes(c.status));
    if (!candidates.length) {
      window.alert("目前沒有可以併入的既有案件。");
      resolve(null);
      return;
    }
    const box = document.createElement("div");
    box.className = "merge-picker-backdrop";
    box.innerHTML = `
      <div class="merge-picker" role="dialog" aria-label="併入既有案件">
        <div class="section-heading compact"><h3>併入哪一件既有案件？</h3></div>
        <p class="muted">這件申請底下的預算／專案／簽呈／費用／合約／文件會一起轉過去，並記錄「併自哪一件」。</p>
        <input type="search" class="merge-filter" placeholder="輸入案件編號或名稱過濾" aria-label="過濾案件">
        <div class="merge-list"></div>
        <label class="merge-reason">併案原因（選填）<input type="text" placeholder="如：與 CASE-0007 同一件冷氣維護"></label>
        <div class="merge-actions"><button type="button" class="secondary btn-sm" data-merge-cancel>取消</button></div>
      </div>`;
    document.body.appendChild(box);
    const listEl = box.querySelector(".merge-list");
    const filterEl = box.querySelector(".merge-filter");
    const draw = () => {
      const q = filterEl.value.trim().toLowerCase();
      const rows = candidates.filter((c) => !q
        || (c.case_code || "").toLowerCase().includes(q) || (c.title || "").toLowerCase().includes(q));
      listEl.innerHTML = rows.length
        ? rows.map((c) => `<button type="button" class="merge-row" data-target="${c.id}">`
            + `<strong>${escapeHtml(c.case_code)}</strong> ${escapeHtml(c.title || "")}`
            + `<span class="muted">${escapeHtml(STATUS_LABELS[c.status] || c.status)}｜${escapeHtml(c.owner || "未指派")}</span></button>`).join("")
        : `<p class="muted">沒有符合的案件。</p>`;
    };
    draw();
    filterEl.addEventListener("input", draw);
    const close = (value) => { box.remove(); resolve(value); };
    box.addEventListener("click", (event) => {
      if (event.target === box || event.target.closest("[data-merge-cancel]")) { close(null); return; }
      const row = event.target.closest("[data-merge-row], .merge-row");
      if (!row) return;
      const target = candidates.find((c) => String(c.id) === row.getAttribute("data-target"));
      close({ id: target.id, label: `${target.case_code} ${target.title || ""}`.trim(),
              reason: box.querySelector(".merge-reason input").value.trim() });
    });
    filterEl.focus();
  });
}

// 依角色/建立者算出案件的複核動作按鈕（需求書 §4 四種審核結果）
function caseWorkflowButtons(item) {
  const btns = [];
  // 退回補件的案子補完可以直接再送，沿用原暫時號、不用重開一件
  if (["draft", "reviewing", "returned"].includes(item.status)) {
    btns.push(`<button type="button" class="secondary btn-sm" data-action="submit">送出複核</button>`);
  }
  if (item.status === "pending_review") {
    const isSubmitter = currentUser && (item.created_by || "") === currentUser.username;
    const isManager = isReviewer(currentUser);
    if (isManager && !isSubmitter) {
      btns.push(`<button type="button" class="btn-sm" data-action="approve">核准</button>`);
    }
    if (isManager && isSubmitter) {
      btns.push(`<span class="muted" title="不能核准自己建立的案件">待他人複核</span>`);
    }
    if (isManager) {
      // 核准以外的三條路：資料不齊→退回補件；已經有同一件→併案；不該立案→駁回但留紀錄
      btns.push(`<button type="button" class="secondary btn-sm" data-action="return" title="資料不齊，退回讓申請人補">退回補件</button>`);
      btns.push(`<button type="button" class="secondary btn-sm" data-action="merge" title="這件事已經有案子了，併過去">併入既有案</button>`);
      btns.push(`<button type="button" class="secondary btn-sm danger" data-action="reject" title="不該立案，但申請紀錄留著">駁回</button>`);
    }
    // 取消複核（退回草稿）：原提交者或主管/助理都可以，不像核准有球員兼裁判風險
    if (isSubmitter || isManager) {
      btns.push(`<button type="button" class="secondary btn-sm" data-action="cancel-review">取消複核</button>`);
    }
  }
  // 核准之後的生命週期：開始執行／暫停／復工／結案／重開，外加隨時可撤案
  for (const a of CASE_STATUS_ACTIONS[item.status] || []) {
    if (a.manager && !isReviewer(currentUser)) continue;
    btns.push(`<button type="button" class="secondary btn-sm" data-status-act="${a.act}">${a.label}</button>`);
  }
  if (CASE_CANCEL_FROM.includes(item.status) && isReviewer(currentUser)) {
    btns.push(`<button type="button" class="secondary btn-sm danger" data-status-act="cancel" title="撤案（限主管）">取消案件</button>`);
  }
  return btns.join(" ");
}

async function loadTodo() {
  if (!todoList) return;
  const payload = await api("/api/todo");
  const items = payload.data || [];
  setText("#tile-count-todo", `匯入預檢・待辦 ${items.length}`);
  // 待辦改由日期自動生成（使用者拍板 2026-07-29）：卡在審核流程的案件 ＋ 快到期的合約/保固/維護
  // ＋ 快到預計付款日的排程。不再靠人工填「下一步」。
  const TODO_KIND_LABEL = { case: "待處理", contract: "合約到期", warranty: "保固到期",
                            maintenance: "維護到期", payment_due: "預計付款" };
  todoList.innerHTML = items.length
    ? items
        .map((c) => {
          const overdue = c.days_left != null && c.days_left < 0;
          const when = c.days_left == null ? ""
            : overdue ? `（已過期 ${-c.days_left} 天）` : `（剩 ${c.days_left} 天）`;
          const badge = c.kind === "case" ? (STATUS_LABELS[c.status] || c.status) : TODO_KIND_LABEL[c.kind];
          return `
            <li data-case-id="${c.id || ""}" style="cursor:pointer" title="點此開啟相關案件">
              <span class="badge ${overdue ? "danger" : c.kind === "case" ? "warn" : "ok"}">${escapeHtml(badge)}</span>
              <strong>${escapeHtml(c.case_code)}　${escapeHtml(c.title)}</strong>
              <small>${escapeHtml(c.detail || "—")}${c.due_date ? `；${escapeHtml(c.due_date)}${when}` : ""}${c.owner ? `；負責人：${escapeHtml(c.owner)}` : ""}</small>
            </li>`;
        })
        .join("")
    : `<li><small class="muted">目前沒有待辦：沒有卡在審核的案件，也沒有 30 天內要處理的到期或付款。</small></li>`;
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

// 費用類別分析：「錢花在哪一類」有兩種合理讀法（預算類別 vs 合約類型），兩種都給、由使用者切，
// 不預先幫他決定。歸不出來的（沒預算、或一案跨多類別）獨立成列並標黃，提示要人工歸戶——
// 塞進「其他」會讓數字看起來很完整，其實是把問題藏起來。
async function loadExpenseCategories() {
  const body = document.querySelector("#expense-category-body");
  if (!body) return;
  const dim = document.querySelector("#category-dimension")?.value || "budget";
  const data = (await api(`/api/reports/expense-categories?dimension=${dim}`)).data || {};
  const rows = data.rows || [];
  const t = data.totals || {};
  const fmt = (n) => Number(n || 0).toLocaleString();
  const lines = rows.map((r) => {
    const pct = t.paid ? `${Math.round((r.paid / t.paid) * 100)}%` : "—";
    const flag = r.needs_attention ? ' <span class="badge warn">待歸戶</span>' : "";
    return `<tr${r.needs_attention ? ' class="needs-attention"' : ""}>
      <td>${escapeHtml(r.category)}${flag}</td>
      <td class="num">${fmt(r.contract_amount)}</td>
      <td class="num">${fmt(r.paid)}</td>
      <td class="num">${fmt(r.pending)}</td>
      <td class="num">${r.payment_count}</td>
      <td class="num">${pct}</td>
    </tr>`;
  });
  if (rows.length) {
    lines.push(`<tr class="total-row"><td>合計</td><td class="num">${fmt(t.contract_amount)}</td>`
      + `<td class="num">${fmt(t.paid)}</td><td class="num">${fmt(t.pending)}</td>`
      + `<td class="num">${rows.reduce((s, r) => s + r.payment_count, 0)}</td><td class="num">100%</td></tr>`);
  }
  body.innerHTML = lines.join("") || `<tr><td colspan="6" class="muted">目前沒有合約或付款資料。</td></tr>`;

  const chart = document.querySelector("#category-chart");
  if (chart) {
    const seg = rows.filter((r) => r.paid > 0)
      .map((r, i) => ({ label: r.category, value: r.paid, color: CHART_COLORS[i % CHART_COLORS.length], text: `${fmt(r.paid)} 元` }));
    chart.innerHTML = seg.length
      ? chartCard(dim === "budget" ? "已付金額：依預算類別" : "已付金額：依合約類型",
                  donutSVG(seg, { center: "已付" }) + chartLegend(seg))
      : `<p class="muted">還沒有已付款項可以分類。</p>`;
  }
}
document.querySelector("#category-dimension")?.addEventListener("change", loadExpenseCategories);

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

// 到期提醒分階段：合約沒人管就是自動續約或斷保，所以不是「快到期」一句話帶過，而是
// 已過期 / 7 / 30 / 60 / 90 天五格，點格就地過濾（沿用進度總表 B2 的統計列互動）。
// 合約到期、保固到期、維護到期是三件不同的事，各自一列，才不會續了約卻忘了續保。
const EXPIRY_BUCKETS = [
  { key: "overdue", label: "已過期" },
  { key: "d7", label: "7 天內" },
  { key: "d30", label: "30 天內" },
  { key: "d60", label: "60 天內" },
  { key: "d90", label: "90 天內" },
];
let expiryFilter = null;  // null＝全部；否則是某一格的 key

async function loadExpiring() {
  const el = document.querySelector("#expiring-list");
  if (!el) return;
  const d = (await api("/api/reports/expiring-contracts")).data || {};
  const all = d.items || [];
  const counts = d.counts || {};
  if (expiryFilter && !counts[expiryFilter]) expiryFilter = null;  // 那格被處理完就自動回全部

  const stat = (key, label, n) =>
    `<button type="button" class="pf-stat${key ? "" : " pf-stat-all"}${expiryFilter === key ? " active" : ""}"`
    + ` data-expiry-filter="${key || ""}"${n === 0 ? " disabled" : ""}>`
    + `${key ? `<span class="pf-dot exp-${key}"></span>` : ""}${label} <b>${n}</b></button>`;
  const stats = `<li class="expiry-stats-row"><div class="pf-stats" role="group" aria-label="依到期階段篩選">`
    + stat(null, "全部", all.length)
    + EXPIRY_BUCKETS.map((b) => stat(b.key, b.label, counts[b.key] || 0)).join("")
    + `</div></li>`;

  const items = expiryFilter ? all.filter((x) => x.stage === expiryFilter) : all;
  const body = document.createElement("ul");
  renderExpandableList(body, "expiring", items, (x) => {
    const left = x.days_left < 0 ? `已過期 ${-x.days_left} 天` : `剩 ${x.days_left} 天`;
    return `
      <li>
        <span class="pf-dot exp-${x.stage}"></span>
        <span class="expiry-kind">${escapeHtml(x.kind_label)}</span>
        <strong>${escapeHtml(x.contract_code)}　${escapeHtml(x.contract_name)}</strong>
        <small>${escapeHtml(x.due_date)}（${left}）；廠商：${escapeHtml(x.vendor_name || "—")}；金額：${money(x.amount)} 元</small>
      </li>`;
  }, expiryFilter ? "這個階段目前沒有要處理的到期項目。" : "目前沒有 90 天內到期或已過期的合約／保固／維護。");
  el.innerHTML = stats + body.innerHTML;
}

document.addEventListener("click", (event) => {
  const btn = event.target.closest("[data-expiry-filter]");
  if (!btn) return;
  const key = btn.getAttribute("data-expiry-filter") || null;
  expiryFilter = (expiryFilter === key) ? null : key;  // 再點同一格＝取消過濾
  loadExpiring();
});

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
  // §8：待付款＝預計未付、下月預計付款＝來自付款排程（比只看已核銷的 payments 完整）
  const payableYear = d.payable_by_year || {};
  const yearLine = Object.keys(payableYear).length
    ? `<p class="cio-year-line muted">各年度待付（依預計付款日歸屬）：${Object.entries(payableYear)
        .map(([y, v]) => `${y} <b>${money(v)}</b> 元`).join("　｜　")}</p>`
    : "";
  // 到期雷達：合約/保固/維護沒人續就是自動續約或斷保，CIO 一頁要看得到還有幾件沒處理
  const xc = d.expiry_counts || {};
  const urgent = (xc.overdue || 0) + (xc.d7 || 0);
  const expiryLine = (xc.overdue || xc.d7 || xc.d30)
    ? `<p class="cio-expiry-line ${urgent ? "urgent" : "muted"}">到期待處理（合約／保固／維護）：`
      + `已過期 <b>${xc.overdue || 0}</b>　｜　7 天內 <b>${xc.d7 || 0}</b>　｜　30 天內 <b>${xc.d30 || 0}</b></p>`
    : "";
  cioMetrics.innerHTML = [
    metric("待付款（預計未付）", `${money(d.payable_planned || 0)} 元`),
    metric("下月預計付款", `${money(d.next_month_planned || 0)} 元`),
    metric("本月應付", `${money(d.this_month_total)} 元`),
    metric("下月預算外", `${money(unplanned)} 元`),
  ].join("") + yearLine + expiryLine;
  const cioCharts = document.querySelector("#cio-charts");
  if (cioCharts) {
    const planSeg = [
      { label: "計畫內（有預算）", value: planned, color: CHART_COLORS[1], text: `${money(planned)} 元` },
      { label: "預算外（無對應預算）", value: unplanned, color: CHART_COLORS[3], text: `${money(unplanned)} 元` },
    ];
    // 現金流用付款排程的預計（planned_forecast）——預計未付才是未來要出的錢；沒有排程時退回舊口徑
    const flowSrc = (d.planned_forecast && d.planned_forecast.length) ? d.planned_forecast : (d.forecast || []);
    const flow = flowSrc.map((f, i) => ({ label: f.month.slice(5), value: f.total || 0, color: i === 0 ? CHART_COLORS[6] : CHART_COLORS[0] }));
    cioCharts.innerHTML =
      chartCard("下月支出：計畫內 vs 預算外", donutSVG(planSeg, { center: unplanned > 0 ? "留意" : "OK" }) + chartLegend(planSeg)) +
      chartCard("未來 6 個月預計付款現金流", flow.length ? barsSVG(flow, { width: 340 }) : `<p class="muted">尚無資料</p>`);
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
      .join("") || `<li class="muted">無關聯費用</li>`;
    const projects = (d.projects || [])
      .map((p) => `<li><strong>${escapeHtml(p.project_code)}</strong> ${escapeHtml(p.project_name || "")} ｜ 進度 ${Number(p.progress || 0)}% ｜ ${escapeHtml(labelStatus(p.status))}</li>`)
      .join("") || `<li class="muted">無關聯專案</li>`;
    cioDrill.innerHTML = `
      <div class="section-heading compact">
        <h2>追查：${escapeHtml(c.case_code || "")}　${escapeHtml(c.title || "")}</h2>
        <button type="button" class="secondary" id="cio-drill-close">收起</button>
      </div>
      <div class="metrics">
        ${metric("承辦", escapeHtml(c.owner || "未指派"))}
        ${metric("狀態", escapeHtml(labelStatus(c.status || "")))}
        ${metric("付款合計", `${money((d.totals || {}).payment_amount)} 元`)}
      </div>
      <h3>對應預算</h3><ul class="note-list">${budgets}</ul>
      <h3>對應專案</h3><ul class="note-list">${projects}</ul>
      <h3>對應簽呈</h3><ul class="note-list">${signoffs}</ul>
      <h3>對應費用</h3><ul class="note-list">${purchases}</ul>
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
    const kind = { case: "案件", project: "專案", project_item: "工作項", contract: "合約" }[i.type] || i.type;
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
  const canApprove = isReviewer(currentUser);
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
            <small>承辦：${escapeHtml(c.owner || "未指派")}｜建立者：${escapeHtml(valueOrDash(c.created_by))}</small>
            <button type="button" data-action="approve-pending">核准</button>
          </li>`)
        .join("")
    : `<li><small class="muted">目前沒有等你複核的案件。</small></li>`;
}

async function loadOrphanPayments() {
  const el = document.querySelector("#orphan-payments-list");
  const wrap = document.querySelector("#orphan-payments");
  if (!el || !wrap) return;
  if (!isReviewer(currentUser)) { wrap.hidden = true; return; }   // 未歸戶付款＝主管層要處理的
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
  for (const k of ["smtp_host", "smtp_port", "smtp_user", "smtp_from", "email_map", "notify_enabled", "contract_system_url"]) {
    if (form.elements[k]) form.elements[k].value = s[k] ?? "";
  }
  if (form.elements.smtp_password) form.elements.smtp_password.placeholder = s.smtp_password_set ? "已設定（留空＝不變更）" : "SMTP 密碼（留空＝不變更）";
  const resetWrap = document.querySelector("#admin-db-reset-wrap");
  if (resetWrap) resetWrap.hidden = !s.allow_db_reset;
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
  // 管轄組別下拉（組長才需要）：選項跟人員主檔同一份可維護清單
  const groupSel = document.querySelector("#admin-user-group");
  if (groupSel) {
    const cur = groupSel.value;
    groupSel.innerHTML = `<option value="">管轄組別（組長才需要）</option>`
      + (d.groups || []).map((g) => `<option value="${escapeHtml(g)}">${escapeHtml(g)}</option>`).join("");
    if (cur) groupSel.value = cur;
  }
  body.innerHTML = (d.users || [])
    .map((u) => {
      const state = u.builtin
        ? '<span class="badge">內建</span>'
        : u.disabled
        ? '<span class="badge danger">已停用</span>'
        : '<span class="badge ok">啟用</span>';
      // 組長沒指派組別＝只看得到自己的案（保守預設），標出來提醒管理員去補
      const isLeader = u.role_code === "group_leader";
      const group = u.group_name
        ? escapeHtml(u.group_name)
        : isLeader ? '<span class="badge warn">未指派</span>' : '<span class="muted">—</span>';
      const groupBtn = (!u.builtin && isLeader)
        ? ` <button type="button" class="secondary" data-uaction="group" data-username="${escapeHtml(u.username)}">改組別</button>` : "";
      const actions = u.builtin
        ? '<span class="muted">—</span>'
        : `<button type="button" class="secondary" data-uaction="${u.disabled ? "enable" : "disable"}" data-username="${escapeHtml(u.username)}">${u.disabled ? "啟用" : "停用"}</button>
           <button type="button" class="secondary" data-uaction="reset" data-username="${escapeHtml(u.username)}">改密碼</button>${groupBtn}
           <button type="button" class="danger" data-uaction="delete" data-username="${escapeHtml(u.username)}">刪除</button>`;
      return `<tr><td>${escapeHtml(u.username)}</td><td>${escapeHtml(u.role_name)}</td><td>${group}</td><td>${escapeHtml(valueOrDash(u.display_name))}</td><td>${escapeHtml(valueOrDash(u.email))}</td><td>${state}</td><td>${actions}</td></tr>`;
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
    contractSystemUrl = o.contract_system_url || "";  // 合約系統連結樣板（後台可維護，空＝不顯示連結）
    personnelGroupOptions = o.person_groups || [];   // 人員組別選項（後台可維護）
    populatePersonnelGroupSelects();
    // 地點／機房（可複選）：機房會增減改名，選項由後台維護，不寫死在前端
    for (const sel of document.querySelectorAll(".contract-location-picker")) {
      const picked = [...sel.selectedOptions].map((o) => o.value);
      sel.innerHTML = (o.contract_locations || [])
        .map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");
      for (const opt of sel.options) opt.selected = picked.includes(opt.value);
    }
    // 合約類型是 select（不是 datalist）：保留「未分類」預設項，其餘由後台選項維護
    for (const sel of document.querySelectorAll(".contract-type-picker")) {
      const cur = sel.value;
      sel.innerHTML = `<option value="">（未分類）合約類型</option>`
        + (o.contract_type || []).map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");
      if (cur) sel.value = cur;
    }
  } catch (error) {
    /* 選項載入失敗不影響主流程 */
  }
}

// 主管儀表板三張卡（助理 2026-08-03 回饋：主管要的是「今天要處理什麼」，
// 不是各模組的統計報表——月度支出、單位別預算那些已移回各自模組）。
// 點卡片在下方展開明細，不用切到別的模組去找。
let managerFocusData = null;
let managerFocusOpen = null;

async function loadManagerFocus() {
  const el = document.querySelector("#manager-focus");
  if (!el) return;
  try {
    managerFocusData = (await api("/api/reports/manager-focus")).data || null;
  } catch (error) {
    el.innerHTML = `<p class="muted">載入失敗：${escapeHtml(error.message)}</p>`;
    return;
  }
  const d = managerFocusData;
  const card = (key, num, label, hint, tone) => `
    <button type="button" class="focus-card${tone ? " " + tone : ""}${managerFocusOpen === key ? " open" : ""}"
            data-focus="${key}" aria-expanded="${managerFocusOpen === key}">
      <span class="focus-num">${num}</span>
      <span class="focus-label">${label}</span>
      <span class="focus-hint">${hint}</span>
    </button>`;
  el.innerHTML = [
    card("new", d.new_cases.count, "本月新成立案件", `${d.this_month}　點看明細`, ""),
    card("risk", d.at_risk.count, "已逾期合約／已延遲專案",
         `合約 ${d.at_risk.overdue_contracts.length}　專案 ${d.at_risk.delayed_projects.length}`,
         d.at_risk.count ? "danger" : ""),
    card("pay", `${money(d.next_month_payment.total)}`, "下個月應付款",
         `${d.next_month}　${d.next_month_payment.items.length} 筆`, ""),
  ].join("");
  renderManagerFocusDetail();
}

function renderManagerFocusDetail() {
  const box = document.querySelector("#manager-focus-detail");
  if (!box) return;
  const d = managerFocusData;
  if (!d || !managerFocusOpen) { box.hidden = true; box.innerHTML = ""; return; }
  const rows = (items, cols, empty) => items.length
    ? `<div class="table-shell"><table><thead><tr>${cols.map((c) => `<th${c.num ? ' class="num"' : ""}>${c.label}</th>`).join("")}</tr></thead>`
      + `<tbody>${items.map((it) => `<tr${it.case_id ? ` data-case-id="${it.case_id}"` : ""}>`
          + cols.map((c) => `<td${c.num ? ' class="num"' : ""}>${c.cell(it)}</td>`).join("") + `</tr>`).join("")}</tbody></table></div>`
    : `<p class="muted">${empty}</p>`;
  let title = "", body = "";
  if (managerFocusOpen === "new") {
    title = `本月新成立案件（${d.this_month}）`;
    body = rows(d.new_cases.items, [
      { label: "案號", cell: (i) => caseNumberCell(i) },
      { label: "案件名稱", cell: (i) => escapeHtml(i.title) },
      { label: "負責人", cell: (i) => escapeHtml(valueOrDash(i.owner)) },
      { label: "金額", num: true, cell: (i) => money(i.amount) },
      { label: "成立時間", cell: (i) => escapeHtml(String(i.established_at || "").slice(0, 16)) },
    ], "本月還沒有新成立的案件。");
  } else if (managerFocusOpen === "risk") {
    title = "已逾期合約／已延遲專案";
    body = `<h4>合約已過到期日</h4>` + rows(d.at_risk.overdue_contracts, [
      { label: "合約編號", cell: (i) => `<strong>${escapeHtml(i.contract_code)}</strong>` },
      { label: "合約名稱", cell: (i) => escapeHtml(i.contract_name || "") },
      { label: "廠商", cell: (i) => escapeHtml(valueOrDash(i.vendor_name)) },
      { label: "到期日", cell: (i) => `<span class="overdue">${escapeHtml(i.end_date)}</span>` },
      { label: "金額", num: true, cell: (i) => money(i.amount) },
    ], "沒有逾期合約。")
    + `<h4>專案過了結束日還沒完成</h4>` + rows(d.at_risk.delayed_projects, [
      { label: "專案", cell: (i) => `<strong>${escapeHtml(i.project_name || i.project_code)}</strong>` },
      { label: "負責人", cell: (i) => escapeHtml(valueOrDash(i.owner)) },
      { label: "結束日", cell: (i) => `<span class="overdue">${escapeHtml(i.end_date)}</span>` },
      { label: "完成度", num: true, cell: (i) => `${Number(i.progress || 0)}%` },
    ], "沒有延遲的專案。");
  } else {
    title = `下個月應付款（${d.next_month}）`;
    body = rows(d.next_month_payment.items, [
      { label: "合約", cell: (i) => escapeHtml(i.contract_code || "—") },
      { label: "項目", cell: (i) => escapeHtml(valueOrDash(i.item)) },
      { label: "廠商", cell: (i) => escapeHtml(valueOrDash(i.vendor)) },
      { label: "金額", num: true, cell: (i) => money(i.payment_amount) },
      { label: "狀態", cell: (i) => statusChip(i.status) },
    ], "下個月沒有要付的款。");
  }
  box.hidden = false;
  box.innerHTML = `<div class="section-heading compact"><h2>${escapeHtml(title)}</h2>`
    + `<button type="button" class="secondary btn-sm" data-focus-close>收起</button></div>${body}`;
}

// 待辦事項四張卡（助理 2026-08-03 回饋）：資料範圍後端已依角色收斂，
// 這裡只決定「這個角色要看哪幾張」——承辦沒有審核權就不給他看待審核。
let todoCardsData = null;
let todoCardsOpen = null;

function todoCardSet() {
  const role = (currentUser && currentUser.role_code) || "";
  const first = role === "group_leader" || role === "manager_assistant"
    ? "pending"                                   // 組長/助理：組內待審核
    : (role === "department_head" || role === "cio" ? "approved" : null);  // 部長/副總：本月新核准
  return [first, "contract", "wbs", "settle"].filter(Boolean);
}

async function loadTodoCards() {
  const el = document.querySelector("#todo-cards");
  if (!el) return;
  try {
    todoCardsData = (await api("/api/reports/todo-cards")).data || null;
  } catch (error) {
    el.innerHTML = `<p class="muted">載入失敗：${escapeHtml(error.message)}</p>`;
    return;
  }
  const d = todoCardsData;
  const meta = {
    pending: { num: d.pending_review.count, label: "待我審核的新案申請", hint: "組內送上來、等你核准的案件",
               tone: d.pending_review.count ? "danger" : "" },
    approved: { num: d.new_approved.count, label: "本月新核准案件", hint: `${d.this_month}　點看明細`, tone: "" },
    contract: { num: d.contracts_expiring.count, label: "合約到期提醒", hint: `${d.contracts_expiring.window}到期`,
                tone: d.contracts_expiring.count ? "danger" : "" },
    wbs: { num: d.wbs_due.count, label: "WBS 到期提醒",
           hint: d.wbs_due.overdue ? `${d.wbs_due.window}到期，其中 ${d.wbs_due.overdue} 項已逾期` : `${d.wbs_due.window}到期未完成`,
           tone: d.wbs_due.overdue ? "danger" : "" },
    settle: { num: d.settlements.count, label: "費用核銷提醒", hint: `${d.this_month}　共 ${money(d.settlements.total)} 元`, tone: "" },
  };
  el.innerHTML = todoCardSet().map((k) => {
    const m = meta[k];
    return `<button type="button" class="focus-card${m.tone ? " " + m.tone : ""}${todoCardsOpen === k ? " open" : ""}"
      data-todo-card="${k}" aria-expanded="${todoCardsOpen === k}">
      <span class="focus-num">${m.num}</span><span class="focus-label">${m.label}</span>
      <span class="focus-hint">${m.hint}</span></button>`;
  }).join("");
  renderTodoCardDetail();
}

function renderTodoCardDetail() {
  const box = document.querySelector("#todo-cards-detail");
  if (!box) return;
  const d = todoCardsData;
  if (!d || !todoCardsOpen) { box.hidden = true; box.innerHTML = ""; return; }
  const today = new Date().toISOString().slice(0, 10);
  const table = (items, cols, empty) => items.length
    ? `<div class="table-shell"><table><thead><tr>${cols.map((c) => `<th${c.num ? ' class="num"' : ""}>${c.label}</th>`).join("")}</tr></thead>`
      + `<tbody>${items.map((it) => `<tr${it.case_id ? ` data-case-id="${it.case_id}"` : (it.id && cols.linkCase ? ` data-case-id="${it.id}"` : "")}>`
          + cols.map((c) => `<td${c.num ? ' class="num"' : ""}>${c.cell(it)}</td>`).join("") + "</tr>").join("")}</tbody></table></div>`
    : `<p class="muted">${empty}</p>`;
  const dateCell = (v) => `<span class="${String(v) < today ? "overdue" : ""}">${escapeHtml(String(v || ""))}</span>`;
  let title = "", body = "";
  if (todoCardsOpen === "pending") {
    title = "待我審核的新案申請";
    const cols = [
      { label: "暫時號", cell: (i) => `<strong>${escapeHtml(caseTempNumber(i) || i.case_code)}</strong>` },
      { label: "案件名稱", cell: (i) => escapeHtml(i.title) },
      { label: "負責人", cell: (i) => escapeHtml(valueOrDash(i.owner)) },
      { label: "金額", num: true, cell: (i) => money(i.amount) },
      { label: "提出人", cell: (i) => escapeHtml(valueOrDash(i.created_by)) },
    ];
    cols.linkCase = true;
    body = table(d.pending_review.items, cols, "目前沒有等你審核的案件。");
  } else if (todoCardsOpen === "approved") {
    title = `本月新核准案件（${d.this_month}）`;
    const cols = [
      { label: "案號", cell: (i) => caseNumberCell(i) },
      { label: "案件名稱", cell: (i) => escapeHtml(i.title) },
      { label: "負責人", cell: (i) => escapeHtml(valueOrDash(i.owner)) },
      { label: "金額", num: true, cell: (i) => money(i.amount) },
      { label: "核准時間", cell: (i) => escapeHtml(String(i.established_at || "").slice(0, 16)) },
    ];
    cols.linkCase = true;
    body = table(d.new_approved.items, cols, "本月還沒有新核准的案件。");
  } else if (todoCardsOpen === "contract") {
    title = `合約到期提醒（${d.contracts_expiring.window}）`;
    body = table(d.contracts_expiring.items, [
      { label: "合約編號", cell: (i) => `<strong>${escapeHtml(i.contract_code)}</strong>${contractSystemLink(i.contract_code)}` },
      { label: "合約名稱", cell: (i) => escapeHtml(i.contract_name || "") },
      { label: "廠商", cell: (i) => escapeHtml(valueOrDash(i.vendor_name)) },
      { label: "到期日", cell: (i) => dateCell(i.end_date) },
      { label: "金額", num: true, cell: (i) => money(i.amount) },
    ], "三個月內沒有到期的合約。");
  } else if (todoCardsOpen === "wbs") {
    title = `WBS 到期提醒（${d.wbs_due.window}）`;
    body = table(d.wbs_due.items, [
      { label: "工作項目", cell: (i) => `<strong>${escapeHtml(i.item_name || "")}</strong>` },
      { label: "所屬專案", cell: (i) => escapeHtml(valueOrDash(i.project_name)) },
      { label: "負責人", cell: (i) => escapeHtml(valueOrDash(i.owner)) },
      { label: "結束日", cell: (i) => dateCell(i.end_date) },
      { label: "完成度", num: true, cell: (i) => `${Number(i.progress || 0)}%` },
    ], "兩週內沒有要完成的工作項。");
  } else {
    title = `費用核銷提醒（${d.this_month}）`;
    body = table(d.settlements.items, [
      { label: "核銷編號", cell: (i) => escapeHtml(valueOrDash(i.settle_no)) },
      { label: "合約", cell: (i) => escapeHtml(i.contract_code || "—") },
      { label: "項目", cell: (i) => escapeHtml(valueOrDash(i.item)) },
      { label: "廠商", cell: (i) => escapeHtml(valueOrDash(i.vendor)) },
      { label: "金額", num: true, cell: (i) => money(i.payment_amount) },
      { label: "狀態", cell: (i) => statusChip(i.status) },
    ], "本月沒有要辦理的核銷。");
  }
  box.hidden = false;
  box.innerHTML = `<div class="section-heading compact"><h2>${escapeHtml(title)}</h2>`
    + `<button type="button" class="secondary btn-sm" data-todo-close>收起</button></div>${body}`;
}

document.querySelector("#todo-cards")?.addEventListener("click", (event) => {
  const btn = event.target.closest("[data-todo-card]");
  if (!btn) return;
  const key = btn.getAttribute("data-todo-card");
  todoCardsOpen = todoCardsOpen === key ? null : key;
  loadTodoCards();
});

document.querySelector("#todo-cards-detail")?.addEventListener("click", (event) => {
  if (event.target.closest("[data-todo-close]")) { todoCardsOpen = null; loadTodoCards(); return; }
  const tr = event.target.closest("tr[data-case-id]");
  if (tr) openCaseFromOverview(tr.getAttribute("data-case-id"));
});

document.querySelector("#manager-focus")?.addEventListener("click", (event) => {
  const btn = event.target.closest("[data-focus]");
  if (!btn) return;
  const key = btn.getAttribute("data-focus");
  managerFocusOpen = managerFocusOpen === key ? null : key;   // 再點一次收起
  loadManagerFocus();
});

document.querySelector("#manager-focus-detail")?.addEventListener("click", (event) => {
  if (event.target.closest("[data-focus-close]")) {
    managerFocusOpen = null;
    loadManagerFocus();
    return;
  }
  const tr = event.target.closest("tr[data-case-id]");
  if (tr) openCaseFromOverview(tr.getAttribute("data-case-id"));
});

async function refresh() {
  // 選項要先到再畫清單：合約清單的「🔗 合約系統」連結是用後台設定的網址組出來的，
  // 跟其他載入平行跑的話，清單常常先畫完、連結就整批不見（改設定後也要重進才會出現）。
  await loadOptions();
  await Promise.all([
    loadDashboard(), loadCases(), loadContracts(), loadPayments(), loadDocuments(),
    loadResource("budget"), loadResource("project"), loadResource("signoff"), loadResource("purchase"),
    loadMappingCatalog(), loadTodo(), loadMonthly(), loadUnitBva(), loadVendorAmt(), loadExpiring(), loadCioOverview(), loadReminders(),
    loadManagerFocus(), loadTodoCards(), loadCaseProgress(), loadPendingApprovals(), loadOrphanPayments(), loadAdminConsole(),
    loadPortfolio(), loadUnitConflicts(), loadPersonnelMaster(), loadCaseOptions(), loadWorkingYear(),
    loadSignoffOptions(), loadPurchaseOptions(), loadParentContractOptions(),
    loadMonthlyStatus(),
  ]);
  // 組別下拉沿用人員組別那份選項（處長預設看全部，要拆組別時才用）
  const msGroup = document.querySelector("#monthly-status-group");
  if (msGroup && msGroup.options.length <= 1) {
    msGroup.innerHTML = `<option value="">全部組別</option>`
      + (personnelGroupOptions || []).map((g) => `<option value="${escapeHtml(g)}">${escapeHtml(g)}</option>`).join("");
  }
  // 費用主檔的清單與「關聯合約」下拉都要等合約載完才畫得出來（合約編號要從快取查）
  await Promise.all([loadExpenses(), loadExpenseContractOptions()]);
}

// 進度總表：組別 tab / 子 tab / 由總覽點列進單一專案
document.querySelector("#pf-groups")?.addEventListener("click", (event) => {
  const t = event.target.closest("[data-pf-g]");
  if (!t) return;
  portfolioState.g = Number(t.getAttribute("data-pf-g"));
  portfolioState.s = "ov";
  portfolioState.f = null;  // 換組別＝重置篩選，各組計數不同，帶著舊篩選會誤導
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
  // 六格統計列：點格過濾，點同一格（或「全部」）取消。先處理，因為它跟專案列同在此容器。
  const filterBtn = event.target.closest("[data-pf-filter]");
  if (filterBtn) {
    const v = filterBtn.getAttribute("data-pf-filter");
    const tone = v || null;
    portfolioState.f = (portfolioState.f === tone) ? null : tone;  // 再點一次同格＝取消
    renderPortfolio();
    return;
  }
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
  form.elements.status.value = item.status || "draft";
  // 助理回饋後的欄位組合：備註/下一步/日期已從表單移除，這裡用 optional chaining 保護，
  // 舊資料的值仍留在 DB（沒有被清掉），只是畫面不再顯示。
  if (form.elements.note) form.elements.note.value = item.note || "";
  if (form.elements.next_step) form.elements.next_step.value = item.next_step || "";
  if (form.elements.due_date) form.elements.due_date.value = item.due_date || "";
  for (const f of ["group_name", "budget_type", "expense_kind", "budget_item", "source", "description"]) {
    if (form.elements[f]) form.elements[f].value = item[f] || "";
  }
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
  // 可複選欄位（合約的地點／機房）：FormData 每個選項各一筆，Object.fromEntries 只會留最後一個，
  // 選了三個機房會只存到一個。改用 getAll 併成逗號分隔（後端就是這樣存）。
  for (const sel of targetForm.querySelectorAll("select[multiple][name]")) {
    data[sel.name] = new FormData(targetForm).getAll(sel.name).join(",");
  }
  // 勾選欄位：沒勾的 FormData 根本不會帶這個 key，PATCH 就永遠取消不掉（只能從 0 改成 1）。
  // 一律明確送 1/0。
  for (const cb of targetForm.querySelectorAll('input[type="checkbox"][name]')) {
    data[cb.name] = cb.checked ? 1 : 0;
  }
  for (const field of config.numberFields) {
    // _id 結尾＝可為空的關聯外鍵，留空要送 null（不能送 0，0 不是合法的關聯目標）；
    // 其餘（金額/進度/數量…）留空視同 0，避免後端 float 欄位收到 null 報 422。
    const isFk = field.endsWith("_id");
    data[field] = data[field] === "" ? (isFk ? null : 0) : Number(data[field]);
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
  // 合約：來源合約下拉要把「正在編輯的這份」拿掉（自己不能是自己的續約來源）。
  // 必須在下面填值之前重建選項，否則剛設好的 parent_contract_id 會被清掉。
  if (type === "contract") await loadParentContractOptions();
  if (type === "contract") setTimeout(refreshAddonGate, 0);   // 值填完再判斷（下面才 set case_id）
  for (const field of config.fields) {
    const el = targetForm.elements[field];
    const val = item[field] ?? "";
    // select 若沒有這個值的選項（例如舊資料的單位名稱還沒登記進主檔），先補一個選項，
    // 避免編輯時看起來「值不見了」、存檔時被誤蓋成空白
    if (el.type === "checkbox") {
      el.checked = String(val) === "1" || val === true;
      continue;
    }
    if (el.tagName === "SELECT" && el.multiple) {
      // 逗號分隔存、多選顯示：把存的字串拆回去逐項打勾（選項還沒登記的先補上，免得看起來值不見了）
      const picked = String(val).split(",").map((v) => v.trim()).filter(Boolean);
      for (const v of picked) {
        if (![...el.options].some((o) => o.value === v)) el.add(new Option(`${v}（未登記）`, v));
      }
      for (const opt of el.options) opt.selected = picked.includes(opt.value);
      continue;
    }
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
  // 案件編號改由系統產生：留空就別送（新增時後端自動配，編輯時不動原本的號）
  if (!String(data.case_code || "").trim()) delete data.case_code;
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

// 合約盤點表匯入（黃助理 0813）：預覽→正式匯入。以合約編號為識別鍵，重匯會更新不新增。
async function contractXlsx(commit) {
  const file = document.querySelector("#contract-xlsx-file")?.files?.[0];
  const el = document.querySelector("#contract-xlsx-status");
  const commitBtn = document.querySelector("#contract-xlsx-commit");
  if (!file) { if (el) el.textContent = "請先選一個 .xlsx 檔"; return; }
  if (commit && !window.confirm("確定正式匯入？同編號的合約會更新、沒見過的會新增。")) return;
  if (el) el.textContent = commit ? "匯入中…" : "解析中…";
  try {
    const res = (await api(`/api/contracts/import-xlsx?commit=${commit}`,
                           { method: "POST", body: file })).data || {};
    if (commit) {
      const bits = [`新增 ${res.created_count} 筆、更新 ${res.updated_count} 筆`];
      if (res.linked_count) bits.push(`接起 ${res.linked_count} 組續約／整併關係`);
      if (res.skipped_count) bits.push(`略過 ${res.skipped_count} 筆`);
      if ((res.handover_hints || []).length) {
        bits.push(`另有 ${res.handover_hints.length} 筆標了原維護人（離職／異動），`
          + `可到「人員管理›離職交接」處理`);
      }
      if (el) el.textContent = `匯入完成：${bits.join("；")}。`;
      await refresh();
    } else {
      const warn = [];
      if (res.unconfirmed) warn.push(`其中 ${res.unconfirmed} 筆還沒填「已確認完成」`);
      if (res.relation_hints) warn.push(`可自動接起 ${res.relation_hints} 組合約關係`);
      if (res.handover_hints) warn.push(`${res.handover_hints} 筆有原維護人`);
      if (el) {
        el.textContent = res.count
          ? `預覽：共 ${res.count} 筆合約${warn.length ? "（" + warn.join("、") + "）" : ""}`
          : "共 0 筆——這個檔不像合約盤點表，請確認工作表裡有「合約編號」欄。";
      }
      if (commitBtn) commitBtn.disabled = !res.count;
    }
  } catch (error) {
    if (el) el.textContent = `失敗：${error.message}`;
  }
}
document.querySelector("#contract-xlsx-preview")?.addEventListener("click", () => contractXlsx(false));
document.querySelector("#contract-xlsx-commit")?.addEventListener("click", () => contractXlsx(true));

// 人員名單匯入：預覽→正式匯入。以姓名為識別鍵，重匯會更新（空欄不覆蓋）不新增重複。
async function personnelXlsx(commit) {
  const file = document.querySelector("#personnel-xlsx-file")?.files?.[0];
  const el = document.querySelector("#personnel-xlsx-status");
  const commitBtn = document.querySelector("#personnel-xlsx-commit");
  if (!file) { if (el) el.textContent = "請先選一個 .xlsx 檔"; return; }
  if (commit && !window.confirm("確定正式匯入？同姓名的人員會更新（空欄不覆蓋既有值）、沒見過的會新增。")) return;
  if (el) el.textContent = commit ? "匯入中…" : "解析中…";
  try {
    const res = (await api(`/api/personnel-master/import-xlsx?commit=${commit}`,
                           { method: "POST", body: file })).data || {};
    if (commit) {
      if (el) el.textContent = `匯入完成：新增 ${res.created_count} 筆、更新 ${res.updated_count} 筆、略過 ${res.skipped_count} 筆（沒有新資訊可更新）。`;
      await refresh();
    } else {
      const warn = [];
      if (res.missing_email) warn.push(`${res.missing_email} 筆沒有 Email`);
      if (res.missing_group) warn.push(`${res.missing_group} 筆沒有部門`);
      if (el) {
        el.textContent = res.count
          ? `預覽：共 ${res.count} 筆${warn.length ? "（" + warn.join("、") + "）" : ""}`
          : "共 0 筆——請確認工作表裡有「姓名」欄。";
      }
      if (commitBtn) commitBtn.disabled = !res.count;
    }
  } catch (error) {
    if (el) el.textContent = `失敗：${error.message}`;
  }
}
document.querySelector("#personnel-xlsx-preview")?.addEventListener("click", () => personnelXlsx(false));
document.querySelector("#personnel-xlsx-commit")?.addEventListener("click", () => personnelXlsx(true));

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
// 預算模組內嵌的那個匯入入口已移除（2026-07-30）：匯入統一收在資料管理 / 匯入匯出，
// 不讓同一件事有兩個地方可按。budgetXlsx() 仍保留可傳 ids 的參數，之後若要再加別的
// 入口不必改函式本身。

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
    // 人工改過某一列之後合計就會跟項目金額對不上，當場講差多少（20 幾列不該讓人自己加）
    let balance = null;
    try { balance = (await api(`/api/budgets/${budgetId}/allocation-check`)).data; } catch (_e) { /* 非必要 */ }
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
          // 金額與比例都可以就地改（談定的分攤常常不是純比例，改一個另一個系統跟著算）
          const amountCell = editable
            ? `<input class="alloc-input" type="number" min="0" step="1" value="${Number(a.amount_int || 0)}"
                 data-alloc-amount="${a.id}" data-budget="${budgetId}" title="改金額，比例跟著算" />`
            : `${money(a.amount_int)} 元`;
          const pctCell = editable
            ? `<input class="alloc-input" type="number" min="0" max="100" step="0.01" value="${Number(a.share_pct || 0)}"
                 data-alloc-pct="${a.id}" data-budget="${budgetId}" title="改比例，金額跟著算" />%`
            : `${Number(a.share_pct || 0)}%`;
          return `<tr>
          <td>${escapeHtml(valueOrDash(a.unit_code))}</td>
          <td>${escapeHtml(a.unit_name)}${remTag}</td>
          <td class="num">${pctCell}</td>
          <td class="num">${amountCell}</td></tr>`;
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
      ${balance && !balance.balanced
        ? `<p class="chip todo">分攤合計 ${money(balance.allocated)} 元，與費用項目金額 ${money(balance.total)} 元`
          + ` 差 ${money(Math.abs(balance.diff))} 元（${balance.diff > 0 ? "還少" : "多"}了）——`
          + `尾數會由「尾數承擔單位」吸收，差太多請檢查是不是有一列改錯。</p>`
        : ""}
      ${editable ? `<p class="muted">分攤% 與分攤金額都可以直接改，改一個另一個會自動換算。
        人工改過之後分攤方法會鎖回「固定金額」，避免下次按重算把談好的結果洗掉。</p>` : ""}
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
  // 選項文字帶組別（同名不同組時分得出來），但存進資料的值仍是純姓名，不影響既有資料
  const rest = (personnelMasterCache || []).map((p) =>
    `<option value="${escapeHtml(p.name)}">${escapeHtml(p.group_name ? `${p.group_name}｜${p.name}` : p.name)}</option>`).join("");
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

// 人員管理（後台）：組別＋姓名可增刪改。人會轉組、會離職，所以每一列都能改組別、停用、刪除。
// 停用＝下拉選不到但歷史資料不動（那些欄位存的是名字文字）；刪除只影響「以後還選不選得到」。
let personnelGroupOptions = [];
let personnelAllCache = [];   // 含已停用（後台列表用）；personnelMasterCache 只留在職的給表單下拉
async function loadPersonnelMaster() {
  const box = document.querySelector("#personnelmaster-result");
  try {
    // 後台要看得到已停用的（才能重新啟用）；表單下拉只吃在職的
    const data = (await api("/api/personnel-master?include_disabled=true")).data || {};
    const masters = data.masters || [];
    personnelAllCache = masters;
    personnelMasterCache = masters.filter((p) => p.status !== "disabled");
    populatePersonnelSelects();
    // 通知「依組別過濾的負責人下拉」重畫（名單換了、轉組了都要跟著更新）
    document.dispatchEvent(new CustomEvent("personnel-loaded"));
    populatePersonnelGroupSelects();
    if (!box) return;
    if (!masters.length) {
      box.innerHTML = `<p class="muted">還沒有登記過人員。用上面「＋新增人員」逐筆登記，或按「載入示範名單」先放四組各三人試用。</p>`;
      return;
    }
    // 助理 2026-08-13：人員＋組別＋EMAIL 沒填好就沒辦法繼續測（通知寄不出去）。
    // 缺什麼直接列在最上面，組別與 email 都改成就地編輯，不用一個一個開編輯框。
    const gap = (data.missing_email || 0) + (data.missing_group || 0);
    const gapLine = gap
      ? `<p class="chip todo">還缺：${data.missing_email ? `<strong>${data.missing_email}</strong> 人沒有 EMAIL` : ""}${
          data.missing_email && data.missing_group ? "、" : ""}${
          data.missing_group ? `<strong>${data.missing_group}</strong> 人沒有組別` : ""}
         —— 沒有 EMAIL 的人，系統通知（催辦、核銷）寄不出去。直接在下面表格填，改完自動存。</p>`
      : `<p class="chip done">在職人員的組別與 EMAIL 都填好了，通知寄得出去。</p>`;
    // 依組別分段列出，一眼看得出哪組有幾個人
    const groups = [...new Set(masters.map((p) => p.group_name || "（未分組）"))];
    box.innerHTML = gapLine + groups.map((g) => {
      const rows = masters.filter((p) => (p.group_name || "（未分組）") === g);
      return `<div class="person-group">
        <h4>${escapeHtml(g)} <span class="muted">${rows.length} 人</span></h4>
        <div class="grid-scroll"><table class="grid-table">
          <thead><tr><th>姓名</th><th>組別</th><th>EMAIL</th><th>狀態</th><th>備註</th><th class="col-actions">操作</th></tr></thead>
          <tbody>${rows.map((p) => `<tr${p.status === "disabled" ? ' class="person-off"' : ""}>
            <td><strong>${escapeHtml(p.name)}</strong></td>
            <td><select class="cell-input" data-person-field="group_name" data-person-id="${p.id}">
                  <option value="">（未分組）</option>
                  ${(personnelGroupOptions || []).map((x) =>
                    `<option value="${escapeHtml(x)}"${x === p.group_name ? " selected" : ""}>${escapeHtml(x)}</option>`).join("")}
                  ${p.group_name && !(personnelGroupOptions || []).includes(p.group_name)
                    ? `<option value="${escapeHtml(p.group_name)}" selected>${escapeHtml(p.group_name)}</option>` : ""}
                </select></td>
            <td><input class="cell-input${String(p.email || "").trim() ? "" : " needs-fill"}" type="email"
                  data-person-field="email" data-person-id="${p.id}"
                  value="${escapeHtml(p.email || "")}" placeholder="還沒填" /></td>
            <td>${p.status === "disabled" ? '<span class="badge neutral">已停用</span>' : '<span class="badge ok">在職</span>'}</td>
            <td class="muted">${escapeHtml(valueOrDash(p.note))}</td>
            <td class="col-actions"><span class="row-actions">
              <button type="button" class="btn-sm secondary" data-person-edit="${p.id}">改</button>
              <button type="button" class="btn-sm secondary" data-person-toggle="${p.id}">${p.status === "disabled" ? "啟用" : "停用"}</button>
              <button type="button" class="btn-sm secondary danger" data-person-del="${p.id}">刪除</button>
            </span></td></tr>`).join("")}</tbody>
        </table></div></div>`;
    }).join("");
  } catch (error) {
    if (box) box.innerHTML = `<p class="muted">人員名單載入失敗：${escapeHtml(error.message)}</p>`;
  }
}

// 組別下拉：選項由後台維護（不同單位組織不一樣），並補上名單裡已出現、但選項清單還沒登記的組別
function populatePersonnelGroupSelects() {
  const used = [...new Set((personnelMasterCache || []).map((p) => p.group_name).filter(Boolean))];
  const all = [...new Set([...personnelGroupOptions, ...used])];
  for (const sel of document.querySelectorAll("select.person-group-select")) {
    const prev = sel.value;
    sel.innerHTML = `<option value="">（未分組）</option>`
      + all.map((g) => `<option value="${escapeHtml(g)}">${escapeHtml(g)}</option>`).join("");
    if (prev && [...sel.options].some((o) => o.value === prev)) sel.value = prev;
  }
}

// 組別／EMAIL 就地改，改完即存（助理要一次填二十幾個人，開編輯框太慢）
document.querySelector("#personnelmaster-result")?.addEventListener("change", async (event) => {
  const el = event.target.closest("[data-person-field]");
  if (!el) return;
  const field = el.getAttribute("data-person-field");
  el.disabled = true;
  try {
    await api(`/api/personnel-master/${el.getAttribute("data-person-id")}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [field]: el.value }),
    });
    await loadPersonnelMaster();
  } catch (e) {
    el.disabled = false;
    window.alert(`儲存失敗：${e.message}`);
  }
});

document.querySelector("#personnelmaster-result")?.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-person-edit],[data-person-toggle],[data-person-del]");
  if (!btn) return;
  const id = btn.getAttribute("data-person-edit") || btn.getAttribute("data-person-toggle") || btn.getAttribute("data-person-del");
  const person = (personnelAllCache || []).find((p) => String(p.id) === String(id));
  try {
    if (btn.hasAttribute("data-person-del")) {
      if (!window.confirm(`確定刪除「${person ? person.name : "這位人員"}」？\n已經填在案件/簽呈上的名字不會消失，只是以後下拉選不到。`)) return;
      await api(`/api/personnel-master/${id}`, { method: "DELETE" });
    } else if (btn.hasAttribute("data-person-toggle")) {
      const next = person && person.status === "disabled" ? "active" : "disabled";
      await api(`/api/personnel-master/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: next }) });
    } else {
      const name = window.prompt("姓名：", person ? person.name : "");
      if (name === null) return;
      const group = window.prompt("組別（留空＝未分組）：", person ? person.group_name : "");
      if (group === null) return;
      await api(`/api/personnel-master/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), group_name: group.trim() }) });
    }
    await loadPersonnelMaster();
  } catch (error) { window.alert(error.message); }
});

document.querySelector("#personnel-seed-demo")?.addEventListener("click", async () => {
  const statusEl = document.querySelector("#personnel-create-status");
  if (!window.confirm("載入示範名單（四組各三人，備註會標「示範資料」）？同名的會跳過。")) return;
  try {
    const res = (await api("/api/personnel-master/seed-demo", { method: "POST" })).data || {};
    if (statusEl) statusEl.textContent = `已新增 ${res.created_count} 人${res.skipped_count ? `，跳過 ${res.skipped_count} 位同名` : ""}`;
    await loadPersonnelMaster();
  } catch (error) {
    if (statusEl) statusEl.textContent = `失敗：${error.message}`;
  }
});

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

// 整個資料庫重置（測試用危險鈕）：比照後端一樣只在 ALLOW_DB_RESET 開著時看得到按鈕；
// 動作不可逆（雖然後端有自動備份），要求手動打字確認，不是按一下就送出。
document.querySelector("#admin-db-reset")?.addEventListener("click", async () => {
  if (!window.confirm("整個資料庫重置：會清空所有案件/合約/預算/專案/簽呈/費用/付款…全部資料，只留空白結構。\n會自動先備份一份到 data/reset_backups/ 才清空，但這是測試用的危險操作，正式資料請勿使用。確定要繼續嗎？")) return;
  const typed = window.prompt('請輸入「RESET」以確認執行（防止手滑）：');
  if (typed !== "RESET") { window.alert("已取消（輸入不符）。"); return; }
  try {
    const r = (await api("/api/admin/db-reset", { method: "POST" })).data || {};
    window.alert(`已重置：清空 ${r.tables_cleared} 張表。備份存在：${r.backup_path || "（原本沒有 db 檔可備份）"}`);
    await refresh();
  } catch (error) {
    window.alert(`重置失敗：${error.message}`);
  }
});

// 清空業務資料（保留部門/人員/帳號/設定）：單機各自使用，不用開 .env 開關，
// 靠打字「ClearALL」（大小寫一致）當確認閘門；後端會先自動備份整個資料庫才清空。
document.querySelector("#admin-clear-all")?.addEventListener("click", async () => {
  if (!window.confirm("清空業務資料：會清掉案件/合約/預算/專案/簽呈/費用/付款/文件…所有業務資料。\n會保留部門、人員主檔、帳號與系統設定；會自動先備份整個資料庫到 data/clear_backups/ 才清空。確定要繼續嗎？")) return;
  const typed = window.prompt('請輸入「ClearALL」以確認執行（大小寫需一致，防止手滑）：');
  if (typed !== "ClearALL") { window.alert("已取消（輸入不符）。"); return; }
  try {
    const r = (await api("/api/admin/clear-all", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm: typed }),
    })).data || {};
    window.alert(`已清空 ${r.cleared_count} 張表（保留部門/人員/帳號/設定）。備份存在：${r.backup_path || "（原本沒有 db 檔可備份）"}`);
    await refresh();
  } catch (error) {
    window.alert(`清空失敗：${error.message}`);
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

// ── 每月支出狀態（使用者 2026-08-12：處長不要核決門檻，他要看每個月支出）──────
// 既有的「月度支出彙總」只算已登錄的核銷＝只看得到已經發生的錢。處長要掌握的是
// 「這個月還要付多少、下個月要準備多少」，所以預計與實際擺在同一張表比對。
async function loadMonthlyStatus() {
  const box = document.querySelector("#monthly-status-box");
  if (!box) return;
  const group = document.querySelector("#monthly-status-group")?.value || "";
  box.innerHTML = `<p class="muted">計算中…</p>`;
  try {
    const d = (await api(`/api/reports/monthly-status?group_name=${encodeURIComponent(group)}`)).data;
    const rows = d.months || [];
    const peak = Math.max(1, ...rows.map((r) => Math.max(r.planned, r.paid + r.unpaid)));
    box.innerHTML = `
      <p class="muted">${escapeHtml(d.note || "")}</p>
      <p>未來要準備的錢合計 <strong>${money(d.ahead_total)}</strong> 元</p>
      <div class="grid-scroll"><table class="grid-table">
        <thead><tr><th>月份</th><th class="num">預計應付</th><th class="num">實際已付</th>
        <th class="num">待付</th><th class="num">差異</th><th>相對規模</th></tr></thead>
        <tbody>${rows.map((r) => {
          const actual = r.paid + r.unpaid;
          const tag = r.is_current ? ' <span class="badge">本月</span>'
                    : r.is_past ? "" : ' <span class="muted">未到期</span>';
          // 過去月份才談「準不準」；未來月份還沒發生，差異沒有意義
          const diff = r.is_past && r.planned
            ? `<span class="${r.diff > 0 ? "owe" : "paid"}">${r.diff > 0 ? "超出" : "低於"} ${money(Math.abs(r.diff))}</span>`
            : '<span class="muted">—</span>';
          return `<tr class="${r.is_current ? "sched-paid" : ""}">
            <td>${escapeHtml(r.month)}${tag}</td>
            <td class="num">${r.planned ? money(r.planned) : '<span class="muted">—</span>'}</td>
            <td class="num">${r.paid ? money(r.paid) : '<span class="muted">—</span>'}</td>
            <td class="num">${r.unpaid ? `<b class="owe">${money(r.unpaid)}</b>` : '<span class="muted">—</span>'}</td>
            <td class="num">${diff}</td>
            <td><span class="ms-bar" title="預計 ${money(r.planned)}／實際 ${money(actual)}">
              <i class="ms-plan" style="width:${Math.round(r.planned / peak * 100)}%"></i>
              <i class="ms-actual" style="width:${Math.round(actual / peak * 100)}%"></i>
            </span></td></tr>`;
        }).join("")}</tbody>
      </table></div>`;
  } catch (e) {
    box.innerHTML = `<p class="muted">載入失敗：${escapeHtml(e.message)}</p>`;
  }
}

document.querySelector("#monthly-status-group")?.addEventListener("change", loadMonthlyStatus);

// ── 人員盤點與離職交接（使用者 2026-08-12）──────────────────────────────
// 先看得到每個人名下有什麼，交接才不是盲的。案件比對登入帳號、其他模組比對人名，
// 這兩種差異在後端處理，前端只呈現結果。
async function loadWorkload() {
  const box = document.querySelector("#workload-result");
  if (!box) return;
  box.innerHTML = `<p class="muted">盤點中…</p>`;
  try {
    const data = (await api("/api/personnel-workload")).data || {};
    const people = (data.people || []).filter((p) => p.total > 0 || p.status !== "disabled");
    if (!people.length) {
      box.innerHTML = `<p class="muted">人員名單是空的，先在上面新增人員。</p>`;
      return;
    }
    const unreg = data.not_in_master || 0;
    box.innerHTML = `<p class="muted">「還在跑」不含已結案／已停用的；${escapeHtml(data.unassigned_hint || "")}</p>
      ${unreg ? `<p class="chip todo">有 <strong>${unreg}</strong> 個人出現在資料裡但沒登記在人員主檔
        —— 沒登記的話，各表單的負責人下拉選不到他們，只能手打。
        <button type="button" class="btn-sm" id="personnel-suggest-open">從資料補登記</button></p>` : ""}
      <div id="personnel-suggest-box" class="schedule-panel" hidden></div>
      <div class="grid-scroll"><table class="grid-table">
        <thead><tr><th>姓名</th><th>組別</th><th>登入帳號</th><th class="num">還在跑</th>
        <th class="num">已結案</th><th>分布</th><th class="col-actions">操作</th></tr></thead>
        <tbody>${people.map((p) => `<tr>
          <td><strong>${escapeHtml(p.name)}</strong>${p.status === "disabled" ? ' <span class="badge">已停用</span>' : ""}${
            p.in_master === false ? ' <span class="badge warn" title="這個人有資料但沒登記在人員主檔，建議補登記">未登記</span>' : ""}</td>
          <td>${escapeHtml(valueOrDash(p.group_name))}</td>
          <td>${p.username ? escapeHtml(p.username) : '<span class="muted" title="沒有登入帳號的人，案件那一塊一定是 0">—</span>'}</td>
          <td class="num"><strong>${p.active}</strong></td>
          <td class="num muted">${p.closed}</td>
          <td>${Object.entries(p.blocks || {}).map(([k, v]) =>
                `<span class="badge">${escapeHtml(k)} ${v}</span>`).join(" ") || '<span class="muted">—</span>'}</td>
          <td>${p.total
            ? `<button type="button" class="secondary btn-sm" data-handover="${escapeHtml(p.name)}"
                 data-username="${escapeHtml(p.username || "")}">離職交接</button>`
            : '<span class="muted">名下沒有資料</span>'}</td>
        </tr>`).join("")}</tbody></table></div>`;
  } catch (e) {
    box.innerHTML = `<p class="muted">盤點失敗：${escapeHtml(e.message)}</p>`;
  }
}

// 從既有資料補登記人員：先列候選讓人看過再建。可疑的（一格塞多人、看起來像備註）不預設勾選。
async function openPersonnelSuggest() {
  const box = document.querySelector("#personnel-suggest-box");
  if (!box) return;
  box.hidden = false;
  box.innerHTML = `<p class="muted">掃描中…</p>`;
  try {
    const data = (await api("/api/personnel-suggest")).data || {};
    const cands = data.candidates || [];
    if (!cands.length) {
      box.innerHTML = `<p class="muted">沒有待補登記的人。</p>`;
      return;
    }
    box.innerHTML = `
      <div class="sched-head">
        <h3>從既有資料補登記人員<span class="muted">　找到 ${cands.length} 個，建議勾選 ${data.recommended} 個</span></h3>
        <button type="button" class="secondary btn-sm" data-suggest-close>收合</button>
      </div>
      <p class="muted">${escapeHtml(data.note || "")}</p>
      <form data-suggest-form>
        <div class="grid-scroll"><table class="grid-table">
          <thead><tr><th class="w-seq"><input type="checkbox" data-suggest-all checked title="全選建議的" /></th>
          <th>姓名</th><th>組別</th><th>EMAIL</th><th class="num">出現次數</th><th>出現在</th><th>備註</th></tr></thead>
          <tbody>${cands.map((c) => `<tr class="${c.suspect ? "sched-warn" : ""}">
            <td><input type="checkbox" data-suggest-pick="${escapeHtml(c.name)}"${c.recommend ? " checked" : ""} /></td>
            <td><strong>${escapeHtml(c.name)}</strong></td>
            <td><select data-suggest-group="${escapeHtml(c.name)}" class="cell-input">
                  <option value="">（未分組）</option>
                  ${(personnelGroupOptions || []).map((g) =>
                    `<option value="${escapeHtml(g)}"${g === c.group_name ? " selected" : ""}>${escapeHtml(g)}</option>`).join("")}
                  ${c.group_name && !(personnelGroupOptions || []).includes(c.group_name)
                    ? `<option value="${escapeHtml(c.group_name)}" selected>${escapeHtml(c.group_name)}</option>` : ""}
                </select></td>
            <td><input class="cell-input" type="email" data-suggest-email="${escapeHtml(c.name)}"
                  placeholder="通知要用（可稍後補）" /></td>
            <td class="num">${c.count}</td>
            <td><span class="muted">${escapeHtml((c.from || []).join("、"))}</span></td>
            <td>${c.suspect
                  ? `<span class="badge danger" title="原始值：${escapeHtml(c.raw_sample)}">${escapeHtml(c.suspect)}</span>`
                  : '<span class="muted">—</span>'}</td>
          </tr>`).join("")}</tbody>
        </table></div>
        <button type="submit">建立勾選的人員</button>
      </form>`;
    box.scrollIntoView({ block: "nearest" });
  } catch (e) {
    box.innerHTML = `<p class="muted">掃描失敗：${escapeHtml(e.message)}</p>`;
  }
}

document.addEventListener("click", (event) => {
  if (event.target.closest("#personnel-suggest-open")) { openPersonnelSuggest(); return; }
  if (event.target.closest("[data-suggest-close]")) {
    document.querySelector("#personnel-suggest-box").hidden = true;
  }
});

document.addEventListener("change", (event) => {
  const all = event.target.closest("[data-suggest-all]");
  if (!all) return;
  for (const cb of document.querySelectorAll("[data-suggest-pick]")) cb.checked = all.checked;
});

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("[data-suggest-form]");
  if (!form) return;
  event.preventDefault();
  const names = [...form.querySelectorAll("[data-suggest-pick]:checked")]
    .map((cb) => cb.getAttribute("data-suggest-pick"));
  if (!names.length) { window.alert("至少要勾一個人。"); return; }
  const groups = {};
  for (const sel of form.querySelectorAll("[data-suggest-group]")) {
    const n = sel.getAttribute("data-suggest-group");
    if (names.includes(n) && sel.value) groups[n] = sel.value;
  }
  const emails = {};
  for (const inp of form.querySelectorAll("[data-suggest-email]")) {
    const n = inp.getAttribute("data-suggest-email");
    if (names.includes(n) && inp.value.trim()) emails[n] = inp.value.trim();
  }
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = true;
  submit.textContent = "建立中…";
  try {
    const r = (await api("/api/personnel-suggest/create", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ names, groups, emails }),
    })).data;
    document.querySelector("#personnel-suggest-box").innerHTML =
      `<p class="chip done">已建立 ${r.created_count} 位人員${r.skipped_count ? `（跳過 ${r.skipped_count} 位已存在的）` : ""}。
       各表單的負責人下拉現在選得到他們了。</p>`;
    await Promise.all([loadPersonnelMaster(), loadWorkload()]);
  } catch (e) {
    submit.disabled = false;
    submit.textContent = "建立勾選的人員";
    window.alert(`建立失敗：${e.message}`);
  }
});

async function openHandover(fromName, fromUsername, includeClosed = false) {
  const box = document.querySelector("#handover-panel");
  if (!box) return;
  box.hidden = false;
  box.dataset.from = fromName;
  box.dataset.username = fromUsername || "";
  box.innerHTML = `<p class="muted">計算中…</p>`;
  try {
    const pv = (await api(`/api/handover/preview?from_name=${encodeURIComponent(fromName)}`
      + `&from_username=${encodeURIComponent(fromUsername || "")}`
      + `&include_closed=${includeClosed ? "true" : "false"}`)).data;
    const people = ((await api("/api/personnel-workload")).data.people || [])
      .filter((p) => p.name !== fromName && p.status !== "disabled");
    const list = (rows) => rows.length
      ? rows.map((r) => `<span class="badge">${escapeHtml(r.label)} ${r.count}</span>`).join(" ")
      : '<span class="muted">無</span>';
    box.innerHTML = `
      <div class="sched-head">
        <h3>離職交接：${escapeHtml(fromName)}${fromUsername ? `（${escapeHtml(fromUsername)}）` : ""}</h3>
        <button type="button" class="secondary btn-sm" data-handover-close>收合</button>
      </div>
      <p><strong>會轉走 ${pv.transfer_count} 筆</strong>：${list(pv.will_transfer)}</p>
      <p><strong>維持原承辦 ${pv.keep_count} 筆</strong>：${list(pv.will_keep)}</p>
      <p class="muted">${escapeHtml(pv.keep_reason || "")}</p>
      <form class="resource-form" data-handover-form>
        <select data-handover-to required>
          <option value="">選接手人 *</option>
          ${people.map((p) => `<option value="${escapeHtml(p.name)}" data-username="${escapeHtml(p.username || "")}">
            ${escapeHtml(p.name)}${p.group_name ? `（${escapeHtml(p.group_name)}）` : ""}｜目前 ${p.active} 筆</option>`).join("")}
        </select>
        <input data-handover-reason placeholder="交接原因（例：林信成 8/31 離職）" />
        <label class="check-inline">
          <input type="checkbox" data-handover-closed${includeClosed ? " checked" : ""} />
          連已結案的一起轉
        </label>
        <button type="submit"${pv.transfer_count ? "" : " disabled"}>確認交接（${pv.transfer_count} 筆）</button>
      </form>`;
    box.scrollIntoView({ block: "nearest" });
  } catch (e) {
    box.innerHTML = `<p class="muted">交接預覽失敗：${escapeHtml(e.message)}</p>`;
  }
}

document.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-handover]");
  if (btn) {
    await openHandover(btn.getAttribute("data-handover"), btn.getAttribute("data-username"));
    return;
  }
  if (event.target.closest("[data-handover-close]")) {
    document.querySelector("#handover-panel").hidden = true;
    return;
  }
  if (event.target.closest("#workload-refresh")) loadWorkload();
  // 進人員管理才盤點：這是全表掃描，沒必要每次登入都跑一遍
  if (event.target.closest('[data-open-panel="personnel-admin"]')) setTimeout(loadWorkload, 200);
});

// 勾「連已結案的一起轉」→ 重新算會動到幾筆（數字要當場變，不能等送出才知道）
document.addEventListener("change", (event) => {
  const cb = event.target.closest("[data-handover-closed]");
  if (!cb) return;
  const box = document.querySelector("#handover-panel");
  openHandover(box.dataset.from, box.dataset.username, cb.checked);
});

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("[data-handover-form]");
  if (!form) return;
  event.preventDefault();
  const box = document.querySelector("#handover-panel");
  const sel = form.querySelector("[data-handover-to]");
  const toName = sel.value;
  const toUsername = sel.selectedOptions[0]?.getAttribute("data-username") || "";
  const includeClosed = form.querySelector("[data-handover-closed]").checked;
  if (!window.confirm(`把 ${box.dataset.from} 名下的資料轉給 ${toName}？\n每一筆都會留下稽核紀錄，事後查得到。`)) return;
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = true;
  submit.textContent = "交接中…";
  try {
    const r = (await api("/api/handover/apply", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        from_name: box.dataset.from, from_username: box.dataset.username,
        to_name: toName, to_username: toUsername,
        include_closed: includeClosed,
        reason: form.querySelector("[data-handover-reason]").value,
      }),
    })).data;
    box.innerHTML = `<p class="chip done">已把 ${escapeHtml(box.dataset.from)} 名下 ${r.moved_count} 筆轉給 ${escapeHtml(toName)}
      （${r.moved.map((m) => `${escapeHtml(m.label)} ${m.count}`).join("、")}）。每一筆都留了稽核紀錄。</p>`;
    await Promise.all([loadWorkload(), loadResource("project"), loadResource("contract"), loadCases()]);
  } catch (e) {
    submit.disabled = false;
    submit.textContent = "確認交接";
    window.alert(`交接失敗：${e.message}`);
  }
});

// 跨模組串接：案件／專案／預算名字不同但在講同一件事（青浦機房搬遷／青浦機房搬遷專案／桃園青浦機房）。
// 比對在後端做（純字串，不連網、不用 AI），這裡只負責把候選列出來讓人裁決。
async function loadCrossLinks() {
  const box = document.querySelector("#name-result");
  const sum = document.querySelector("#name-summary");
  if (!box) return;
  box.innerHTML = `<p class="muted">比對中…</p>`;
  try {
    const data = (await api("/api/cross-links")).data || {};
    const cands = data.candidates || [];
    if (sum) {
      sum.innerHTML = cands.length
        ? `<p class="warn-line">⚠ 找到 <strong>${cands.length}</strong> 筆專案／預算，名字跟某個案件很像但沒掛在一起。系統只提建議、不自動歸戶。</p>`
        : `<p class="ok-line">✓ 沒有找到名字相近卻沒串在一起的資料。</p>`;
    }
    if (!cands.length) {
      box.innerHTML = `<p class="muted">目前沒有建議。<br />
        比對方式：取兩個名稱的最長共同片段，至少 3 個字且要佔短名稱一半以上才會列出來——
        寧可漏掉幾個讓你手動歸戶，也不要把「桃園機房搬遷」跟「青浦機房搬遷」配在一起。</p>`;
      return;
    }
    const KIND = { project: "專案", budget: "預算" };
    box.innerHTML = `<p class="muted">${escapeHtml(data.note || "")}</p>
      <div class="grid-scroll"><table class="grid-table">
        <thead><tr><th>類型</th><th>目前這筆</th><th>目前掛在</th><th>建議歸到的案件</th>
        <th>為什麼像</th><th class="col-actions">操作</th></tr></thead>
        <tbody>${cands.map((c) => `<tr>
          <td>${escapeHtml(KIND[c.kind] || c.kind)}</td>
          <td><strong>${escapeHtml(c.name || "")}</strong><br /><small class="muted">${escapeHtml(c.code || "")}</small></td>
          <td>${c.current_case_title
                ? escapeHtml(c.current_case_title)
                : '<span class="muted">尚未歸戶</span>'}</td>
          <td><strong>${escapeHtml(c.suggest_case_title || "")}</strong><br />
              <small class="muted">${escapeHtml(c.suggest_case_code || "")}</small></td>
          <td><span class="badge">共同「${escapeHtml(c.common_part)}」</span></td>
          <td><button type="button" class="btn-sm" data-cross-apply
                data-kind="${escapeHtml(c.kind)}" data-id="${c.id}" data-case="${c.suggest_case_id}"
                title="把這筆歸到該案件底下（會留稽核紀錄，可日後改掛）">歸到這個案件</button></td>
        </tr>`).join("")}</tbody></table></div>`;
  } catch (error) {
    box.innerHTML = `<p class="muted">比對失敗：${escapeHtml(error.message)}</p>`;
  }
}

document.querySelector("#name-result")?.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-cross-apply]");
  if (!btn) return;
  btn.disabled = true;
  btn.textContent = "歸戶中…";
  try {
    await api("/api/cross-links/apply", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: btn.getAttribute("data-kind"),
        id: Number(btn.getAttribute("data-id")),
        case_id: Number(btn.getAttribute("data-case")),
      }),
    });
    await Promise.all([loadResource("project"), loadResource("budget")]);
    await loadCrossLinks();
  } catch (e) {
    btn.disabled = false;
    btn.textContent = "歸到這個案件";
    window.alert(`歸戶失敗：${e.message}`);
  }
});

async function loadNameCleaning() {
  const box = document.querySelector("#name-result");
  const sum = document.querySelector("#name-summary");
  if (!box) return;
  if (nameKind === "cross") { await loadCrossLinks(); return; }   // 跨模組走另一套比對
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
// 分攤金額／比例就地改：給哪一個就以哪一個為準，另一個由後端換算，改完重載看合計對不對
document.addEventListener("change", async (event) => {
  const amt = event.target.closest("[data-alloc-amount]");
  const pct = event.target.closest("[data-alloc-pct]");
  const el = amt || pct;
  if (!el) return;
  const id = el.getAttribute(amt ? "data-alloc-amount" : "data-alloc-pct");
  const budgetId = el.getAttribute("data-budget");
  const body = amt ? { amount: Number(el.value || 0) } : { share_pct: Number(el.value || 0) };
  el.disabled = true;
  try {
    await api(`/api/budget-allocations/${id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    await loadResource("budget");            // 分攤方法可能被鎖回固定金額
    await loadBudgetAllocations(budgetId);
  } catch (error) {
    el.disabled = false;
    window.alert(`分攤修改失敗：${error.message}`);
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

// 狀態動作（開始執行/暫停/復工/結案/取消/重開）：需要原因的先問，取消輸入就中止
cases.addEventListener("click", async (event) => {
  const btn = event.target.closest("button[data-status-act]");
  if (!btn) return;
  const id = btn.closest("[data-case-id]").dataset.caseId;
  const act = btn.dataset.statusAct;
  const meta = Object.values(CASE_STATUS_ACTIONS).flat().find((a) => a.act === act)
    || { label: "取消案件", ask: "取消原因（會留在案件紀錄）：" };
  let reason = "";
  if (meta.ask) {
    const input = window.prompt(`${meta.label}：${meta.ask}`, "");
    if (input === null) return;
    if (!input.trim()) { window.alert(`請填${meta.label}原因。`); return; }
    reason = input.trim();
  } else if (act === "close" && !window.confirm("確定結案？結案後仍可由主管重新開啟（會留重開紀錄）。")) {
    return;
  }
  try {
    await api(`/api/cases/${id}/status/${act}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }) });
  } catch (error) { window.alert(error.message); }
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
    // 需求書 §4 核准以外的三條路。退件/駁回一定要寫原因，取消輸入就中止、不送出。
    if (action === "return" || action === "reject") {
      const label = action === "return" ? "退回補件" : "駁回";
      const hint = action === "return" ? "請說明要補什麼，申請人會看到：" : "請說明駁回理由（會留在審核紀錄）：";
      const reason = window.prompt(`${label}：${hint}`, "");
      if (reason === null) return;                       // 按取消＝不做
      if (!reason.trim()) { window.alert(`請填${label}原因。`); return; }
      await api(`/api/cases/${id}/${action}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: reason.trim() }) });
    }
    if (action === "merge") {
      const target = await pickMergeTarget(id);
      if (!target) return;
      const res = (await api(`/api/cases/${id}/merge`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_case_id: target.id, reason: target.reason }) })).data || {};
      const moved = Object.entries(res.moved || {}).map(([k, n]) => `${MERGE_TABLE_LABEL[k] || k} ${n} 筆`).join("、");
      window.alert(`已併入 ${target.label}。${moved ? `\n一併轉過去的資料：${moved}` : "\n這件申請底下還沒有資料要轉。"}`);
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

for (const tab of dashTabs) {
  tab.addEventListener("click", () => activateDashTab(tab.dataset.dashTab));
}

for (const tab of ioTabs) {
  tab.addEventListener("click", () => activateIoTab(tab.dataset.ioTab));
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
    if (!total) {
      backfillStatusEl.textContent = "全部已有編號、已掛案件，無需補號。";
      return;
    }
    // 按下去之前要看得到會動到哪些狀態：匯入來的草稿要補，但如果裡面混著真的還在等審核
    // 的新申請，補號等於讓它提前佔號——所以把分組攤開，讓人自己判斷再決定按不按。
    const byStatus = Object.entries(d.cases_by_status || {})
      .map(([s, n]) => `${STATUS_LABELS[s] || s} ${n}`).join("、");
    const skipped = Object.entries(d.skipped_by_status || {})
      .map(([s, n]) => `${STATUS_LABELS[s] || s} ${n}`).join("、");
    backfillStatusEl.innerHTML =
      `待補：案件系統編號 <b>${d.cases_missing}</b> 筆、付款核銷編號 ${d.settle_missing} 筆、預算/專案未掛案件 ${d.case_link_missing} 筆`
      + (byStatus ? `<br/><span class="muted">會補的案件狀態：${escapeHtml(byStatus)}</span>` : "")
      + (skipped ? `<br/><span class="muted">跳過不補（不該佔正式號）：${escapeHtml(skipped)}</span>` : "");
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
// 搜尋範圍下拉也依角色收斂：後端已濾掉搜不到的型別，這裡把選項一併拿掉，
// 免得選了一個永遠 0 筆的範圍還以為是資料不見了。CIO 只有決策總覽 → 整個搜尋停用。
const SEARCH_TYPE_MODULE = {
  case: "cases-module", contract: "contracts-module", payment: "payments-module",
  document: "data-review", budget: "budget", project: "projects",
  signoff: "signoff", purchase: "purchases",
};
function applySearchScopeByRole(user) {
  if (!searchScope || !user) return;
  const mods = new Set(user.allowed_modules || []);
  for (const opt of [...searchScope.options]) {
    if (!opt.value) continue;  // 「全部功能」永遠留著
    opt.hidden = !mods.has(SEARCH_TYPE_MODULE[opt.value]);
  }
  const searchable = Object.values(SEARCH_TYPE_MODULE).some((m) => mods.has(m));
  if (globalSearch) {
    globalSearch.disabled = !searchable;
    globalSearch.placeholder = searchable
      ? "輸入 ≥2 字搜尋八大模組"
      : "你的角色只看決策總覽，請從總覽下探";
  }
  if (searchScope) searchScope.disabled = !searchable;
}
const searchResults = document.querySelector("#search-results");      // 側欄小提示
const searchPanel = document.querySelector("#search-panel");           // 中間大結果區
const searchResultsMain = document.querySelector("#search-results-main");
const SEARCH_LABEL = { case: "案件", contract: "合約", payment: "付款", document: "文件", budget: "預算", project: "專案", signoff: "簽呈", purchase: "費用", project_item: "專案子項" };
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
    } else if (act === "group") {
      // 指派組長管哪一組：留空＝未指派（該帳號會退化成只看自己的案，不會看到全公司）
      const groups = ((await api("/api/admin/users")).data || {}).groups || [];
      const g = window.prompt(
        `${username} 管哪一組？\n可填：${groups.join("／") || "（尚未設定組別選項）"}\n留空＝未指派（只看得到自己的案）`, "");
      if (g === null) return;
      await api(`/api/admin/users/${username}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ group_name: g.trim() }) });
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
  const REQUIRED_BY_STEP = {
    project: ["project_name"],
    purchase: ["purchase_code", "item_name"],
    contract: ["contract_code", "contract_name"],
  };
  const OPTIONAL_STEPS = ["project", "contract", "purchase"];

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
  const WIZARD_NAME_AUTOFILL_FIELD = { project: "project_name", contract: "contract_name" };
  for (const toggle of wizardForm.querySelectorAll("[data-wizard-toggle]")) {
    toggle.addEventListener("change", () => {
      const step = toggle.getAttribute("data-wizard-toggle");
      setStepEnabled(step, toggle.checked);
      if (toggle.checked) {
        const fieldName = WIZARD_NAME_AUTOFILL_FIELD[step];
        const nameEl = fieldName && stepScope(step)?.querySelector(`[name="${fieldName}"]`);
        const titleEl = stepScope("case")?.querySelector('[name="title"]');
        if (nameEl && !nameEl.value.trim() && titleEl && titleEl.value.trim()) nameEl.value = titleEl.value.trim();
        // 專案負責人預設沿用案件負責人（仍可改）
        if (step === "project") {
          const projOwner = stepScope("project")?.querySelector('[name="owner"]');
          const caseOwner = stepScope("case")?.querySelector('[name="owner"]');
          if (projOwner && !projOwner.value && caseOwner && caseOwner.value) projOwner.value = caseOwner.value;
        }
        // 廠商沿用（助理第三次回饋 §6）：這個精靈頁面一次填多個步驟，同一個 Case 十之八九是
        // 同一家廠商，別的步驟已經填過就直接帶過來（欄位仍是空的才帶，不覆蓋使用者已填的）。
        const vendorEl = stepScope(step)?.querySelector('[name="vendor_name"]');
        if (vendorEl && !vendorEl.value.trim()) {
          for (const otherStep of ["project", "contract", "purchase"]) {
            if (otherStep === step) continue;
            const otherVendor = stepScope(otherStep)?.querySelector('[name="vendor_name"]');
            if (otherVendor && otherVendor.value.trim()) { vendorEl.value = otherVendor.value.trim(); break; }
          }
        }
      }
    });
  }

  // 負責人依組別過濾：選了組別才列該組的人（助理回饋）。組別留空＝全部列出。
  const groupSel = wizardForm.querySelector("[data-wizard-group]");
  const ownerSel = wizardForm.querySelector("[data-group-filtered]");
  function filterOwnerByGroup() {
    if (!ownerSel) return;
    const g = groupSel ? groupSel.value : "";
    const list = (personnelMasterCache || []).filter((p) => !g || p.group_name === g);
    const prev = ownerSel.value;
    ownerSel.innerHTML = `<option value="">（未選擇）負責人 *</option>`
      + list.map((p) => `<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}</option>`).join("");
    if (prev && list.some((p) => p.name === prev)) ownerSel.value = prev;
  }
  groupSel?.addEventListener("change", filterOwnerByGroup);
  document.addEventListener("personnel-loaded", filterOwnerByGroup);

  // 預算名目：預算內＝從匯入的預算表帶出既有名目給人選；預算外＝自己打（助理回饋）
  const itemList = document.querySelector("#opt-budget-items");
  function refreshBudgetItems() {
    const inBudget = wizardForm.querySelector('[name="budget_type"][value="in_budget"]')?.checked;
    const itemEl = stepScope("case")?.querySelector('[name="budget_item"]');
    if (itemEl) {
      itemEl.placeholder = inBudget ? "預算名目 *（從既有預算表選）" : "預算名目 *（預算外，自行填寫）";
    }
    if (!itemList) return;
    itemList.innerHTML = inBudget
      ? [...new Set((resourceCaches.budget || []).map((b) => b.budget_code).filter(Boolean))]
          .map((v) => `<option value="${escapeHtml(v)}"></option>`).join("")
      : "";
  }
  for (const r of wizardForm.querySelectorAll('[name="budget_type"]')) r.addEventListener("change", refreshBudgetItems);

  // Bug 修復（第三次回饋）：datalist 選定名目後 input.value 等於該選項全文，瀏覽器再開下拉時
  // 只會顯示「前綴符合目前輸入值」的選項，等於自己一個以外的全被濾掉，使用者看起來像選項消失、
  // 選錯了也換不了。對策：聚焦/點擊時先清空目前值讓下拉顯示全部選項，沒有重新選過就在失焦時還原。
  {
    const budgetItemEl = wizardForm.querySelector('[name="budget_item"][list="opt-budget-items"]');
    if (budgetItemEl) {
      const showFullList = () => {
        if (budgetItemEl.value) {
          budgetItemEl.dataset.prevValue = budgetItemEl.value;
          budgetItemEl.value = "";
        }
      };
      budgetItemEl.addEventListener("focus", showFullList);
      budgetItemEl.addEventListener("mousedown", showFullList);
      budgetItemEl.addEventListener("blur", () => {
        if (!budgetItemEl.value && budgetItemEl.dataset.prevValue) {
          budgetItemEl.value = budgetItemEl.dataset.prevValue;
        }
        delete budgetItemEl.dataset.prevValue;
      });
    }
  }

  wizardForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const statusEl = document.querySelector("#wizard-status");
    const resultEl = document.querySelector("#wizard-result");
    const c = readStep("case", ["title", "owner", "group_name", "expense_kind", "budget_item", "source", "description"]);
    const body = {
      case: {
        title: c.title, owner: c.owner,
        group_name: c.group_name, expense_kind: c.expense_kind, budget_item: c.budget_item,
        source: c.source, description: c.description,
        // 預算內/外是 radio，readStep 只讀得到第一個，改用 checked 判斷
        budget_type: wizardForm.querySelector('[name="budget_type"]:checked')?.value || "",
      },
    };
    if (wizardForm.querySelector('[data-wizard-toggle="project"]').checked) {
      const p = readStep("project", ["project_name", "level", "owner", "vendor_name", "cross_company", "start_date", "end_date"]);
      const involvesProcurement = stepScope("project")?.querySelector('[name="involves_procurement"]')?.checked ? 1 : 0;
      body.project = { project_name: p.project_name, level: p.level, owner: p.owner,
                       vendor_name: p.vendor_name, cross_company: p.cross_company,
                       start_date: p.start_date, end_date: p.end_date,
                       involves_procurement: involvesProcurement };
    }
    if (wizardForm.querySelector('[data-wizard-toggle="purchase"]').checked) {
      const p = readStep("purchase", ["purchase_code", "item_name", "vendor_name", "quantity", "amount", "note"]);
      body.purchase = { purchase_code: p.purchase_code, item_name: p.item_name, vendor_name: p.vendor_name, quantity: num(p.quantity), amount: num(p.amount), note: p.note };
    }
    if (contractToggle.checked) {
      const k = readStep("contract", ["contract_code", "contract_name", "vendor_name", "amount", "start_date", "end_date"]);
      body.contract = { contract_code: k.contract_code, contract_name: k.contract_name, vendor_name: k.vendor_name, amount: num(k.amount), start_date: k.start_date, end_date: k.end_date };
    }

    if (statusEl) statusEl.textContent = "送出中…";
    if (resultEl) resultEl.innerHTML = "";
    try {
      const created = (await api("/api/case-wizard", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })).data || {};
      if (statusEl) statusEl.textContent = "全部建立成功！";
      // 原本這行印「案件 TMP20260038（TMP20260038，核准後才配正式案號）」——同一個暫時號印兩次。
      // 改成報案名；使用者自己填的編號才顯示（那不是系統配的暫時號）。
      const newCase = created.case || {};
      const codeBit = isTempCaseCode(newCase.case_code) ? "" : `（${escapeHtml(newCase.case_code || "")}）`;
      const lines = [`案件「${escapeHtml(newCase.title || "")}」${codeBit}已建立，核准後才配正式案號`];
      if (created.project) {
        const wbs = created.project.standard_wbs;
        const wbsNote = wbs ? `　已自動排 ${wbs.created_count} 項標準 WBS 工作項` : "";
        lines.push(`專案 ${escapeHtml(created.project.project_name)}${wbsNote}　`
          + `<button type="button" class="link-btn" data-goto-wbs="${created.project.id}">前往填寫／調整 WBS →</button>`);
      }
      if (created.contract) lines.push(`合約 ${escapeHtml(created.contract.contract_code)}`);
      if (created.purchase) lines.push(`費用 ${escapeHtml(created.purchase.purchase_code)}`);
      if (resultEl) resultEl.innerHTML = `<div class="callout">${lines.join("<br/>")}</div>`;
      wizardForm.reset();
      for (const step of OPTIONAL_STEPS) setStepEnabled(step, false);
      await refresh();
    } catch (error) {
      if (statusEl) statusEl.textContent = `失敗：${error.message}`;
    }
  });

  document.querySelector("#wizard-result")?.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-goto-wbs]");
    if (btn) openProjectItem(btn.getAttribute("data-goto-wbs"));
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
