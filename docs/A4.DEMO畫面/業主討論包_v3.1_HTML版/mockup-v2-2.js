document.querySelectorAll("table[data-sortable]").forEach((table) => {
  table.querySelectorAll("th button").forEach((button, columnIndex) => {
    button.addEventListener("click", () => {
      const tbody = table.tBodies[0];
      const rows = Array.from(tbody.rows);
      const direction = button.dataset.direction === "asc" ? "desc" : "asc";
      table.querySelectorAll("th button").forEach((item) => delete item.dataset.direction);
      button.dataset.direction = direction;
      rows.sort((a, b) => {
        const textA = a.cells[columnIndex].innerText.trim();
        const textB = b.cells[columnIndex].innerText.trim();
        return direction === "asc"
          ? textA.localeCompare(textB, "zh-Hant", { numeric: true })
          : textB.localeCompare(textA, "zh-Hant", { numeric: true });
      });
      rows.forEach((row) => tbody.appendChild(row));
    });
  });
});

document.querySelectorAll("[data-tabs]").forEach((tabs) => {
  const buttons = Array.from(tabs.querySelectorAll("[data-tab-target]"));
  const panels = buttons
    .map((button) => document.getElementById(button.dataset.tabTarget))
    .filter(Boolean);

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      buttons.forEach((item) => item.classList.toggle("active", item === button));
      panels.forEach((panel) => {
        panel.hidden = panel.id !== button.dataset.tabTarget;
      });
    });
  });
});

document.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener("click", (event) => {
    const panelId = link.getAttribute("href").slice(1);
    const targetButton = document.querySelector(`[data-tab-target="${panelId}"]`);
    if (!targetButton) return;
    event.preventDefault();
    targetButton.click();
    document.getElementById(panelId)?.scrollIntoView({ block: "nearest" });
  });
});
