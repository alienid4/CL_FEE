(function () {
  var storageKey = "fee-workbench-menu-state";

  function readState() {
    try {
      return JSON.parse(localStorage.getItem(storageKey) || "{}");
    } catch (error) {
      return {};
    }
  }

  function writeState(state) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
    } catch (error) {
      return;
    }
  }

  function setOpen(group, isOpen) {
    var toggle = group.querySelector(".menu-toggle");
    group.classList.toggle("is-collapsed", !isOpen);
    if (toggle) {
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    }
  }

  function setPinned(group, isPinned) {
    var pin = group.querySelector(".menu-pin");
    group.classList.toggle("is-pinned", isPinned);
    if (pin) {
      pin.setAttribute("aria-pressed", isPinned ? "true" : "false");
    }
  }

  var state = readState();
  var groups = Array.prototype.slice.call(document.querySelectorAll(".menu-group[data-menu-group]"));

  groups.forEach(function (group) {
    var key = group.getAttribute("data-menu-group");
    var saved = state[key];
    var hasActiveItem = !!group.querySelector(".menu-item.active");
    var isPinned = !!(saved && saved.pinned);
    var isOpen = isPinned ? !!saved.open : hasActiveItem;
    var toggle = group.querySelector(".menu-toggle");
    var pin = group.querySelector(".menu-pin");

    setOpen(group, isOpen);
    setPinned(group, isPinned);

    if (toggle) {
      toggle.addEventListener("click", function () {
        var nextOpen = group.classList.contains("is-collapsed");
        setOpen(group, nextOpen);

        if (state[key] && state[key].pinned) {
          state[key].open = nextOpen;
          writeState(state);
        }
      });
    }

    if (pin) {
      pin.addEventListener("click", function () {
        var nextPinned = !(state[key] && state[key].pinned);
        var currentOpen = !group.classList.contains("is-collapsed");

        if (nextPinned) {
          state[key] = { pinned: true, open: currentOpen };
        } else {
          delete state[key];
        }

        writeState(state);
        setPinned(group, nextPinned);
      });
    }
  });
})();

document.querySelectorAll("table[data-sortable]").forEach(function (table) {
  table.querySelectorAll("th button").forEach(function (button, columnIndex) {
    button.addEventListener("click", function () {
      var tbody = table.tBodies[0];
      var rows = Array.prototype.slice.call(tbody.rows);
      var direction = button.dataset.direction === "asc" ? "desc" : "asc";

      table.querySelectorAll("th button").forEach(function (item) {
        delete item.dataset.direction;
      });

      button.dataset.direction = direction;
      rows.sort(function (a, b) {
        var textA = a.cells[columnIndex].innerText.trim();
        var textB = b.cells[columnIndex].innerText.trim();
        return direction === "asc"
          ? textA.localeCompare(textB, "zh-Hant", { numeric: true })
          : textB.localeCompare(textA, "zh-Hant", { numeric: true });
      });
      rows.forEach(function (row) {
        tbody.appendChild(row);
      });
    });
  });
});

document.querySelectorAll("[data-tabs]").forEach(function (tabs) {
  var buttons = Array.prototype.slice.call(tabs.querySelectorAll("[data-tab-target]"));
  var panels = buttons
    .map(function (button) {
      return document.getElementById(button.dataset.tabTarget);
    })
    .filter(Boolean);

  buttons.forEach(function (button) {
    button.addEventListener("click", function () {
      buttons.forEach(function (item) {
        item.classList.toggle("active", item === button);
      });
      panels.forEach(function (panel) {
        panel.hidden = panel.id !== button.dataset.tabTarget;
      });
    });
  });
});

document.querySelectorAll('a[href^="#"]').forEach(function (link) {
  link.addEventListener("click", function (event) {
    var panelId = link.getAttribute("href").slice(1);
    var targetButton = document.querySelector('[data-tab-target="' + panelId + '"]');
    if (!targetButton) return;
    event.preventDefault();
    targetButton.click();
    var panel = document.getElementById(panelId);
    if (panel) {
      panel.scrollIntoView({ block: "nearest" });
    }
  });
});
