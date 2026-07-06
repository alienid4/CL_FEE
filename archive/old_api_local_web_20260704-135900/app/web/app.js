const views = [
  { key: "dashboard", label: "八項控管看板" },
  { key: "search", label: "全文檢索" },
  { key: "case360", label: "Case 360" },
  { key: "timeline", label: "時間線" },
  { key: "priority", label: "處理優先" },
  { key: "owners", label: "負責人" },
  { key: "vendors", label: "廠商" },
  { key: "excel", label: "Excel 匯入匯出" },
  { key: "cmdb", label: "CMDB 預留" },
  { key: "rules", label: "狀態規則" },
  { key: "data", label: "資料維護" }
];

const dataModules = {
  "signing-cases": {
    label: "案件",
    endpoint: "/api/signing-cases",
    columns: ["id", "case_code", "title", "category", "amount", "status"]
  },
  contracts: {
    label: "合約",
    endpoint: "/api/contracts",
    columns: ["id", "contract_code", "contract_name", "vendor_name", "amount", "status"]
  },
  "payment-schedules": {
    label: "付款排程",
    endpoint: "/api/payment-schedules",
    columns: ["id", "case_id", "contract_id", "payment_month", "payment_amount", "invoice_status", "status"]
  },
  documents: {
    label: "附件 / 簽呈",
    endpoint: "/api/documents",
    columns: ["id", "case_id", "contract_id", "file_name", "document_type", "parse_status"]
  },
  "budget-lines": {
    label: "預算",
    endpoint: "/api/budget-lines",
    columns: ["id", "budget_year", "category", "item_name", "owner_group", "budget_amount", "status"]
  }
};

const state = {
  view: "dashboard",
  role: "manager",
  lastSearch: "",
  selectedCaseId: null
};

const el = {
  nav: document.querySelector("#moduleNav"),
  workspace: document.querySelector("#workspace"),
  viewTitle: document.querySelector("#viewTitle"),
  statusStrip: document.querySelector("#statusStrip"),
  serviceStatus: document.querySelector("#serviceStatus"),
  globalSearch: document.querySelector("#globalSearch"),
  roleSelect: document.querySelector("#roleSelect"),
  refreshButton: document.querySelector("#refreshButton")
};

const labels = {
  id: "項次",
  case_code: "案件 ID",
  title: "案件名稱",
  category: "負責人 / 分類",
  amount: "金額",
  status: "狀態",
  contract_code: "合約 ID",
  contract_name: "合約名稱",
  vendor_name: "廠商",
  case_id: "案件",
  contract_id: "合約",
  payment_month: "付款月份",
  payment_amount: "付款金額",
  invoice_status: "發票狀態",
  file_name: "檔名",
  document_type: "文件類型",
  parse_status: "解析狀態",
  budget_year: "年度",
  item_name: "項目",
  owner_group: "單位",
  budget_amount: "預算金額",
  code: "代碼",
  owner: "負責人",
  vendor: "廠商",
  item_type: "類型",
  open_count: "未完成",
  done_count: "完成",
  case_count: "案件數",
  total_amount: "總金額",
  contract_count: "合約數",
  contract_amount: "合約金額",
  first_start_date: "最早開始",
  last_end_date: "最晚結束"
};

function titleFor(viewKey) {
  return views.find((view) => view.key === viewKey)?.label || "系統功能";
}

function money(value) {
  const number = Number(value || 0);
  return number.toLocaleString("zh-Hant-TW");
}

function cell(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "number") return money(value);
  return String(value);
}

async function api(path) {
  const response = await fetch(path);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
  return data.data ?? data;
}

function renderNav() {
  el.nav.innerHTML = views.map((view) => {
    const active = view.key === state.view ? "active" : "";
    return `<button class="${active}" type="button" data-view="${view.key}">${view.label}</button>`;
  }).join("");
  el.viewTitle.textContent = titleFor(state.view);
}

function renderStatus(cards = {}) {
  const items = [
    ["案件", cards.signing_cases ?? 0, "cases"],
    ["合約", cards.contracts ?? 0, "contracts"],
    ["付款排程", cards.payment_schedules ?? 0, "payments"],
    ["文件 / 簽呈", cards.documents ?? 0, "documents"]
  ];
  el.statusStrip.innerHTML = items.map(([label, value, metric]) => `
    <button class="metric-card" type="button" data-drilldown="${metric}">
      <span>${label}</span>
      <strong>${cell(value)}</strong>
    </button>
  `).join("");
}

function panel(title, body, actions = "") {
  return `
    <section class="panel">
      <div class="panel-header">
        <h3>${title}</h3>
        <div>${actions}</div>
      </div>
      <div class="panel-body">${body}</div>
    </section>
  `;
}

function table(rows, columns, options = {}) {
  if (!rows || rows.length === 0) {
    return document.querySelector("#emptyTemplate").innerHTML;
  }
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>${columns.map((key) => `<th>${labels[key] || key}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr ${options.caseLink && row.id ? `data-case-id="${row.id}"` : ""}>
              ${columns.map((key) => `<td>${cell(row[key])}</td>`).join("")}
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

async function renderDashboard() {
  const dashboard = await api(`/api/dashboard/${state.role}`);
  renderStatus(dashboard.cards);
  const cards = [
    ["有效案件", dashboard.cards.active_cases ?? 0, "active_cases", "排除作廢後仍需控管的案件。"],
    ["未完成案件", "下鑽", "unfinished_cases", "點擊後列出尚未完成、結案或作廢的案件。"],
    ["簽呈金額", money(dashboard.cards.signing_amount), "cases", "簽呈案件金額彙總，可回到案件明細。"],
    ["付款與發票", dashboard.cards.payment_schedules ?? 0, "payments", "可追付款月份、廠商、發票與付款狀態。"]
  ];
  const features = [
    ["全文檢索", "跨案件、合約、廠商、文件與來源欄位搜尋。", "search"],
    ["Case 360", "一個案件看完流程、金額、附件、付款與舉證。", "case360"],
    ["時間線", "用顏色看每個案件節點完成、未完成、不適用與異常。", "timeline"],
    ["處理優先", "用金額與急迫程度排序主管今天要先處理的事。", "priority"],
    ["負責人視角", "點人可看今年手上案件、未完成與金額。", "owners"],
    ["廠商視角", "看廠商合約、付款、發票與異常。", "vendors"],
    ["Excel 操作", "匯入、欄位對應、檢核、匯出與版本控管。", "excel"],
    ["CMDB 預留", "第一階段保留關聯欄位，第二階段接 CMDB 查詢或匯入。", "cmdb"],
    ["狀態規則", "說明完成、未完成、不適用、異常如何判斷。", "rules"],
    ["資料維護", "維護底層案件、合約、付款、文件與預算資料。", "data"]
  ];
  el.workspace.innerHTML = `
    ${panel("主管摘要", `<div class="metric-grid">${cards.map(([label, value, metric, help]) => `
      <button class="metric-card" type="button" data-drilldown="${metric}">
        <span>${label}</span>
        <strong>${value}</strong>
        <span>${help}</span>
      </button>
    `).join("")}</div>`)}
    ${panel("12 項系統功能入口", `<div class="feature-grid">${features.map(([label, help, view]) => `
      <button class="feature-card" type="button" data-view="${view}">
        <span>系統功能</span>
        <strong>${label}</strong>
        <p>${help}</p>
      </button>
    `).join("")}</div>`)}
  `;
}

async function renderSearch(q = state.lastSearch) {
  renderStatus({});
  state.lastSearch = q || "";
  const result = q ? await api(`/api/search?q=${encodeURIComponent(q)}&limit=100`) : [];
  el.workspace.innerHTML = panel(
    "全文檢索",
    `
      <div class="filter-row">
        <input id="searchInput" type="search" value="${state.lastSearch}" placeholder="輸入 XX專案、廠商、合約、付款月份、附件" />
        <button id="searchButton" class="primary-button" type="button">搜尋</button>
      </div>
      ${table(result, ["result_type", "id", "title", "subtitle", "status"])}
    `
  );
}

async function renderDrilldown(metric, params = {}) {
  const search = new URLSearchParams({ metric, ...params });
  const data = await api(`/api/system/drilldown?${search.toString()}`);
  state.view = "dashboard";
  renderNav();
  el.workspace.innerHTML = panel(
    data.title || "下鑽明細",
    table(data.rows, ["item_type", "id", "code", "title", "owner", "vendor", "amount", "status"], { caseLink: metric.includes("case") })
  );
}

async function renderCase360(caseId = state.selectedCaseId) {
  renderStatus({});
  const fallback = `
    <div class="filter-row">
      <input id="caseIdInput" type="number" min="1" placeholder="輸入 Case ID" />
      <button id="caseLoadButton" class="primary-button" type="button">查看 Case 360</button>
    </div>
    <p class="small-muted">也可以從搜尋結果、時間線、下鑽明細或處理優先矩陣點進來。</p>
  `;
  if (!caseId) {
    el.workspace.innerHTML = panel("Case 360", fallback);
    return;
  }
  state.selectedCaseId = caseId;
  const data = await api(`/api/system/case-360/${caseId}`);
  const caseData = data.case;
  const timeline = renderTimelineNodes(data.timeline);
  el.workspace.innerHTML = `
    ${panel("Case 360", `
      ${fallback}
      <div class="metric-grid">
        <div class="metric-card"><span>案件</span><strong>${caseData ? cell(caseData.title) : `Case #${caseId}`}</strong></div>
        <div class="metric-card"><span>簽呈金額</span><strong>${money(data.totals.case_amount)}</strong></div>
        <div class="metric-card"><span>合約金額</span><strong>${money(data.totals.contract_amount)}</strong></div>
        <div class="metric-card"><span>付款金額</span><strong>${money(data.totals.payment_amount)}</strong></div>
      </div>
    `)}
    ${panel("流程時間線", timeline)}
    <div class="split-grid">
      ${panel("關聯付款", table(data.payments, ["id", "contract_id", "payment_month", "payment_amount", "invoice_status", "status"]))}
      ${panel("舉證鏈", renderEvidence(data.evidence))}
    </div>
    <div class="split-grid">
      ${panel("關聯合約", table(data.contracts, ["id", "contract_code", "contract_name", "vendor_name", "amount", "status"]))}
      ${panel("附件 / 簽呈", table(data.documents, ["id", "file_name", "document_type", "parse_status", "source_note"]))}
    </div>
  `;
}

function renderTimelineNodes(nodes) {
  return `<div class="timeline">${nodes.map((node) => `
    <button class="node tone-${node.tone}" type="button" title="${node.evidence}">
      <span class="dot"></span>
      <strong>${node.step}</strong>
      <span>${node.status}</span>
    </button>
  `).join("")}</div>`;
}

function renderEvidence(items) {
  return `<div class="evidence-list">${items.map((item) => `
    <div class="evidence-item">
      <strong>${item.title || "-"}</strong>
      <span class="badge">${item.type}</span>
      <p class="small-muted">${cell(item.source)}</p>
      <p>${cell(item.detail)}</p>
    </div>
  `).join("")}</div>`;
}

async function renderTimeline() {
  renderStatus({});
  const rows = await api("/api/system/timeline?limit=30");
  el.workspace.innerHTML = panel("案件時間線", `
    <div class="timeline-list">
      ${rows.length ? rows.map((row) => `
        <button class="timeline-card" type="button" data-case-id="${row.case.id}">
          <h4>${cell(row.case.title)} <span class="small-muted">#${row.case.id}</span></h4>
          ${renderTimelineNodes(row.timeline)}
        </button>
      `).join("") : document.querySelector("#emptyTemplate").innerHTML}
    </div>
  `);
}

async function renderPriority() {
  renderStatus({});
  const data = await api("/api/system/priority-matrix");
  const bubbles = data.bubbles || [];
  el.workspace.innerHTML = panel("處理優先矩陣", `
    <div class="matrix">
      <span class="matrix-label top">急迫 / 需主管確認</span>
      <span class="matrix-label right">金額影響大</span>
      ${bubbles.map((bubble) => {
        const left = Math.max(4, Math.min(82, bubble.impact));
        const top = Math.max(8, Math.min(78, 100 - bubble.urgency));
        return `
          <button class="bubble" type="button" data-case-id="${bubble.case_id}" style="left:${left}%; top:${top}%">
            <strong>${cell(bubble.label)}</strong>
            <span>${money(bubble.amount)} / ${bubble.status}</span>
          </button>
        `;
      }).join("")}
    </div>
  `);
}

async function renderOwners() {
  renderStatus({});
  const rows = await api("/api/system/owners");
  el.workspace.innerHTML = panel(
    "負責人視角",
    table(rows, ["owner", "case_count", "open_count", "done_count", "total_amount"])
  );
}

async function renderVendors() {
  renderStatus({});
  const rows = await api("/api/system/vendors");
  el.workspace.innerHTML = panel(
    "廠商視角",
    table(rows, ["vendor", "contract_count", "contract_amount", "first_start_date", "last_end_date"])
  );
}

async function renderRules() {
  renderStatus({});
  const rows = await api("/api/system/rules");
  el.workspace.innerHTML = panel("狀態規則管理", `
    <div class="rules-list">
      ${rows.map((row) => `<div class="rule-item"><strong>${row.rule}</strong><p>${row.description}</p></div>`).join("")}
    </div>
  `);
}

async function renderExcel() {
  renderStatus({});
  const data = await api("/api/system/excel-operations");
  el.workspace.innerHTML = `
    ${panel("Excel 匯入匯出", `
      <div class="feature-grid">
        <div class="feature-card"><span>範本</span><strong>${data.templates.length} 類</strong><p>${data.templates.join("、")}</p></div>
        <div class="feature-card"><span>匯入流程</span><strong>${data.import_modes.length} 步</strong><p>${data.import_modes.join(" → ")}</p></div>
        <div class="feature-card"><span>匯出模式</span><strong>${data.export_modes.length} 種</strong><p>${data.export_modes.join("、")}</p></div>
      </div>
      <p class="small-muted">${data.note}</p>
    `)}
  `;
}

async function renderCmdb() {
  renderStatus({});
  const data = await api("/api/system/cmdb-integration");
  el.workspace.innerHTML = `
    ${panel("CMDB 關聯預留", `
      <div class="feature-grid">
        ${data.strategy.map((item) => `
          <div class="feature-card">
            <span>第 ${item.phase} 階段</span>
            <strong>${item.name}</strong>
            <p>${item.description}</p>
            <span class="badge ${item.status === "reserved" ? "warning" : "active"}">${item.status}</span>
          </div>
        `).join("")}
      </div>
    `)}
    <div class="split-grid">
      ${panel("預留欄位", `<div class="rules-list">${data.reserved_fields.map((field) => `<div class="rule-item"><strong>${field}</strong><p>保留給 Case、合約、專案、付款或文件舉證使用。</p></div>`).join("")}</div>`)}
      ${panel("未來來源與落點", `
        <div class="rules-list">
          <div class="rule-item"><strong>來源</strong><p>${data.future_sources.join("、")}</p></div>
          <div class="rule-item"><strong>落點</strong><p>${data.supported_targets.join("、")}</p></div>
          <div class="rule-item"><strong>驗收</strong><p>${data.acceptance.join("；")}</p></div>
        </div>
      `)}
    </div>
  `;
}

async function renderDataMaintenance() {
  renderStatus({});
  const body = Object.entries(dataModules).map(([key, module]) => `
    <button class="feature-card" type="button" data-data-module="${key}">
      <span>資料維護</span>
      <strong>${module.label}</strong>
      <p>${module.endpoint}</p>
    </button>
  `).join("");
  el.workspace.innerHTML = panel("資料維護入口", `<div class="feature-grid">${body}</div>`);
}

async function renderDataModule(key) {
  renderStatus({});
  const module = dataModules[key];
  const rows = await api(`${module.endpoint}?limit=100`);
  el.workspace.innerHTML = panel(module.label, table(rows, module.columns, { caseLink: key === "signing-cases" }));
}

async function renderCurrentView() {
  renderNav();
  if (state.view === "dashboard") return renderDashboard();
  if (state.view === "search") return renderSearch();
  if (state.view === "case360") return renderCase360();
  if (state.view === "timeline") return renderTimeline();
  if (state.view === "priority") return renderPriority();
  if (state.view === "owners") return renderOwners();
  if (state.view === "vendors") return renderVendors();
  if (state.view === "excel") return renderExcel();
  if (state.view === "cmdb") return renderCmdb();
  if (state.view === "rules") return renderRules();
  if (state.view === "data") return renderDataMaintenance();
  return renderDashboard();
}

async function checkHealth() {
  try {
    const health = await api("/health");
    el.serviceStatus.textContent = health.database?.ok ? "服務正常" : "資料庫異常";
  } catch {
    el.serviceStatus.textContent = "服務無回應";
  }
}

el.nav.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-view]");
  if (!button) return;
  state.view = button.dataset.view;
  renderCurrentView().catch(showError);
});

el.workspace.addEventListener("click", (event) => {
  const viewButton = event.target.closest("button[data-view]");
  if (viewButton) {
    state.view = viewButton.dataset.view;
    renderCurrentView().catch(showError);
    return;
  }
  const drilldown = event.target.closest("button[data-drilldown]");
  if (drilldown) {
    renderDrilldown(drilldown.dataset.drilldown).catch(showError);
    return;
  }
  const caseLink = event.target.closest("[data-case-id]");
  if (caseLink) {
    state.view = "case360";
    renderNav();
    renderCase360(caseLink.dataset.caseId).catch(showError);
    return;
  }
  const dataModule = event.target.closest("button[data-data-module]");
  if (dataModule) {
    renderDataModule(dataModule.dataset.dataModule).catch(showError);
  }
});

el.workspace.addEventListener("click", (event) => {
  if (event.target.id === "searchButton") {
    const input = document.querySelector("#searchInput");
    renderSearch(input?.value || "").catch(showError);
  }
  if (event.target.id === "caseLoadButton") {
    const input = document.querySelector("#caseIdInput");
    renderCase360(input?.value || null).catch(showError);
  }
});

el.globalSearch.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  state.view = "search";
  renderNav();
  renderSearch(el.globalSearch.value).catch(showError);
});

el.roleSelect.addEventListener("change", () => {
  state.role = el.roleSelect.value;
  renderCurrentView().catch(showError);
});

el.refreshButton.addEventListener("click", () => {
  Promise.all([checkHealth(), renderCurrentView()]).catch(showError);
});

function showError(error) {
  el.workspace.innerHTML = panel("系統訊息", `<div class="empty-state"><h3>載入失敗</h3><p>${error.message}</p></div>`);
}

Promise.all([checkHealth(), renderCurrentView()]).catch(showError);
