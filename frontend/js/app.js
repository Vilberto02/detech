// Estado global
const state = {
  files: [], // File objects seleccionados
  reportData: null, // Último reporte retornado por la API
};

// Elementos del DOM
const $ = (id) => document.getElementById(id);

const els = {
  dropZone: $("drop-zone"),
  fileInput: $("file-input"),
  browseBtn: $("browse-btn"),
  fileList: $("file-list"),
  uploadActions: $("upload-actions"),
  analyzeBtn: $("analyze-btn"),
  clearBtn: $("clear-btn"),
  loadingOverlay: $("loading-overlay"),
  resultsSection: $("results-section"),
  uploadCard: $("upload-card"),

  // Stats
  statFiles: $("stat-files"),
  statCritical: $("stat-critical"),
  statWarning: $("stat-warning"),
  statInfo: $("stat-info"),

  // Results
  filterTabs: $("filter-tabs"),
  searchInput: $("search-input"),
  resultsContent: $("results-content"),

  // Export
  exportHtmlBtn: $("export-html-btn"),
  exportPdfBtn: $("export-pdf-btn"),
  newAnalysisBtn: $("new-analysis-btn"),

  // Theme Toggle
  themeToggle: $("theme-toggle"),
};

// Toggle de Tema Oscuro
if (els.themeToggle) {
  els.themeToggle.addEventListener("click", () => {
    document.documentElement.classList.toggle("dark");
  });
}

// Drag & Drop
["dragenter", "dragover", "dragleave", "drop"].forEach((ev) => {
  els.dropZone.addEventListener(ev, (e) => {
    e.preventDefault();
    e.stopPropagation();
  });
  document.body.addEventListener(ev, (e) => {
    e.preventDefault();
    e.stopPropagation();
  });
});

els.dropZone.addEventListener("dragenter", () =>
  els.dropZone.classList.add("drag-over"),
);
els.dropZone.addEventListener("dragover", () =>
  els.dropZone.classList.add("drag-over"),
);
els.dropZone.addEventListener("dragleave", () =>
  els.dropZone.classList.remove("drag-over"),
);

els.dropZone.addEventListener("drop", (e) => {
  els.dropZone.classList.remove("drag-over");
  const files = Array.from(e.dataTransfer.files);
  if (files.length) addFiles(files);
});

els.dropZone.addEventListener("click", (e) => {
  if (e.target === els.browseBtn || els.browseBtn.contains(e.target)) return;
  els.fileInput.click();
});

els.browseBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  els.fileInput.click();
});

els.fileInput.addEventListener("change", () => {
  const files = Array.from(els.fileInput.files);
  if (files.length) addFiles(files);
  els.fileInput.value = "";
});

// Gestión de archivos
function addFiles(newFiles) {
  newFiles.forEach((f) => {
    if (!state.files.find((x) => x.name === f.name && x.size === f.size)) {
      state.files.push(f);
    }
  });
  renderFileList();
}

function removeFile(index) {
  state.files.splice(index, 1);
  renderFileList();
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function renderFileList() {
  const hasFiles = state.files.length > 0;
  els.fileList.classList.toggle("hidden", !hasFiles);
  els.uploadActions.style.display = hasFiles ? "flex" : "none";

  els.fileList.innerHTML = state.files
    .map(
      (f, i) => `
    <div class="file-item" id="file-item-${i}">
      <div class="file-icon">.${escapeHtml(f.name.split('.').pop())}</div>
      <div class="file-info">
        <div class="file-name">${escapeHtml(f.name)}</div>
        <div class="file-size">${formatBytes(f.size)}</div>
      </div>
      <button class="file-remove" onclick="removeFile(${i})" title="Quitar archivo" id="remove-file-${i}">
        <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
        </svg>
      </button>
    </div>
  `,
    )
    .join("");
}

els.clearBtn.addEventListener("click", () => {
  state.files = [];
  renderFileList();
});

// Análisis
els.analyzeBtn.addEventListener("click", runAnalysis);

async function runAnalysis() {
  if (!state.files.length) return;

  setLoading(true);

  try {
    const formData = new FormData();
    state.files.forEach((f) => formData.append("files", f, f.name));

    const res = await fetch("/api/analyze", { method: "POST", body: formData });

    if (!res.ok) {
      const err = await res
        .json()
        .catch(() => ({ detail: "Error desconocido" }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    state.reportData = await res.json();
    renderResults(state.reportData);
  } catch (err) {
    showError(`Error al analizar: ${err.message}`);
  } finally {
    setLoading(false);
  }
}

function setLoading(active) {
  els.loadingOverlay.classList.toggle("hidden", !active);
  els.analyzeBtn.disabled = active;
}

// Renderizado de resultados
function renderResults(data) {
  // Mostrar sección de resultados
  els.resultsSection.classList.remove("hidden");
  els.resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  // Animar contadores
  animateCount(els.statFiles, 0, data.summary.total_files);
  animateCount(els.statCritical, 0, data.summary.critical);
  animateCount(els.statWarning, 0, data.summary.warning);
  animateCount(els.statInfo, 0, data.summary.info);

  // Renderizar archivos
  els.resultsContent.innerHTML = data.files
    .map((f) => renderFileCard(f))
    .join("");
}

function renderFileCard(fileData) {
  const hasAnomalies = fileData.anomalies.length > 0;

  const badgesHtml = hasAnomalies
    ? `
    ${fileData.critical > 0 ? `<span class="badge badge-critical">⚠ ${fileData.critical} crítico${fileData.critical !== 1 ? "s" : ""}</span>` : ""}
    ${fileData.warning > 0 ? `<span class="badge badge-warning">! ${fileData.warning} advertencia${fileData.warning !== 1 ? "s" : ""}</span>` : ""}
    ${fileData.info > 0 ? `<span class="badge badge-info">ℹ ${fileData.info} info</span>` : ""}
  `
    : `<span class="badge badge-success">Sin anomalías</span>`;

  const rowsHtml = hasAnomalies
    ? fileData.anomalies
        .map(
          (a) => `
        <tr class="anomaly-row" data-category="${a.category}" data-severity="${a.severity}"
            data-search="${escapeHtml((a.message + " " + a.rule_id + " " + a.context).toLowerCase())}">
          <td class="col-line">#${a.line}</td>
          <td class="col-rule">${escapeHtml(a.rule_id)}</td>
          <td><span class="badge badge-${a.severity === "critical" ? "critical" : a.severity === "warning" ? "warning" : "info"}">${severityLabel(a.severity)}</span></td>
          <td class="col-message">${escapeHtml(a.message)}</td>
          <td class="col-context" title="${escapeHtml(a.context)}">${a.context ? `<code>${escapeHtml(a.context)}</code>` : "—"}</td>
        </tr>
      `,
        )
        .join("")
    : `<tr><td colspan="5" class="no-anomalies">
          <div>No se detectaron anomalías en este archivo</div>
       </td></tr>`;

  const tableHtml = `
    <div class="table-wrapper">
      <table class="table">
        <thead>
          <tr>
            <th>Línea</th>
            <th>Regla</th>
            <th>Severidad</th>
            <th>Descripción</th>
            <th>Contexto</th>
          </tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>
  `;

  return `
    <div class="model-card">
      <div class="model-card-header">
        <div class="model-card-title">
          📄 ${escapeHtml(fileData.filepath)}
        </div>
        <div class="model-card-meta">
          <span class="badge " style="background:var(--surface-bone); color:var(--ink);">${fileData.total_lines} líneas</span>
          ${badgesHtml}
        </div>
      </div>
      ${tableHtml}
    </div>
  `;
}

function severityLabel(s) {
  return s === "critical"
    ? "Crítico"
    : s === "warning"
      ? "Advertencia"
      : "Info";
}

// Filtrado
els.filterTabs.addEventListener("click", (e) => {
  const tab = e.target.closest(".sub-nav-pill");
  if (!tab) return;
  document
    .querySelectorAll(".sub-nav-pill")
    .forEach((t) => t.classList.remove("active"));
  tab.classList.add("active");
  applyFilters();
});

els.searchInput.addEventListener("input", applyFilters);

function applyFilters() {
  const activeTab = document.querySelector(".sub-nav-pill.active");
  const category = activeTab?.dataset.filter || "all";
  const search = els.searchInput.value.toLowerCase().trim();

  document.querySelectorAll(".anomaly-row").forEach((row) => {
    const catMatch = category === "all" || row.dataset.category === category;
    const searchMatch = !search || row.dataset.search.includes(search);
    row.classList.toggle("hidden-row", !(catMatch && searchMatch));
  });
}

// Exportar reportes
els.exportHtmlBtn.addEventListener("click", () => exportReport("html"));
els.exportJsonBtn = $("export-json-btn");
if (els.exportJsonBtn) {
  els.exportJsonBtn.addEventListener("click", () => exportReport("json"));
}

async function exportReport(format) {
  if (!state.reportData) return;

  const btn = format === "html" ? els.exportHtmlBtn : els.exportJsonBtn;
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span>Generando...</span>`;

  try {
    if (format === "json") {
      // Exportación directa a JSON
      const jsonStr = JSON.stringify(state.reportData, null, 2);
      const blob = new Blob([jsonStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `detech_report.json`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      // Exportación a HTML como archivo descargable
      const res = await fetch(`/api/report?format=html`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state.reportData),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `detech_report.html`;
      a.click();
      URL.revokeObjectURL(url);
    }
  } catch (err) {
    showError(`No se pudo exportar el reporte: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

// Nuevo análisis
els.newAnalysisBtn.addEventListener("click", () => {
  state.files = [];
  state.reportData = null;
  renderFileList();
  els.resultsSection.classList.add("hidden");
  els.resultsContent.innerHTML = "";
  els.searchInput.value = "";
  document
    .querySelectorAll(".sub-nav-pill")
    .forEach((t) => t.classList.remove("active"));
  $("tab-all").classList.add("active");
  document
    .querySelector("#upload-section")
    .scrollIntoView({ behavior: "smooth" });
});

// Animación de contadores
function animateCount(el, from, to) {
  const duration = 600;
  const start = performance.now();
  const update = (now) => {
    const t = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = Math.round(from + (to - from) * eased);
    if (t < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

// Utilidades
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showError(msg) {
  const el = document.createElement("div");
  el.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 999;
    background: var(--surface-dark); border: 1px solid var(--critical);
    color: var(--on-dark); padding: 14px 20px; border-radius: var(--rounded-md);
    font-size: 14px; max-width: 360px;
    animation: slide-in 0.2s ease;
  `;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}
