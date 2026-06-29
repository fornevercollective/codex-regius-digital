(function () {
  const LAYERS = [
    { id: "artistic", label: "Artistic vellum", file: "artistic_vellum.jpg" },
    { id: "clean", label: "Clean white", file: "clean_white.jpg" },
    { id: "grok_artistic", label: "Grok vellum", file: "grok_artistic_vellum.jpg" },
    { id: "grok_clean", label: "Grok clean", file: "grok_clean_white.jpg" },
  ];

  const state = { page: 10, layer: "grok_clean", index: {} };

  function $(s) { return document.querySelector(s); }

  function pageDir(n) {
    return `processed/page_${String(n).padStart(3, "0")}`;
  }

  function pageMeta(n) {
    return state.index[n] || { status: "partial", poem: "" };
  }

  async function loadIndex() {
    try {
      const r = await fetch("data/hub_page_index.json");
      if (!r.ok) return;
      const data = await r.json();
      (data.pages || []).forEach((p) => { state.index[p.page] = p; });
    } catch (_) {}
  }

  function layerPath(page, file) {
    return `${pageDir(page)}/${file}`;
  }

  function updateView() {
    const meta = pageMeta(state.page);
    const layer = LAYERS.find((l) => l.id === state.layer) || LAYERS[3];
    const src = layerPath(state.page, layer.file);

    $("#current-page").textContent = state.page;
    $("#page-title").textContent = `Page ${state.page}`;
    $("#page-poem").textContent = meta.poem || "—";
    $("#page-status").textContent = meta.status || "partial";
    $("#page-status").className = `status-badge status-${meta.status || "partial"}`;
    $("#spread-img").src = src;
    $("#spread-img").alt = `GKS 2365 4to page ${state.page} — ${layer.label}`;
    $("#hub-link").href = `paleography-hub.html`;
    $("#assessment-link").href = `${pageDir(state.page)}/ai_assessment.md`;
    $("#page-input").value = state.page;

    LAYERS.forEach((l) => {
      const btn = document.querySelector(`[data-layer="${l.id}"]`);
      if (btn) btn.classList.toggle("active", l.id === state.layer);
    });

    $("#prev-btn").disabled = state.page <= 1;
    $("#next-btn").disabled = state.page >= 144;
  }

  function setPage(n) {
    state.page = Math.max(1, Math.min(144, n));
    const params = new URLSearchParams(location.search);
    params.set("page", state.page);
    history.replaceState(null, "", `?${params}`);
    updateView();
  }

  function setLayer(id) {
    state.layer = id;
    updateView();
  }

  function init() {
    const params = new URLSearchParams(location.search);
    const p = parseInt(params.get("page") || "10", 10);
    if (!Number.isNaN(p)) state.page = p;

    $("#prev-btn").addEventListener("click", () => setPage(state.page - 1));
    $("#next-btn").addEventListener("click", () => setPage(state.page + 1));
    $("#page-input").addEventListener("change", (e) => setPage(+e.target.value));
    document.querySelectorAll("[data-layer]").forEach((btn) => {
      btn.addEventListener("click", () => setLayer(btn.dataset.layer));
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") setPage(state.page - 1);
      if (e.key === "ArrowRight") setPage(state.page + 1);
    });

    loadIndex().then(updateView);
  }

  document.addEventListener("DOMContentLoaded", init);
})();