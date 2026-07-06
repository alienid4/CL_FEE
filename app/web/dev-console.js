const state = {
  status: null,
  busyCommand: "",
};

const selectors = {
  metrics: document.querySelector("#metrics"),
  commands: document.querySelector("#commands"),
  currentStatus: document.querySelector("#current-status"),
  startNext: document.querySelector("#start-next"),
  auditList: document.querySelector("#audit-list"),
  projectProfile: document.querySelector("#project-profile"),
  runtimeState: document.querySelector("#runtime-state"),
  commandOutput: document.querySelector("#command-output"),
  commandState: document.querySelector("#command-state"),
  statusVersion: document.querySelector("#status-version"),
  refresh: document.querySelector("#refresh"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatJson(value) {
  if (!value) return "No data";
  return JSON.stringify(value, null, 2);
}

function renderMetrics(payload) {
  const auditCount = payload.audit_entries?.length ?? 0;
  const commandCount = payload.commands?.length ?? 0;
  const runtimeStatus = payload.runtime_state?.status ?? "none";
  const commandMode = payload.safety?.command_mode ?? "unknown";
  selectors.metrics.innerHTML = [
    ["Commands", commandCount],
    ["Recent Audit", auditCount],
    ["Runtime", runtimeStatus],
    ["Command Mode", commandMode],
  ]
    .map(([label, value]) => `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`)
    .join("");
}

function renderCommands(commands) {
  selectors.commands.innerHTML = commands
    .map(
      (command) => `
        <button type="button" data-command="${escapeHtml(command.command_id)}" ${state.busyCommand ? "disabled" : ""}>
          ${escapeHtml(command.label)}
        </button>
      `,
    )
    .join("");
}

function renderAudit(entries) {
  if (!entries?.length) {
    selectors.auditList.innerHTML = '<div class="audit-item"><strong>No recent audit</strong><span>Run a local loop to create evidence.</span></div>';
    return;
  }
  selectors.auditList.innerHTML = entries
    .slice()
    .reverse()
    .map(
      (entry) => `
        <div class="audit-item">
          <strong>${escapeHtml(entry.goal || "Untitled")}</strong>
          <span>${escapeHtml(entry.timestamp || "")} | ${escapeHtml(entry.classification || "")} | ${escapeHtml(entry.audit_result || "")}</span>
          <span>${escapeHtml(entry.verification || "")}</span>
        </div>
      `,
    )
    .join("");
}

function render(payload) {
  state.status = payload;
  selectors.statusVersion.textContent = payload.version || "";
  selectors.currentStatus.textContent = payload.current_status || "No current status.";
  selectors.startNext.textContent = payload.start_next || "No next slice.";
  selectors.projectProfile.textContent = formatJson(payload.project_profile);
  selectors.runtimeState.textContent = formatJson(payload.runtime_state);
  renderMetrics(payload);
  renderCommands(payload.commands || []);
  renderAudit(payload.audit_entries || []);
}

async function loadStatus() {
  const response = await fetch("/api/dev-console/status");
  const payload = await response.json();
  render(payload.data);
}

async function runCommand(commandId) {
  state.busyCommand = commandId;
  selectors.commandState.textContent = `Running ${commandId}`;
  selectors.commandOutput.textContent = "";
  renderCommands(state.status?.commands || []);
  try {
    const response = await fetch("/api/dev-console/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command_id: commandId }),
    });
    const payload = await response.json();
    selectors.commandState.textContent = payload.data?.ok ? "Passed" : "Finished with findings";
    selectors.commandOutput.textContent = formatJson(payload.data);
    await loadStatus();
  } catch (error) {
    selectors.commandState.textContent = "Failed";
    selectors.commandOutput.textContent = String(error);
  } finally {
    state.busyCommand = "";
    renderCommands(state.status?.commands || []);
  }
}

selectors.refresh.addEventListener("click", loadStatus);
selectors.commands.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-command]");
  if (!button) return;
  runCommand(button.getAttribute("data-command"));
});

loadStatus();
