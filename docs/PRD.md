# EnerViz Chile – Product Requirements Document (PRD)  
*(revision v0.2 • 2025-04-27)*

---

## 1  Background  
Chile’s Sistema Eléctrico Nacional (SEN) publishes grid prices (Costo Marginal), topology and plant locations, but they arrive in disparate CSVs, shapefiles and Excel workbooks.  The public therefore cannot visualise *where* and *why* the grid is stressed in real time.

---

## 2  Vision  
A browser-based **CesiumJS globe** that fuses geography, live marginal prices and basic resilience indicators:

| Layer | Visual encoding | Source |
|-------|-----------------|--------|
| Grid lines ≥ 66 kV | **Arrowed polylines** • width 8 px • coloured by voltage<br>66 kV yellow · 110 kV lime · 220 kV cyan · 500 kV red | IDE-Energía `Lineas_220.shp` |
| Power-flow direction | Static arrow-heads **from generation → load**<br>• Dedicated lines use IDE order<br>• Other lines: arrow points out of the endpoint that injects energy | Generation list from Coordinador Excel §11.1.2 |
| Price orbs | 32 × 32 SVG billboard, coloured on $/MWh ramp | “Costo Marginal Online” CSV |
| Rich tooltip | Name · Voltage kV · Circuit · Length km · Type · Owner · Status · Comuna | IDE shapefile attributes |

---

## 3  Goals & Non-Goals (MVP – 4 weeks of nights)

| Goal | Non-goal |
|------|----------|
| Visualise **last 24 h** marginal price at 8 key barras | ≥ 30-day archive or forecast |
| Show generation sites, sub-stations & lines ≥ 66 kV | Distribution grid (< 66 kV) |
| Generation → load arrows; voltage colour | Animated particles, live MW flow |
| Mobile-friendly, public read-only site (Vite + PNPM) | Auth, dashboards, BI queries |

---

## 4  User Personas (primary MVP focus ⭐)

| # | Persona | Pain point | EnerViz value |
|---|---------|-----------|---------------|
| ⭐1 | Energy reporter | Quickly illustrate where price spikes originate | One-click globe screenshot |
| ⭐2 | Engineering student | Understand how topology affects price | Interactive 3-D map + tooltips |
| ⭐3 | Curious citizen | Post-blackout anxiety; wants to “see” fragility | Arrows & colour reveal stress |

*(Full 8-persona table lives in `/docs/personas.md`)*

---

## 5  Technical Design

### 5.1  Data pipeline (“ETL”)

| Step | Tool | Frequency |
|------|------|-----------|
| `extract_generation_barras.py` → JSON list via Excel column L | **pandas + openpyxl** | Manual whenever Excel is updated |
| `annotate_lines.py` – merge all IDE line metadata (volt, owner, etc.) | **GeoPandas** | Manual |
| `tessellate_lines.py` – split each line into ≤ 256 pieces at 0.05°; keep volt & tooltip fields | **Shapely 2** | Manual |
| Hourly fetch *Costo Marginal Online* CSV → `prices_sample.json` | GitHub Actions (cron) | Hourly |

### 5.2  Front end (Vite + React 19 + Resium 1.19)

* Cesium 1.128 static assets copied in `postinstall`.
* Global arrow material (static) → zero per-frame callbacks.
* State managed via **Zustand** (future timeline slider).
* Images: Bing Aerial + labels; Cesium World Terrain.

---

## 6  Key Issues Encountered & Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| *Excel barra names contained “220 kV” suffix* | Generator matching failed → arrows pointed into plants | `normalise()` strips “### kV/kv” tokens |
| Tessellation exploded to 300 k segments | 44 MB GeoJSON & freeze | Hard-cap 256 segments per line via `TARGET_DEG 0.05` |
| Attributes lost after tessellation | Empty tooltips | Tessellator copies full attribute set into every segment |
| Direction incorrect on “DEDICADO” lines | Arrows reversed on single-plant feeders | If `tipo == dedicado` keep IDE order (gen → grid) |

---

## 7  Metrics of Success

| Metric (90 d) | Target |
|---------------|--------|
| Unique visitors | ≥ 1 500 / month |
| Average session | ≥ 3 min |
| CSV exports | ≥ 100 / month |
| Media citations | ≥ 5 |

---

## 8  Milestones (night-project cadence)

| Week | Deliverable |
|------|-------------|
| 0    | Repo + raw data verified (`v0.0.0`) |
| 1    | Generation alias list & voltage-coloured lines |
| 2    | Directional arrows + rich tooltip **(done)** |
| 3    | Hourly price auto-refresh + mobile tweaks |
| 4    | Public beta, Netlify URL |

---

## 9  Future Extensions

* **Reserve-margin indicator** (green / amber / red pill).  
* Historical animation slider.  
* Congestion overlay (flow > capacity).  
* EV-fast-charge price map (merge with EcoCarga API).

---

*Last edited: 27 Apr 2025 by Julian + o3.*
