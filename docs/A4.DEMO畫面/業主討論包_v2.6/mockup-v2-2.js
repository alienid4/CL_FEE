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
