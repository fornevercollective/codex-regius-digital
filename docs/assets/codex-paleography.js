(function () {
  const LAYERS = [
    { id: "raw", label: "Raw scan", file: "raw.png", defaultOn: false, opacity: 0.35 },
    { id: "artistic", label: "Artistic vellum", file: "artistic_vellum.jpg", defaultOn: true, opacity: 0.5 },
    { id: "clean", label: "Clean white", file: "clean_white.jpg", defaultOn: true, opacity: 0.65 },
    { id: "grok_artistic", label: "Grok vellum", file: "grok_artistic_vellum.jpg", defaultOn: true, opacity: 0.85 },
    { id: "grok_clean", label: "Grok clean", file: "grok_clean_white.jpg", defaultOn: true, opacity: 1 },
  ];

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
    layerState: {},
    pageHighlights: null,
    glyphIndex: null,
    penmanship: null,
    animTimer: null,
    eventFilter: "",
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

  function pagesForFilter() {
    const idx = state.data.highlights;
    if (!state.eventFilter || !idx) return null;
    const cat = state.eventFilter;
    return new Set(idx.by_category?.[cat] || []);
  }

  function renderPageList() {
    const list = $("#page-list");
    const filterSet = pagesForFilter();
    const eventPages = new Set((state.data.highlights?.pages || []).map((p) => p.page));
    list.innerHTML = "";
    let shown = 0;
    for (let i = 1; i <= 144; i++) {
      if (filterSet && !filterSet.has(i)) continue;
      shown++;
      const b = document.createElement("button");
      b.type = "button";
      b.className = "page-pill" + (i === state.page ? " active" : "") + (eventPages.has(i) ? " has-events" : "");
      b.textContent = i;
      b.dataset.page = i;
      b.title = eventPages.has(i) ? "Has indexed events" : "";
      b.addEventListener("click", () => selectPage(i));
      list.appendChild(b);
    }
    $("#page-filter-label").textContent = filterSet ? `(${shown} with ${state.eventFilter})` : "(1–144)";
  }

  function selectPage(n) {
    state.page = n;
    $("#page-input").value = n;
    $all(".page-pill").forEach((el) => el.classList.toggle("active", +el.dataset.page === n));
    updatePageView();
  }

  function initLayerState() {
    LAYERS.forEach((L) => {
      if (state.layerState[L.id] === undefined) {
        state.layerState[L.id] = { on: L.defaultOn, opacity: L.opacity };
      }
    });
  }

  function renderLayerControls() {
    initLayerState();
    const el = $("#layer-controls");
    el.innerHTML = LAYERS.map((L) => {
      const s = state.layerState[L.id];
      return `<label class="layer-control">
        <input type="checkbox" data-layer="${L.id}" ${s.on ? "checked" : ""} />
        ${L.label}
        <input type="range" min="0" max="100" value="${Math.round(s.opacity * 100)}" data-opacity="${L.id}" />
      </label>`;
    }).join("");

    el.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.addEventListener("change", () => {
        state.layerState[cb.dataset.layer].on = cb.checked;
        applyLayerVisibility();
      });
    });
    el.querySelectorAll('input[type="range"]').forEach((rng) => {
      rng.addEventListener("input", () => {
        state.layerState[rng.dataset.opacity].opacity = rng.value / 100;
        applyLayerVisibility();
      });
    });
  }

  function applyLayerVisibility() {
    $all(".layer-img").forEach((img) => {
      const id = img.dataset.layer;
      const s = state.layerState[id];
      img.style.opacity = s?.on ? (s.opacity ?? 1) : 0;
      img.style.display = s?.on ? "block" : "none";
    });
    drawHighlights();
  }

  async function buildLayerStack() {
    const dir = pageDir(state.page);
    const stack = $("#layer-stack");
    stack.innerHTML = "";
    const loadPromises = LAYERS.map((L) => {
      return new Promise((resolve) => {
        const img = document.createElement("img");
        img.className = "layer-img";
        img.dataset.layer = L.id;
        img.alt = L.label;
        img.onload = () => resolve(true);
        img.onerror = () => resolve(false);
        img.src = `${dir}/${L.file}`;
        stack.appendChild(img);
      });
    });
    await Promise.all(loadPromises);
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
    if (!$("#show-highlights").checked || !state.pageHighlights?.events?.length) return;

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

  async function loadPageData() {
    const dir = pageDir(state.page);
    state.pageHighlights = null;
    state.glyphIndex = null;
    state.penmanship = null;
    try {
      state.pageHighlights = await loadJSON(`${dir}/page_highlights.json`);
    } catch (_) { /* optional */ }
    try {
      state.glyphIndex = await loadJSON(`${dir}/glyph_index.json`);
    } catch (_) { /* optional */ }
    try {
      state.penmanship = await loadJSON(`${dir}/penmanship_report.json`);
    } catch (_) { /* optional */ }
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
      html += `<li><span class="event-chip">${cat}</span> ${pages.length} pages: ${pages.slice(0, 12).join(", ")}${pages.length > 12 ? "…" : ""}</li>`;
    });
    html += "</ul>";
    el.innerHTML = html;
  }

  function renderTimeline() {
    const scribe = state.data.scribe || {};
    const items = (scribe.timeline || []).filter((t) => {
      const y = t.year;
      return state.year >= y - 30 && state.year <= y + 30;
    });
    const el = $("#scribe-timeline");
    if (!items.length) {
      el.innerHTML = "<p class='empty'>Adjust year slider to explore scribe context.</p>";
      return;
    }
    el.innerHTML = items.map((t) => `
      <div class="timeline-item">
        <div class="timeline-year">${t.era || ""} ${t.year}</div>
        <div>${t.event}</div>
        <small>${t.type || ""}</small>
      </div>`).join("");
  }

  function renderAlphabet() {
    const letters = (state.data.alphabet || {}).letters || [];
    const el = $("#alphabet-grid");
    el.innerHTML = letters.map((L) => `
      <div class="letter-cell" title="${(L.variants || []).join(", ")}">
        ${L.char}<small>${L.name}</small>
      </div>`).join("");
  }

  function renderCodicology() {
    const v = (state.data.codicology || {}).vellum || {};
    $("#codicology-body").innerHTML = `
      <div class="card-grid">
        <div class="card"><h4>Animal</h4><p>${v.animal || "—"}<br><small>${v.animal_note || ""}</small></p></div>
        <div class="card"><h4>Region</h4><p>${v.region_origin || "—"}</p></div>
        <div class="card"><h4>Age</h4><p>${v.age_estimate || "—"}</p></div>
        <div class="card"><h4>Preparation</h4><p>${(v.preparation || {}).fiber_pattern || "—"}</p></div>
      </div>`;
  }

  function pagePoemEntry(page) {
    const index = state.data.liturgy?.page_index || [];
    return index.find((e) => e.page === page) || null;
  }

  function renderLiturgy() {
    const lit = state.data.liturgy || {};
    const themes = (state.data.themes || {}).themes || [];
    const poem = pagePoemEntry(state.page);
    const stanzas = (lit.key_stanzas || []).filter((s) => (s.pages_cr || []).includes(state.page));
    let html = "<h4>Witness manuscripts</h4><table><tr><th>Siglum</th><th>Name</th><th>Date</th></tr>";
    (lit.witnesses || []).forEach((w) => {
      html += `<tr><td>${w.siglum}</td><td>${w.name}</td><td>${w.date}</td></tr>`;
    });
    html += "</table>";
    if (poem && poem.poem) {
      const flags = [];
      if (poem.lacuna_before) flags.push("lacuna before");
      if (poem.lacuna_after) flags.push("lacuna after");
      if (poem.extended_scan) flags.push(`extended → CR p.${poem.maps_to_cr_page || "?"}`);
      html += `<h4>Poem on this page</h4>
        <p><strong>${poem.poem}</strong><br>
        <small>${poem.section || ""} · ${poem.type || ""}${flags.length ? " · " + flags.join("; ") : ""}</small></p>`;
    }
    if (stanzas.length) {
      html += "<h4>Keyed stanzas (collation)</h4>";
      stanzas.forEach((s) => {
        html += `<p><strong>${s.poem} st. ${s.stanza}</strong>: ${s.cr_text || "[pending]"}</p>`;
      });
    }
    html += "<h4>Thematic parallels</h4><ul>";
    themes.forEach((t) => {
      html += `<li><strong>${t.label}</strong>: ${(t.pagan_concepts || []).slice(0, 2).join(", ")} ↔ ${(t.christian_parallels || []).slice(0, 1).join(", ")}</li>`;
    });
    html += "</ul>";
    $("#liturgy-body").innerHTML = html;
  }

  async function updatePageView() {
    const dir = pageDir(state.page);
    $("#page-title").textContent = `Page ${state.page}`;
    await loadPageData();
    await buildLayerStack();
    renderLayerControls();
    renderGlyphs();
    renderPenmanship();
    renderPageEvents();
    renderLiturgy();

    const links = [
      ["AI Assessment", `${dir}/ai_assessment.md`],
      ["Doodles", `${dir}/doodles_catalog.md`],
      ["Glyph index", `${dir}/glyph_index.json`],
      ["Penmanship", `${dir}/penmanship_report.json`],
      ["Highlights", `${dir}/page_highlights.json`],
      ["Codicology", `${dir}/codicology.md`],
      ["Liturgy", `${dir}/liturgy_comparison.md`],
      ["JSON Report", `${dir}/scholarly_report.json`],
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

  function exportFont() {
    const a = document.createElement("a");
    a.href = "data/codex_regius_font.json";
    a.download = "codex_regius_font.json";
    a.click();
  }

  async function init() {
    try {
      const [codicology, scribe, alphabet, liturgy, themes, highlights] = await Promise.all([
        loadJSON("data/codicology.json"),
        loadJSON("data/scribe_timeline.json"),
        loadJSON("data/alphabet_reference.json"),
        loadJSON("data/liturgy_comparisons.json"),
        loadJSON("data/thematic_crossrefs.json"),
        loadJSON("data/page_highlights.json").catch(() => null),
      ]);
      state.data = { codicology, scribe, alphabet, liturgy, themes, highlights };
    } catch (e) {
      console.warn("Data load:", e);
    }

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
    $("#export-font-btn").addEventListener("click", exportFont);
    $("#show-highlights").addEventListener("change", drawHighlights);
    $("#play-animation-btn").addEventListener("click", playAnimation);
    window.addEventListener("resize", resizeHighlightCanvas);
  }

  document.addEventListener("DOMContentLoaded", init);
})();