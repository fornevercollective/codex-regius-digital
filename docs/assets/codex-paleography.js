(function () {
  const LAYERS = [
    { id: "raw", label: "Raw", file: "raw.png", group: "base" },
    { id: "artistic", label: "Artistic vellum", file: "artistic_vellum.jpg", group: "base" },
    { id: "clean", label: "Clean white", file: "clean_white.jpg", group: "base" },
    { id: "grok_artistic", label: "Grok vellum", file: "grok_artistic_vellum.jpg", group: "grok" },
    { id: "grok_clean", label: "Grok clean", file: "grok_clean_white.jpg", group: "grok" },
  ];

  const BOOK_EXPORTS = [
    { id: "grok_clean_white", label: "Grok clean (book)", zip: "codex_regius_grok_clean_white.zip" },
    { id: "grok_artistic_vellum", label: "Grok vellum (book)", zip: "codex_regius_grok_artistic_vellum.zip" },
    { id: "clean_white", label: "Clean white (book)", zip: "codex_regius_clean_white.zip" },
    { id: "artistic_vellum", label: "Artistic vellum (book)", zip: "codex_regius_artistic_vellum.zip" },
    { id: "ai_assessment", label: "AI assessments (book)", zip: "codex_regius_ai_assessment.zip" },
  ];

  const PRESETS = {
    grok_clean: { label: "Grok clean", layers: { grok_clean: { on: true, opacity: 1 } } },
    grok_vellum: { label: "Grok vellum", layers: { grok_artistic: { on: true, opacity: 1 } } },
    raw: { label: "Raw scan", layers: { raw: { on: true, opacity: 1 } } },
    raw_grok_clean: { label: "Raw + Grok clean", mix: 50 },
    raw_grok_vellum: { label: "Raw + Grok vellum", layers: { raw: { on: true, opacity: 0.45 }, grok_artistic: { on: true, opacity: 0.95 } } },
    scholastic: { label: "Scholastic mix", layers: { clean: { on: true, opacity: 0.35 }, grok_clean: { on: true, opacity: 1 } } },
    full: { label: "Full stack", layers: { raw: { on: true, opacity: 0.2 }, artistic: { on: true, opacity: 0.25 }, grok_artistic: { on: true, opacity: 0.5 }, grok_clean: { on: true, opacity: 1 } } },
  };

  const CATEGORY_COLORS = {
    doodle: "rgba(201, 162, 39, 0.45)",
    calligraphy: "rgba(139, 90, 43, 0.25)",
    penmanship: "rgba(200, 100, 50, 0.35)",
    qc: "rgba(220, 60, 60, 0.4)",
    ocr: "rgba(100, 180, 255, 0.35)",
  };

  const state = {
    page: 10,
    year: 1270,
    data: {},
    pageIndex: {},
    layerState: {},
    layerAvailability: {},
    pageHighlights: null,
    glyphIndex: null,
    penmanship: null,
    transcription: "",
    animTimer: null,
    eventFilter: "",
    activePreset: "grok_clean",
    mixValue: 100,
  };

  async function loadJSON(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error(path);
    return r.json();
  }

  function $(sel) { return document.querySelector(sel); }
  function $all(sel) { return document.querySelectorAll(sel); }

  function pageDir(n) {
    return `processed/page_${String(n).padStart(3, "0")}`;
  }

  function pageMeta(n) {
    return state.pageIndex[n] || { status: "partial", layers: {} };
  }

  function pagesForFilter() {
    const idx = state.data.highlights;
    if (!state.eventFilter || !idx) return null;
    return new Set(idx.by_category?.[state.eventFilter] || []);
  }

  function renderPageList() {
    const list = $("#page-list");
    const filterSet = pagesForFilter();
    list.innerHTML = "";
    let shown = 0;
    for (let i = 1; i <= 144; i++) {
      if (filterSet && !filterSet.has(i)) continue;
      shown++;
      const meta = pageMeta(i);
      const b = document.createElement("button");
      b.type = "button";
      b.className = `page-pill status-${meta.status}` + (i === state.page ? " active" : "");
      b.textContent = i;
      b.dataset.page = i;
      b.title = `${meta.status} · ${meta.poem || "—"}`;
      b.addEventListener("click", () => selectPage(i));
      list.appendChild(b);
    }
    $("#page-filter-label").textContent = filterSet ? `(${shown} filtered)` : "(1–144)";
  }

  function selectPage(n) {
    state.page = n;
    $("#page-input").value = n;
    $all(".page-pill").forEach((el) => el.classList.toggle("active", +el.dataset.page === n));
    updatePageView();
  }

  function defaultLayerState() {
    const s = {};
    LAYERS.forEach((L) => { s[L.id] = { on: false, opacity: 1 }; });
    s.grok_clean = { on: true, opacity: 1 };
    return s;
  }

  function applyPreset(key) {
    const preset = PRESETS[key];
    if (!preset) return;
    state.activePreset = key;
    state.layerState = defaultLayerState();
    if (preset.mix !== undefined) {
      state.mixValue = preset.mix;
      $("#mix-slider").value = preset.mix;
      applyMix(preset.mix);
    } else if (preset.layers) {
      Object.entries(preset.layers).forEach(([id, cfg]) => {
        state.layerState[id] = { on: cfg.on, opacity: cfg.opacity };
      });
      applyLayerVisibility();
    }
    $all(".preset-btn").forEach((b) => b.classList.toggle("active", b.dataset.preset === key));
    renderLayerControls();
  }

  function applyMix(val) {
    state.mixValue = val;
    const t = val / 100;
    state.layerState.raw = { on: t < 1, opacity: 1 - t };
    state.layerState.grok_clean = { on: true, opacity: t || 0.01 };
    state.layerState.grok_artistic = { on: false, opacity: 0 };
    state.layerState.artistic = { on: false, opacity: 0 };
    state.layerState.clean = { on: false, opacity: 0 };
    $("#mix-value").textContent = t <= 0.02 ? "100% Raw" : t >= 0.98 ? "100% Grok clean" : `${Math.round((1 - t) * 100)}% Raw / ${Math.round(t * 100)}% Grok`;
    applyLayerVisibility();
    renderLayerControls();
  }

  function renderPresets() {
    const el = $("#layer-presets");
    el.innerHTML = Object.entries(PRESETS).map(([k, p]) =>
      `<button type="button" class="preset-btn${k === state.activePreset ? " active" : ""}" data-preset="${k}">${p.label}</button>`
    ).join("");
    el.querySelectorAll(".preset-btn").forEach((b) => {
      b.addEventListener("click", () => applyPreset(b.dataset.preset));
    });
  }

  function renderQuickToggles() {
    const el = $("#quick-toggles");
    const toggles = [
      { id: "raw", label: "Raw" },
      { id: "grok_artistic", label: "Grok vellum" },
      { id: "grok_clean", label: "Grok clean" },
    ];
    el.innerHTML = toggles.map((t) => {
      const on = state.layerState[t.id]?.on;
      return `<button type="button" class="toggle-btn${on ? " active" : ""}" data-toggle="${t.id}">${t.label}</button>`;
    }).join("");
    el.querySelectorAll(".toggle-btn").forEach((b) => {
      b.addEventListener("click", () => {
        const id = b.dataset.toggle;
        const cur = state.layerState[id] || { on: false, opacity: 1 };
        state.layerState[id] = { on: !cur.on, opacity: cur.opacity || 1 };
        state.activePreset = "";
        $all(".preset-btn").forEach((p) => p.classList.remove("active"));
        applyLayerVisibility();
        renderQuickToggles();
        renderLayerControls();
      });
    });
  }

  function renderLayerControls() {
    const el = $("#layer-controls");
    el.innerHTML = LAYERS.map((L) => {
      const s = state.layerState[L.id] || { on: false, opacity: 1 };
      const avail = state.layerAvailability[L.id] !== false;
      return `<label class="layer-control${avail ? "" : " missing"}" title="${avail ? L.label : "Not processed yet"}">
        <input type="checkbox" data-layer="${L.id}" ${s.on && avail ? "checked" : ""} ${avail ? "" : "disabled"} />
        ${L.label}
        <input type="range" min="0" max="100" value="${Math.round(s.opacity * 100)}" data-opacity="${L.id}" ${avail ? "" : "disabled"} />
      </label>`;
    }).join("");

    el.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.addEventListener("change", () => {
        state.layerState[cb.dataset.layer].on = cb.checked;
        state.activePreset = "";
        applyLayerVisibility();
        renderQuickToggles();
      });
    });
    el.querySelectorAll('input[type="range"]').forEach((rng) => {
      rng.addEventListener("input", () => {
        state.layerState[rng.dataset.opacity].opacity = rng.value / 100;
        state.layerState[rng.dataset.opacity].on = rng.value > 0;
        applyLayerVisibility();
      });
    });
  }

  function applyLayerVisibility() {
    $all(".layer-img").forEach((img) => {
      const id = img.dataset.layer;
      const s = state.layerState[id];
      const avail = state.layerAvailability[id] !== false;
      const show = avail && s?.on;
      img.style.opacity = show ? (s.opacity ?? 1) : 0;
      img.style.display = show ? "block" : "none";
    });
    drawHighlights();
  }

  async function buildLayerStack() {
    const dir = pageDir(state.page);
    const stack = $("#layer-stack");
    stack.innerHTML = "";
    state.layerAvailability = {};

    await Promise.all(LAYERS.map((L) => new Promise((resolve) => {
      const img = document.createElement("img");
      img.className = "layer-img";
      img.dataset.layer = L.id;
      img.alt = L.label;
      img.onload = () => { state.layerAvailability[L.id] = true; resolve(true); };
      img.onerror = () => { state.layerAvailability[L.id] = false; resolve(false); };
      img.src = `${dir}/${L.file}`;
      stack.appendChild(img);
    })));

    applyLayerVisibility();
    resizeHighlightCanvas();
  }

  function resizeHighlightCanvas() {
    const stack = $("#layer-stack");
    const canvas = $("#highlight-canvas");
    const rect = stack.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    drawHighlights();
  }

  function drawHighlights() {
    const canvas = $("#highlight-canvas");
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const cb = $("#show-highlights");
    if (!cb.checked || cb.disabled || !state.pageHighlights?.events?.length) return;

    state.pageHighlights.events.forEach((ev) => {
      const b = ev.bbox;
      if (!b || b.x === undefined) return;
      const x = b.x * canvas.width;
      const y = b.y * canvas.height;
      const w = (b.w || 0.05) * canvas.width;
      const h = (b.h || 0.05) * canvas.height;
      ctx.fillStyle = CATEGORY_COLORS[ev.category] || "rgba(255,255,0,0.3)";
      ctx.strokeStyle = "rgba(201, 162, 39, 0.9)";
      ctx.lineWidth = 2;
      ctx.fillRect(x, y, w, h);
      ctx.strokeRect(x, y, w, h);
    });
  }

  async function loadTranscription() {
    const dir = pageDir(state.page);
    state.transcription = "";
    try {
      const r = await fetch(`${dir}/ai_assessment.md`);
      if (!r.ok) return;
      const text = await r.text();
      const m = text.match(/## Original Text[^\n]*\n```\n([\s\S]*?)```/i);
      if (m && !/\[PASTE/i.test(m[1])) state.transcription = m[1].trim();
    } catch (_) { /* optional */ }
  }

  function renderTextOverlay() {
    const el = $("#text-overlay");
    const show = $("#show-text-layer").checked && state.transcription;
    el.hidden = !show;
    el.textContent = show ? state.transcription : "";
  }

  function renderDownloads() {
    const dir = pageDir(state.page);
    const meta = pageMeta(state.page);
    const pageDl = $("#page-downloads");
    pageDl.innerHTML = LAYERS.map((L) => {
      const avail = state.layerAvailability[L.id];
      return `<a class="btn-dl${avail ? "" : " missing"}" href="${dir}/${L.file}" download="page_${String(state.page).padStart(3, "0")}_${L.file}">${L.label}</a>`;
    }).join("") + `<a class="btn-dl" href="${dir}/ai_assessment.md" download="page_${String(state.page).padStart(3, "0")}_ai_assessment.md">Text MD</a>`;

    const bookDl = $("#book-downloads");
    bookDl.innerHTML = BOOK_EXPORTS.map((e) =>
      `<a class="btn-dl" href="exports/${e.zip}" download data-export="${e.zip}">${e.label}</a>`
    ).join("") + `<span class="empty" style="font-size:0.7rem;margin-left:0.5rem">Run <code>python3 tools/build_hub_exports.py</code> locally for zips</span>`;
    bookDl.querySelectorAll("[data-export]").forEach(async (a) => {
      try {
        const r = await fetch(a.href, { method: "HEAD" });
        if (!r.ok) a.classList.add("missing");
      } catch (_) {
        a.classList.add("missing");
      }
    });
  }

  function updateHighlightsToggle() {
    const cb = $("#show-highlights");
    const hint = $("#highlights-hint");
    const ready = state.data.hubIndex?.highlights_ready;
    if (ready) {
      cb.disabled = false;
      hint.textContent = "(doodles, glyphs, QC indexed)";
    } else {
      cb.checked = false;
      cb.disabled = true;
      hint.textContent = "(pending full tool index)";
    }
  }

  async function loadPageData() {
    state.pageHighlights = null;
    state.glyphIndex = null;
    state.penmanship = null;
    const dir = pageDir(state.page);
    try { state.pageHighlights = await loadJSON(`${dir}/page_highlights.json`); } catch (_) {}
    try { state.glyphIndex = await loadJSON(`${dir}/glyph_index.json`); } catch (_) {}
    try { state.penmanship = await loadJSON(`${dir}/penmanship_report.json`); } catch (_) {}
    await loadTranscription();
  }

  function renderGlyphs() {
    const el = $("#glyph-gallery");
    const glyphs = state.glyphIndex?.glyphs || [];
    if (!glyphs.length) {
      el.innerHTML = "<p class='empty'>No glyph crops yet — run glyph-pipeline.py on this page.</p>";
      return;
    }
    const dir = pageDir(state.page);
    el.innerHTML = glyphs.slice(0, 120).map((g) =>
      `<div class="glyph-thumb" title="${g.id}">
        <img src="${dir}/${g.file}" alt="${g.char}" loading="lazy" />
        <small>${g.char}</small>
      </div>`
    ).join("");
  }

  function renderPenmanship() {
    const m = state.penmanship?.metrics;
    const el = $("#penmanship-metrics");
    if (!m || !m.glyph_count) {
      el.innerHTML = "<p class='empty'>Run glyph-pipeline.py then grok-penmanship-script.py for metrics.</p>";
      $("#penmanship-summary").textContent = "";
      return;
    }
    el.innerHTML = `
      <div class="card"><h4>Flow</h4><p>${(m.flow_score * 100).toFixed(0)}%</p></div>
      <div class="card"><h4>Dexterity</h4><p>${(m.dexterity_score * 100).toFixed(0)}%</p></div>
      <div class="card"><h4>Speed</h4><p>${m.speed_estimate}</p></div>
      <div class="card"><h4>Glyphs</h4><p>${m.glyph_count}</p></div>`;
    $("#penmanship-summary").textContent = state.penmanship.assessment || "";
  }

  function playAnimation() {
    if (state.animTimer) clearInterval(state.animTimer);
    const glyphs = state.glyphIndex?.glyphs || [];
    const grokSeq = state.penmanship?.grok_penmanship?.animation_sequence || [];
    const dir = pageDir(state.page);
    const stage = $("#animation-glyph");
    const cap = $("#animation-caption");
    if (!glyphs.length && !grokSeq.length) {
      cap.textContent = "No glyph sequence available.";
      return;
    }
    let i = 0;
    const steps = grokSeq.length
      ? grokSeq.map((s, idx) => ({ caption: s.stroke_style || s.letter_hint, glyph: glyphs[idx] }))
      : glyphs.map((g) => ({ caption: `Stroke ${g.reading_order + 1}: ${g.char}`, glyph: g }));
    function tick() {
      const step = steps[i % steps.length];
      stage.classList.remove("writing");
      void stage.offsetWidth;
      stage.classList.add("writing");
      if (step.glyph) {
        stage.innerHTML = `<img src="${dir}/${step.glyph.file}" alt="${step.glyph.char}" />`;
      } else {
        stage.textContent = step.caption?.[0] || "—";
      }
      cap.textContent = step.caption || "";
      i++;
    }
    tick();
    state.animTimer = setInterval(tick, 700);
  }

  function renderPageEvents() {
    const list = $("#page-events-list");
    const events = state.pageHighlights?.events || [];
    list.innerHTML = events.length
      ? events.map((e) => `<li><span class="event-chip">${e.category}</span> <strong>${e.type}</strong>: ${e.label}</li>`).join("")
      : "<li class='empty'>No events indexed for this page.</li>";
  }

  function renderEventIndex() {
    const idx = state.data.highlights;
    const el = $("#event-index");
    if (!idx?.by_category) {
      el.innerHTML = "<p class='empty'>Run glyph-pipeline.py --all to build page_highlights.json</p>";
      return;
    }
    let html = `<p><strong>${idx.pages_with_events}</strong> pages with events (of ${idx.pages_total})</p><ul>`;
    Object.entries(idx.by_category).forEach(([cat, pages]) => {
      html += `<li><span class="event-chip">${cat}</span> ${pages.length} pages</li>`;
    });
    html += "</ul>";
    el.innerHTML = html;
  }

  function renderTimeline() {
    const scribe = state.data.scribe || {};
    const items = (scribe.timeline || []).filter((t) => state.year >= t.year - 30 && state.year <= t.year + 30);
    const el = $("#scribe-timeline");
    el.innerHTML = items.length ? items.map((t) => `
      <div class="timeline-item">
        <div class="timeline-year">${t.era || ""} ${t.year}</div>
        <div>${t.event}</div>
        <small>${t.type || ""}</small>
      </div>`).join("") : "<p class='empty'>Adjust year slider to explore scribe context.</p>";
  }

  function renderAlphabet() {
    const letters = (state.data.alphabet || {}).letters || [];
    $("#alphabet-grid").innerHTML = letters.map((L) => `
      <div class="letter-cell" title="${(L.variants || []).join(", ")}">
        ${L.char}<small>${L.name}</small>
      </div>`).join("");
  }

  function renderCodicology() {
    const v = (state.data.codicology || {}).vellum || {};
    $("#codicology-body").innerHTML = `
      <div class="card-grid">
        <div class="card"><h4>Animal</h4><p>${v.animal || "—"}</p></div>
        <div class="card"><h4>Region</h4><p>${v.region_origin || "—"}</p></div>
        <div class="card"><h4>Age</h4><p>${v.age_estimate || "—"}</p></div>
        <div class="card"><h4>Preparation</h4><p>${(v.preparation || {}).fiber_pattern || "—"}</p></div>
      </div>`;
  }

  function pagePoemEntry(page) {
    return (state.data.liturgy?.page_index || []).find((e) => e.page === page) || null;
  }

  function renderLiturgy() {
    const lit = state.data.liturgy || {};
    const themes = (state.data.themes || {}).themes || [];
    const poem = pagePoemEntry(state.page);
    let html = "<h4>Witness manuscripts</h4><table><tr><th>Siglum</th><th>Name</th><th>Date</th></tr>";
    (lit.witnesses || []).forEach((w) => {
      html += `<tr><td>${w.siglum}</td><td>${w.name}</td><td>${w.date}</td></tr>`;
    });
    html += "</table>";
    if (poem?.poem) {
      html += `<h4>Poem on this page</h4><p><strong>${poem.poem}</strong><br><small>${poem.section || ""}</small></p>`;
    }
    html += "<h4>Thematic parallels</h4><ul>";
    themes.forEach((t) => {
      html += `<li><strong>${t.label}</strong></li>`;
    });
    html += "</ul>";
    $("#liturgy-body").innerHTML = html;
  }

  async function updatePageView() {
    const dir = pageDir(state.page);
    const meta = pageMeta(state.page);
    $("#page-title").textContent = `Page ${state.page} · ${meta.poem || "—"} (${meta.status})`;
    await loadPageData();
    await buildLayerStack();
    renderLayerControls();
    renderQuickToggles();
    renderDownloads();
    renderTextOverlay();
    renderGlyphs();
    renderPenmanship();
    renderPageEvents();
    renderLiturgy();

    const links = [
      ["AI Assessment", `${dir}/ai_assessment.md`],
      ["Doodles", `${dir}/doodles_catalog.md`],
      ["Glyph index", `${dir}/glyph_index.json`],
      ["Penmanship", `${dir}/penmanship_report.json`],
    ];
    $("#page-links").innerHTML = links.map(([l, h]) =>
      `<a href="${h}" class="btn" style="margin-right:0.5rem">${l}</a>`
    ).join("");
  }

  function setupTabs() {
    $all(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        $all(".tab").forEach((t) => t.classList.remove("active"));
        $all(".tabpanel").forEach((p) => p.classList.remove("active"));
        tab.classList.add("active");
        $(`#${tab.dataset.tab}`).classList.add("active");
      });
    });
  }

  async function init() {
    try {
      const [codicology, scribe, alphabet, liturgy, themes, highlights, hubIndex] = await Promise.all([
        loadJSON("data/codicology.json"),
        loadJSON("data/scribe_timeline.json"),
        loadJSON("data/alphabet_reference.json"),
        loadJSON("data/liturgy_comparisons.json"),
        loadJSON("data/thematic_crossrefs.json"),
        loadJSON("data/page_highlights.json").catch(() => null),
        loadJSON("data/hub_page_index.json").catch(() => null),
      ]);
      state.data = { codicology, scribe, alphabet, liturgy, themes, highlights, hubIndex };
      if (hubIndex?.pages) {
        hubIndex.pages.forEach((p) => { state.pageIndex[p.page] = p; });
      }
    } catch (e) {
      console.warn("Data load:", e);
    }

    state.layerState = defaultLayerState();
    renderPresets();
    applyPreset("grok_clean");
    updateHighlightsToggle();
    renderPageList();
    renderEventIndex();
    renderCodicology();
    renderAlphabet();
    renderTimeline();
    await updatePageView();
    setupTabs();

    $("#page-input").addEventListener("change", (e) => selectPage(+e.target.value));
    $("#event-filter").addEventListener("change", (e) => {
      state.eventFilter = e.target.value;
      renderPageList();
    });
    $("#year-slider").addEventListener("input", (e) => {
      state.year = +e.target.value;
      $("#year-value").textContent = state.year;
      renderTimeline();
    });
    $("#export-font-btn")?.addEventListener("click", () => {
      const a = document.createElement("a");
      a.href = "data/codex_regius_font.json";
      a.download = "codex_regius_font.json";
      a.click();
    });
    $("#show-highlights").addEventListener("change", drawHighlights);
    $("#show-text-layer").addEventListener("change", renderTextOverlay);
    $("#mix-slider").addEventListener("input", (e) => {
      state.activePreset = "";
      $all(".preset-btn").forEach((p) => p.classList.remove("active"));
      applyMix(+e.target.value);
    });
    $("#play-animation-btn").addEventListener("click", playAnimation);
    window.addEventListener("resize", resizeHighlightCanvas);
  }

  document.addEventListener("DOMContentLoaded", init);
})();