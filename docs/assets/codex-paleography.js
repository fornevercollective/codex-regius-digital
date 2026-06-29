(function () {
  const state = { page: 10, year: 1270, data: {} };

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

  function renderPageList() {
    const list = $("#page-list");
    list.innerHTML = "";
    for (let i = 1; i <= 144; i++) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "page-pill" + (i === state.page ? " active" : "");
      b.textContent = i;
      b.dataset.page = i;
      b.addEventListener("click", () => selectPage(i));
      list.appendChild(b);
    }
  }

  function selectPage(n) {
    state.page = n;
    $("#page-input").value = n;
    $all(".page-pill").forEach((el) => el.classList.toggle("active", +el.dataset.page === n));
    updatePageView();
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
      <div class="letter-cell" title="${(L.variants || []).join(', ')}">
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

  function renderLiturgy() {
    const lit = state.data.liturgy || {};
    const themes = (state.data.themes || {}).themes || [];
    const stanzas = (lit.key_stanzas || []).filter((s) => (s.pages_cr || []).includes(state.page));
    let html = "<h4>Witness manuscripts</h4><table><tr><th>Siglum</th><th>Name</th><th>Date</th></tr>";
    (lit.witnesses || []).forEach((w) => {
      html += `<tr><td>${w.siglum}</td><td>${w.name}</td><td>${w.date}</td></tr>`;
    });
    html += "</table>";
    if (stanzas.length) {
      html += "<h4>Stanzas on this page</h4>";
      stanzas.forEach((s) => {
        html += `<p><strong>${s.poem} st. ${s.stanza}</strong>: ${s.cr_text || "[pending]"}</p>`;
      });
    } else {
      html += "<p class='empty'>No stanza keyed to this page in liturgy_comparisons.json yet.</p>";
    }
    html += "<h4>Thematic parallels</h4><ul>";
    themes.forEach((t) => {
      html += `<li><strong>${t.label}</strong>: ${(t.pagan_concepts || []).slice(0, 2).join(", ")} ↔ ${(t.christian_parallels || []).slice(0, 1).join(", ")}</li>`;
    });
    html += "</ul>";
    $("#liturgy-body").innerHTML = html;
  }

  function updatePageView() {
    const dir = pageDir(state.page);
    $("#page-title").textContent = `Page ${state.page}`;
    $("#page-preview").src = `${dir}/grok_artistic_vellum.jpg`;
    $("#page-preview").onerror = function () {
      this.src = `${dir}/artistic_vellum.jpg`;
    };
    const links = [
      ["AI Assessment", `${dir}/ai_assessment.md`],
      ["Doodles", `${dir}/doodles_catalog.md`],
      ["Codicology", `${dir}/codicology.md`],
      ["Calligraphy", `${dir}/calligraphy_sheet.md`],
      ["Liturgy", `${dir}/liturgy_comparison.md`],
      ["Etymology", `${dir}/etymology.md`],
      ["JSON Report", `${dir}/scholarly_report.json`],
    ];
    $("#page-links").innerHTML = links.map(([l, h]) => `<a href="${h}" class="btn" style="margin-right:0.5rem">${l}</a>`).join("");
    renderLiturgy();
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
      const [codicology, scribe, alphabet, liturgy, themes] = await Promise.all([
        loadJSON("data/codicology.json"),
        loadJSON("data/scribe_timeline.json"),
        loadJSON("data/alphabet_reference.json"),
        loadJSON("data/liturgy_comparisons.json"),
        loadJSON("data/thematic_crossrefs.json"),
      ]);
      state.data = { codicology, scribe, alphabet, liturgy, themes };
    } catch (e) {
      console.warn("Data load:", e);
    }

    renderPageList();
    renderCodicology();
    renderAlphabet();
    renderTimeline();
    updatePageView();
    setupTabs();

    $("#page-input").addEventListener("change", (e) => selectPage(+e.target.value));
    $("#year-slider").addEventListener("input", (e) => {
      state.year = +e.target.value;
      $("#year-value").textContent = state.year;
      renderTimeline();
    });
    $("#export-font-btn").addEventListener("click", exportFont);
  }

  document.addEventListener("DOMContentLoaded", init);
})();