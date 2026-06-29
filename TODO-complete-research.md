# Codex Regius Digital Edition · Research Completion Checklist

## Core Content (All 144 pages)
- [ ] Process remaining pages with full template (artistic, musical, paleography, etymology)
- [ ] QC pass on all pages (OCR, layout, translation accuracy)
- [x] Add rune stick / stone carving parallels for key stanzas — `data/runic_parallels.json` + hub **Runic & Stone** tab + book viewer panel

## Research Depth
- [ ] Vellum full codicology report
- [ ] Complete calligraphy alphabet + scribe biography timeline
- [ ] Script-to-Font generator prototype
- [x] Comparative liturgy table (variants across time + religious parallels) — `data/liturgy_comparisons.json`
- [x] Runic & archaeological parallels (Bergen sticks, Rök stone, Ramsund, galdr) — hub + book viewer
- [ ] Expand stanza-level runic collation for full Hávamál + Völuspá
- [ ] Medical music theory + galdr/seidr magical context notes

## Site Features
- [x] Consistent top navigation on every page
- [x] Music style switcher (Gregorian/Galdr/historical) in liturgy tab
- [x] Paleography hub with layer mixer, scribe timeline, runic parallels
- [x] Book viewer with real manuscript layers (pages 1–144)
- [ ] Search bar functional across the site
- [ ] Full index / poem list with links
- [ ] Showcase page polished

## Scholarly context (Codex Regius age)
- **Date:** c. 1270–1280 Iceland, one main scribe
- **Not the oldest Eddic artifact** — runic inscriptions and wooden sticks can be earlier
- **Primary complete witness** — most complete medieval Poetic Edda vellum; AM 748 I 4to and fragments supplement

## Commands
```bash
python3 tools/build_runic_parallels.py   # refresh page index from liturgy + parallels
python3 tools/build_liturgy_map.py --update-metadata
python3 tools/build_hub_index.py
```

## Polish & Release
- [x] GitHub Pages deploy (trimmed artifact, chunked exports via LFS)
- [ ] Final deployment test
- [ ] About / Use Cases page
- [ ] Launch post / announcement
- [ ] License + proper citation for Árni Magnússon Institute

## Bonus (Future)
- Interactive map of manuscript history
- Per-stanza runic image overlays
- User annotation system
- API for other researchers

Mark items `[x]` when finished.