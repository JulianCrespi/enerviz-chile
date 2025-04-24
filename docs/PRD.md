# EnerViz Chile – Product Requirements Document (v0.3, 2025-04-23)

> Goal: a night-and-weekend hobby project that can reach a public beta in ≈ 4 weeks with heavy AI pair-programming (Cursor + Copilot + o3).

---

## 1. Background

The *Coordinador Eléctrico Nacional* publishes:

| Data | Format | Where | Notes |
|------|--------|-------|-------|
| **Costo Marginal Online** (hour-ahead prices per “barra”) | **JSON** array, **monthly** download (“Descargar Datos”) | Same page as the chart | File extension shows “TSV” but payload is valid JSON. |
| Hourly CSV exporter | `;`-separated CSV (last ~12 months only) | Export button on chart | Good for real-time (<24 h); schema stable. |
| 220 kV+ lines, plants, substations | Shapefile & WMS | IDE-Energía portal | Lines: 1 052 features; Substations: 1 177. |

Pain: analysts juggle QGIS, spreadsheets and CLI tools just to answer  
“Where is it expensive to inject/withdraw power *right now* and what’s around that node?”

---

## 2. Vision

*Browser-based CesiumJS globe (React + Resium) that fuses geography and price.*

* 3-D lines ≥ 220 kV, plants & substations.
* Price colour-coding at each barra (live & last 24 h).
* One-click data export, shareable permalink.

---

## 3. MVP Goals (4 sprints, nights/weekends)

| Goal | Non-Goal |
|------|----------|
| Render static grid lines + today’s prices (manual refresh). | Full history playback. |
| Use **pre-processed GeoJSON** & monthly JSON for first demo. | Live join in PostGIS. |
| Public read-only site, mobile OK. | Auth, user accounts, write APIs. |
| CSV/JSON download of current view. | Complete BI chart builder. |

---

## 4. Users & Use-Cases

1. **Energy reporters** – screenshot / embed 3-D view.  
2. **Students** – explore price propagation along the grid.  
3. **NGOs / community groups** – check if local plants drive local prices.  
4. **(Later) EV planners** – merge price with fast-charger map.

---

## 5. Data & ETL Requirements

### 5.1 Normalisation helper

* `barra_lookup.csv` (generated once) maps **8-10 key barras** → `lat, lon`
  * Derived via fuzzy match (`difflib`) between price JSON and *Subestaciones* `NOMBRE`.
  * Stored in `data/processed/`.

### 5.2 One-off converters

| Script | Purpose |
|--------|---------|
| `scripts/shp2geojson.ts` | Simplify *Lineas_220.shp* → `public/grid_lines.geojson` (TopoJSON later). |
| `scripts/barras_geojson.ts` | Merge `barra_lookup.csv` to tiny point GeoJSON. |

### 5.3 “Static-first” ETL loop (Phase 2)

npm run etl ├─ loads latest hourly CSV (if present) ├─ falls back to last-modified monthly JSON ├─ attaches coords via barra_lookup └─ writes public/prices/latest.json

### 5.4 Future upgrade (Phase 5)

* GitHub Action hourly cron  
* Neon Postgres + PostGIS extension  
* SQL view `vw_price_nodes` exposed via Vercel Edge Function.

---

## 6. Front-End Requirements

| Feature | Constraint |
|---------|------------|
| Cesium globe (Resium) | Loads in < 3 s on fibre in CL. |
| Timeline slider (last 24 h) | Zustand store. |
| Hover tooltip: barra, price, timestamp. | WCAG-AA colour palette. |
| Layer toggles (Plants / Subs / Lines). | Works in last 2 versions of Chrome, Edge, Safari, Firefox. |
| Download button → current JSON/CSV. | Static hosting (Vercel). |

---

## 7. Testing & QA

| Stage | Tool | Assertion |
|-------|------|-----------|
| Unit | Jest | `parsePriceJson()` returns array; `normName()` strips accents. |
| Integration | Playwright | Slider scrub → canvas pixel changes. |
| e2e (CI) | Cypress on Vercel preview | Homepage loads, console error-free. |
| Data ETL | GitHub Action | Fail job if new JSON < 50 kB or schema drift. |

---

## 8. Learning Resources

* CesiumJS Quick-start (15 min).  
* Resium “React + Cesium” talk (10 min).  
* Spatial SQL in 5 minutes (postgis.net).  

Links live in `docs/learning.md`.

---

## 9. Milestones & Timeline

| Week | Nights | Deliverable |
|------|--------|-------------|
| 0 | 2 | **Phase 0** complete – raw data downloaded, `barra_lookup.csv`, PRD committed. |
| 1 | 3-4 | **Scaffold** React + Cesium globe (no data). |
| 2 | 3-4 | Convert shapefile → GeoJSON; render static grid. |
| 3 | 2-3 | Hook `latest.json`; colour nodes; timeline slider. |
| 4 | 2 | Polish (tooltips, mobile tweaks); deploy public beta 🎉 |

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Coordinador JSON schema change | ETL fails | JSON-schema unit test in CI. |
| Substation names drift | Lookup mismatch | Fuzzy-match script reruns monthly. |
| Cesium free-tier tile quota | Imagery fails | Switch to open DEM + Bing Aerial. |
| Colour-blind users | Inaccessible heatmap | Dual palette + numeric labels. |

---

## 11. Open Questions

1. Keep lookup CSV or migrate to full point layer?  
2. Is English UI needed at launch?  
3. Licence choice: code MIT, data CC BY 4.0?  
4. PostGIS vs. Cloudflare D1 for Phase 5?

---

*End of PRD v0.3*