(function () {
  const LAYERS = [
    { id: "raw", label: "Raw", file: "raw.png", group: "base" },
    { id: "artistic", label: "Artistic vellum", file: "artistic_vellum.jpg", group: "base" },
    { id: "clean", label: "Clean white", file: "clean_white.jpg", group: "base" },
    { id: "grok_artistic", label: "Grok vellum", file: "grok_artistic_vellum.jpg", group: "grok" },
    { id: "grok_clean", label: "Grok clean", file: "grok_clean_white.jpg", group: "grok" },
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

    renderBookDownloads();
  }

  async function renderBookDownloads() {
    const bookDl = $("#book-downloads");
    let manifest = state.data.exportManifest;
    if (!manifest) {
      try {
        manifest = await loadJSON("exports/manifest.json");
        state.data.exportManifest = manifest;
      } catch (_) {
        bookDl.innerHTML = `<span class="empty">Run <code>python3 tools/build_hub_exports.py</code> to build book downloads</span>`;
        return;
      }
    }
    const labels = {
      artistic_vellum: "Artistic vellum",
      clean_white: "Clean white",
      grok_artistic_vellum: "Grok vellum",
      grok_clean_white: "Grok clean",
      ai_assessment: "AI assessments",
    };
    const onPages = location.hostname.includes("github.io");
    const exportBase = onPages
      ? "https://media.githubusercontent.com/media/fornevercollective/codex-regius-digital/main/exports/"
      : "exports/";
    let html = "";
    (manifest.variations || []).forEach((v) => {
      const label = labels[v.id] || v.id;
      (v.parts || []).forEach((p) => {
        const range = p.page_start === p.page_end ? `p${p.page_start}` : `p${p.page_start}–${p.page_end}`;
        const mb = (p.bytes / (1024 * 1024)).toFixed(0);
        html += `<a class="btn-dl" href="${exportBase}${p.file}" download title="${mb} MB">${label} (${range})</a>`;
      });
    });
    bookDl.innerHTML = html || `<span class="empty">No exports built yet</span>`;
    bookDl.querySelectorAll("a.btn-dl").forEach(async (a) => {
      try {
        const r = await fetch(a.getAttribute("href"), { method: "HEAD" });
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

  function runicPageEntry(page) {
    return (state.data.runic?.page_index || []).find((e) => e.page === page) || null;
  }

  function renderRunicOverview() {
    const o = state.data.runic?.overview || {};
    const cats = state.data.runic?.artifact_categories || [];
    $("#runic-overview").innerHTML = `
      <div class="card"><h4>Codex date</h4><p>${o.codex_date || "—"}</p></div>
      <div class="card"><h4>Primary witness?</h4><p>${o.is_primary_complete_witness ? "Yes — most complete Eddic vellum" : "—"}</p></div>
      <div class="card"><h4>Oldest poem artifact?</h4><p>${o.is_oldest_poetic_artifact ? "Yes" : "No — runic carvings earlier"}</p></div>
      <div class="card" style="grid-column:1/-1"><h4>Scholarly note</h4><p>${o.summary || ""}</p>
        <p style="margin-top:0.5rem;font-size:0.85rem"><strong>Older traditions:</strong> ${(o.older_traditions || []).join(" · ")}</p></div>
      ${cats.map((c) => `<div class="card"><h4>${c.label}</h4><p style="font-size:0.85rem">${c.description}</p></div>`).join("")}`;
  }

  function renderRunicPage() {
    const entry = runicPageEntry(state.page);
    const poem = pagePoemEntry(state.page);
    const links = (state.data.runic?.stanza_links || []).filter((s) => (s.pages_cr || []).includes(state.page));
    const el = $("#runic-page-body");
    if (!entry && !links.length) {
      el.innerHTML = `<p class="empty">No indexed runic parallels for page ${state.page} yet. Poem: <strong>${poem?.poem || "—"}</strong></p>`;
      return;
    }
    let html = `<p><strong>${poem?.poem || "—"}</strong> · ${poem?.section || ""}</p>`;
    if (entry?.poem_summary) {
      html += `<p class="runic-density">Runic density: <strong>${entry.poem_summary.runic_density}</strong> — ${entry.poem_summary.summary}</p>`;
    }
    if (links.length) {
      html += "<h4>Stanza links</h4><table><tr><th>Poem</th><th>St.</th><th>CR text</th><th>Match</th><th>Note</th></tr>";
      links.forEach((l) => {
        html += `<tr><td>${l.poem}</td><td>${l.stanza ?? "—"}</td><td><code>${(l.cr_text || "").slice(0, 60)}</code></td><td>${l.match_type}</td><td>${l.note}</td></tr>`;
      });
      html += "</table>";
    }
    const arts = entry?.artifacts || [];
    if (arts.length) {
      html += "<h4>Artifacts</h4><ul class='runic-artifact-list'>";
      arts.forEach((a) => {
        html += `<li><strong>${a.name}</strong> (${a.date}) · ${a.type.replace("_", " ")}<br><small>${a.note}</small><br><em>${a.reference || ""}</em></li>`;
      });
      html += "</ul>";
    }
    el.innerHTML = html;
  }

  function renderRunicCorpusTable() {
    const artifacts = state.data.runic?.artifacts || [];
    const summaries = state.data.runic?.poem_summaries || [];
    let html = "<table><tr><th>Poem / region</th><th>Pages</th><th>Runic density</th><th>Key artifacts</th></tr>";
    summaries.forEach((s) => {
      const arts = artifacts.filter((a) => (a.poems || []).some((p) => s.poem.includes(p) || p.includes(s.poem.split(" ")[0])));
      html += `<tr><td>${s.poem}</td><td>${s.page_start}–${s.page_end}</td><td>${s.runic_density}</td><td>${arts.map((a) => a.name).join("; ") || "—"}</td></tr>`;
    });
    html += "</table><h4>All catalogued artifacts</h4><table><tr><th>Name</th><th>Type</th><th>Date</th><th>Poems</th><th>Relation</th></tr>";
    artifacts.forEach((a) => {
      html += `<tr><td>${a.name}</td><td>${a.type}</td><td>${a.date}</td><td>${(a.poems || []).join(", ")}</td><td>${a.relation}</td></tr>`;
    });
    html += "</table>";
    $("#runic-corpus-table").innerHTML = html;
  }

  function renderRunic() {
    if (!$("#runic-overview")) return;
    renderRunicOverview();
    renderRunicPage();
    renderRunicCorpusTable();
  }

  function folioEntry(page) {
    const folios = state.data.viscoll?.folios || [];
    return folios.find((f) => f.page === page) || null;
  }

  function quireEntry(quireId) {
    const quires = state.data.viscoll?.quires || [];
    return quires.find((q) => q.id === quireId) || null;
  }

  function renderCompletionSnapshot() {
    const el = $("#completion-snapshot");
    if (!el) return;
    const snap = state.data.completion;
    if (!snap?.summary) {
      el.innerHTML = '<p class="empty">Run <code>python3 tools/build_completion_snapshot.py</code></p>';
      return;
    }
    const total = snap.pages_total || 144;
    const qc = snap.qc || {};
    const items = Object.entries(snap.summary).map(([key, val]) => {
      const count = val.count ?? 0;
      const pct = Math.round((count / total) * 100);
      const warn = pct < 100;
      const missing = (val.missing || []).length;
      return `<div class="completion-card${warn ? " warn" : ""}">
        <div class="label">${key}</div>
        <div class="completion-pct">${count}/${total}</div>
        <div class="completion-bar"><span style="width:${pct}%"></span></div>
        <small>${warn ? `${missing} missing` : "complete"}</small>
      </div>`;
    });
    items.push(`<div class="completion-card${qc.needs_review ? " warn" : ""}">
      <div class="label">QC review</div>
      <div class="completion-pct">${qc.ok || 0} ok · ${qc.needs_review || 0} review</div>
      <div class="completion-bar"><span style="width:${Math.round(((qc.ok || 0) / total) * 100)}%"></span></div>
      <small>${qc.needs_review || 0} pages flagged</small>
    </div>`);
    el.innerHTML = items.join("");
  }

  function renderFolioPlacement() {
    const folio = folioEntry(state.page);
    const place = $("#folio-placement");
    const quireEl = $("#quire-context");
    if (!place) return;
    if (!folio) {
      place.innerHTML = '<p class="empty">No VisColl folio map — run build_viscoll_collation.py</p>';
      if (quireEl) quireEl.innerHTML = "";
      return;
    }
    const spineActive = folio.binding_edge === "spine";
    const foreActive = folio.binding_edge === "fore-edge";
    place.innerHTML = `
      <div class="folio-diagram" aria-label="Folio ${folio.folio} ${folio.side}">
        <div class="folio-edge spine${spineActive ? " active" : ""}" title="Spine / binding">Spine</div>
        <div class="folio-face">
          <div class="siglum">${folio.folio}</div>
          <div>${folio.side === "recto" ? "Recto" : "Verso"} · digital page ${folio.page}</div>
          <div class="folio-meta">
            <span>Quire ${folio.quire}</span>
            <span>Pos ${folio.position_in_quire}/8</span>
            ${folio.signature ? `<span>Sig. ${folio.signature}</span>` : "<span>Signature —</span>"}
            ${folio.catchword ? `<span>Catchword: ${folio.catchword}</span>` : ""}
          </div>
        </div>
        <div class="folio-edge fore${foreActive ? " active" : ""}" title="Fore-edge">Fore</div>
      </div>
      <p style="font-size:0.8rem;opacity:0.85;margin-top:0.5rem">
        Binding edge: <strong>${folio.binding_edge}</strong> —
        ${spineActive ? "gutter at spine (inner margin)" : "outer margin at fore-edge"}.
        Scaffold quire map; verify against physical collation (<a href="https://viscoll.org" target="_blank" rel="noopener">VisColl</a>).
      </p>`;
    const q = quireEntry(folio.quire);
    if (quireEl && q) {
      let cells = "";
      for (let p = q.page_start; p <= q.page_end; p++) {
        cells += `<div class="quire-cell${p === state.page ? " current" : ""}" title="Page ${p}">${p}</div>`;
      }
      quireEl.innerHTML = `<p style="font-size:0.8rem;margin:0 0 0.35rem"><strong>${q.id}</strong> · folios ${q.page_start}–${q.page_end} (${q.leaves} leaves)</p><div class="quire-strip">${cells}</div>`;
    }
  }

  function renderTeiCatalog() {
    const el = $("#tei-catalog");
    if (!el) return;
    const tei = state.data.tei?.msDesc;
    if (!tei) {
      el.innerHTML = '<p class="empty">No TEI catalog — see data/tei_manuscript.json</p>';
      return;
    }
    const id = tei.msIdentifier || {};
    const phys = tei.physDesc?.objectDesc?.supportDesc || {};
    const origin = tei.history?.origin || {};
    const items = (tei.msContents?.msItem || []).map((it) =>
      `<li><strong>${it.title}</strong> (${it.locus}) · ${it.class || ""}</li>`
    ).join("");
    const prov = (tei.history?.provenance || []).map((p) =>
      `<li>${p.date}: ${p.event}</li>`
    ).join("");
    const alt = (id.altIdentifier || []).map((a) =>
      a.url ? `<a href="${a.url}" target="_blank" rel="noopener">${a.value || a.type}</a>` : (a.value || a.note)
    ).join(" · ");
    el.innerHTML = `<dl class="tei-block">
      <dt>Identifier</dt>
      <dd><strong>${id.idno?.value || "GKS 2365 4to"}</strong> · ${id.repository || ""}, ${id.country || ""}<br>${alt}</dd>
      <dt>Contents</dt>
      <dd>${tei.msContents?.summary || ""}<ul>${items}</ul></dd>
      <dt>Physical</dt>
      <dd>${phys.material || "parchment"} · ${phys.extent || "144 sides"}</dd>
      <dt>Origin</dt>
      <dd>c. ${origin.origDate?.when || "1270"} · ${origin.origPlace || "Iceland"}</dd>
      <dt>Provenance</dt>
      <dd><ul>${prov}</ul></dd>
      <dt>Standards</dt>
      <dd><a href="${state.data.tei?.spec || "#"}" target="_blank" rel="noopener">TEI P5 msDesc</a> ·
          <a href="https://viscoll.org/collation/" target="_blank" rel="noopener">VisColl collation</a></dd>
    </dl>`;
  }

  function renderExpansionChart() {
    const chart = $("#expansion-chart");
    const phasesEl = $("#expansion-phases");
    if (!chart) return;
    const exp = state.data.expansion;
    if (!exp) {
      chart.innerHTML = '<p class="empty" style="padding:1rem">No expansion timeline data</p>';
      return;
    }
    const minYear = 1200;
    const maxYear = 2035;
    const span = maxYear - minYear;
    const pct = (y) => `${((y - minYear) / span) * 100}%`;
    let html = '<div class="expansion-axis"></div>';
    (exp.eras || []).forEach((era) => {
      const left = pct(era.start);
      const width = `${((era.end - era.start) / span) * 100}%`;
      html += `<div class="expansion-era" style="left:${left};width:${width};background:${era.color}22">${era.label}</div>`;
    });
    (exp.date_chart || []).forEach((ev, i) => {
      const bottom = 36 + (i % 3) * 22;
      html += `<div class="expansion-event" style="left:${pct(ev.year)};bottom:${bottom}px" title="${ev.year}">
        <strong>${ev.year}</strong><br>${ev.event}</div>`;
    });
    for (let y = 1250; y <= 2030; y += 50) {
      html += `<div class="expansion-tick" style="left:${pct(y)}">${y}</div>`;
    }
    chart.innerHTML = html;

    if (phasesEl) {
      const snap = state.data.completion?.summary || {};
      phasesEl.innerHTML = (exp.phases || []).map((ph) => {
        const ms = (ph.manuscripts || []).map((m) =>
          `<li>${m.siglum} (${m.date || ""})${m.pipeline_pct != null ? ` — ${m.pipeline_pct}%` : ""}</li>`
        ).join("");
        const cols = (ph.collections || []).map((c) =>
          `<li><a href="${c.url}" target="_blank" rel="noopener">${c.label || c.id}</a></li>`
        ).join("");
        const miles = (ph.milestones || []).map((m) => {
          let detail = m.detail || "";
          if (ph.id === "phase-1" && m.task?.includes("Grok clean")) {
            const g = snap["grok_clean_white.jpg"];
            if (g) detail = `${g.count}/144`;
          }
          if (ph.id === "phase-1" && m.task?.includes("doodle")) {
            const d = snap["grok_doodles.json"];
            if (d) detail = `${d.count}/144`;
          }
          return `<li><span class="phase-status">${m.status}</span> ${m.task}${detail ? ` (${detail})` : ""}</li>`;
        }).join("");
        return `<div class="phase-card ${ph.status || ""}">
          <strong>${ph.label}</strong> <span class="phase-status">${ph.status}</span>
          ${ph.start_year ? `<br><small>${ph.start_year}${ph.target_year ? ` → ${ph.target_year}` : ""}</small>` : ""}
          ${ms ? `<ul>${ms}</ul>` : ""}
          ${cols ? `<ul>${cols}</ul>` : ""}
          ${miles ? `<ul>${miles}</ul>` : ""}
        </div>`;
      }).join("");
    }
  }

  function renderCorpusRegistry() {
    const el = $("#corpus-registry");
    if (!el) return;
    const reg = state.data.corpus;
    if (!reg) {
      el.innerHTML = '<p class="empty">See data/corpus_registry.json</p>';
      return;
    }
    const pri = reg.primary || {};
    let html = `<p><strong>Active:</strong> ${pri.siglum} · <a href="${pri.url}" target="_blank" rel="noopener">handrit</a> · ${pri.date} · ${pri.pages} pages</p>`;
    html += "<table><tr><th>Priority</th><th>Target</th><th>Collection</th><th>Status</th></tr>";
    (reg.targets || []).forEach((t) => {
      const link = t.list_url || t.url || "#";
      const label = t.siglum || t.title || t.collection || t.institution || "—";
      html += `<tr><td>${t.priority}</td><td><a href="${link}" target="_blank" rel="noopener">${label}</a></td>
        <td>${t.collection || t.institution || "—"}</td><td>${t.status}</td></tr>`;
    });
    html += "</table>";
    const std = reg.standards || {};
    html += `<p style="font-size:0.78rem;margin-top:0.75rem">
      <a href="${std.tei_ms}" target="_blank" rel="noopener">TEI-MS</a> ·
      <a href="${std.viscoll}" target="_blank" rel="noopener">VisColl</a> ·
      <a href="${std.baekur}" target="_blank" rel="noopener">Bækur</a> ·
      <a href="${std.handrit_api}" target="_blank" rel="noopener">handrit.is</a>
    </p>`;
    el.innerHTML = html;
  }

  function renderCatalog() {
    if (!$("#tab-catalog")) return;
    renderCompletionSnapshot();
    renderFolioPlacement();
    renderTeiCatalog();
    renderExpansionChart();
    renderCorpusRegistry();
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
    renderRunic();
    renderFolioPlacement();

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

  const HASH_TO_TAB = {
    codicology: "tab-codicology",
    calligraphy: "tab-calligraphy",
    layers: "tab-layers",
    penmanship: "tab-penmanship",
    scribe: "tab-scribe",
    liturgy: "tab-liturgy",
    runic: "tab-runic",
    doodles: "tab-doodles",
    catalog: "tab-catalog",
  };

  const MUSIC_MODES = {
    gregorian: {
      label: "Gregorian Chant",
      note: "Latin ecclesiastical chant style — useful for comparing later Icelandic liturgical reception of Eddic metres.",
    },
    galder: {
      label: "Galder / Eddic Chant",
      note: "Norse galdralag and oral performance tradition — aligns with skaldic and eddic recitation patterns on this folio.",
    },
    historical: {
      label: "Historical Neumes",
      note: "13th-century Icelandic notation context — reconstructs how scribes may have heard metre while copying.",
    },
    modern: {
      label: "Modern Reconstruction",
      note: "Contemporary scholarly performance — pairs with the read-along tools and thematic cross-references below.",
    },
  };

  function activateTab(tabId) {
    const tab = document.querySelector(`.tab[data-tab="${tabId}"]`);
    const panel = $(`#${tabId}`);
    if (!tab || !panel) return;
    $all(".tab").forEach((t) => t.classList.remove("active"));
    $all(".tabpanel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    panel.classList.add("active");
  }

  function syncNavFromHash() {
    const hash = (location.hash || "").replace("#", "");
    $all(".site-nav a").forEach((a) => {
      const href = a.getAttribute("href") || "";
      a.classList.toggle("active", href === `#${hash}`);
    });
  }

  function handleHashNavigation(scroll) {
    const hash = (location.hash || "").replace("#", "");
    if (!hash) return;
    const tabId = HASH_TO_TAB[hash];
    if (!tabId) return;
    activateTab(tabId);
    syncNavFromHash();
    if (scroll) {
      const panel = $(`#${tabId}`);
      panel?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function setupTabs() {
    $all(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        activateTab(tab.dataset.tab);
        const hashKey = Object.entries(HASH_TO_TAB).find(([, id]) => id === tab.dataset.tab)?.[0];
        if (hashKey) {
          history.replaceState(null, "", `#${hashKey}`);
          syncNavFromHash();
        }
      });
    });
    window.addEventListener("hashchange", () => handleHashNavigation(true));
  }

  function setupMusicModes() {
    const note = $("#music-mode-note");
    const buttons = $("#music-mode-buttons");
    if (!buttons || !note) return;
    buttons.querySelectorAll("[data-mode]").forEach((btn) => {
      btn.addEventListener("click", () => {
        buttons.querySelectorAll("[data-mode]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const mode = MUSIC_MODES[btn.dataset.mode];
        note.textContent = mode ? `${mode.label}: ${mode.note}` : "";
        activateTab("tab-liturgy");
        history.replaceState(null, "", "#liturgy");
        syncNavFromHash();
      });
    });
  }

  async function init() {
    try {
      const [codicology, scribe, alphabet, liturgy, themes, highlights, hubIndex, runic,
        tei, viscoll, expansion, completion, corpus] = await Promise.all([
        loadJSON("data/codicology.json"),
        loadJSON("data/scribe_timeline.json"),
        loadJSON("data/alphabet_reference.json"),
        loadJSON("data/liturgy_comparisons.json"),
        loadJSON("data/thematic_crossrefs.json"),
        loadJSON("data/page_highlights.json").catch(() => null),
        loadJSON("data/hub_page_index.json").catch(() => null),
        loadJSON("data/runic_parallels.json").catch(() => null),
        loadJSON("data/tei_manuscript.json").catch(() => null),
        loadJSON("data/viscoll_collation.json").catch(() => null),
        loadJSON("data/expansion_timeline.json").catch(() => null),
        loadJSON("data/completion_snapshot.json").catch(() => null),
        loadJSON("data/corpus_registry.json").catch(() => null),
      ]);
      state.data = { codicology, scribe, alphabet, liturgy, themes, highlights, hubIndex, runic,
        tei, viscoll, expansion, completion, corpus };
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
    renderRunicOverview();
    renderRunicCorpusTable();
    renderCatalog();
    await updatePageView();
    setupTabs();
    setupMusicModes();
    handleHashNavigation(false);

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