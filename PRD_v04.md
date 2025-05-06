# EnerViz – Product Requirements Document (PRD)

## 0 · Purpose & Vision  
Deliver an interactive **electrical‑grid resilience explorer** for Chile’s Sistema Eléctrico Nacional (SEN).  
Stakeholders (Transelec, SEC, CNE, etc.) need to _see_ how a planned or unplanned outage at any asset (line, sub‑station, bar, generator) propagates through the network under **N‑1 / N‑2 scenarios**.  
ArcGIS Maps SDK for JavaScript will replace CesiumJS as the primary viewer due to richer GIS analysis, Utility Network tooling and smoother path to enterprise deployment.

---
## 1 · Scope (MVP)
| Layer | Source | Key tables / files | Notes |
|-------|--------|--------------------|-------|
| **Inventory** | `instalaciones_activos.xlsx` | `Empresa`, `Linea`, `Tramo`, `Subestaciones`, `Patios Subestaciones`, `Barras`, … | Canonical master; each sheet already carries stable primary keys. |
| **Geometries** | IDE‑Energía Shapefiles | `Lineas_66‑500kV.shp`, `Linea_de_Transmision.shp`, etc. | Used only for geometry; authoritative attributes come from Excel. |
| **(Future)** Generation plants | Same Excel sheets | `Centrales`, `Unidades Generadoras` | Phase 2. |

### 1.1 Data model (simplified)
```text
Empresa (id) ─owns──► Linea (id)
Linea ─feeds──► Subestacion (id)
Subestacion ─contains──► Barra (id)
Tramo (id) belongs_to Linea
Patio (id) logical parent of Barra
```
*Primary keys* are the `id` columns in every sheet.  All relations exist as `<entity>_id` foreign keys.

---
## 2 · Functional Requirements
1. **Topological Viewer**  
   * ArcGIS 3D Scene shows lines (voltage‑colored, arrowed by power‑flow), substations (colored by criticality) and generation plants.  
   * Hover reveals rich popup (attributes from Excel).
2. **Resilience Lens**  
   * Click asset → run **N‑1** (remove asset ➜ recompute connectivity graph).  
   * Visual diff (blinking red) for newly disconnected demand nodes.
3. **Outage Simulator**  
   * Select time‑window, pick asset list, simulate cascading failure with Utility Network Analysis.
4. **Reporting**  
   * Export CSV/GeoJSON for the selected scenario.  
   * Printable PDF one‑pager for regulators.

---
## 3 · Non‑Functional Requirements
| Category | Requirement |
|----------|-------------|
| Performance | < 3 s to load viewer (10 MB gzipped), < 1 s N‑1 graph recompute (in‑browser WebWorker). |
| Accuracy | Data parity with Coordinator’s “InfoTécnica” inventory (nightly ETL). |
| Security | Auth via ArcGIS OAuth; personal use licence in dev, Portal Enterprise for prod. |
| Extensibility | Plug‑in architecture for new layers (congestion, reserve‑margin, price heatmaps). |

---
## 4 · Architecture
```mermaid
graph TD
    subgraph Backend (Python)
      A1[ETL – DuckDB] -->|nightly| A2[Parquet tiles + JSON index]
    end
    subgraph Frontend (ArcGIS JS v4.x)
      B1[Vue + ArcGIS Maps SDK] --> B2[3D Scene]
      B1 --> B3[WebWorker – NetworkX light]
    end
    A2 -->|HTTP 🔗| B1
```
* DuckDB stores the normalized Excel + shapefile geometries.  
* Utility Network analyses run server‑side (Arcpy/ArcGIS Pro) and are cached; simple N‑1 connectivity runs client‑side with a slimmed NetworkX JSON.

---
## 5 · Milestones & Sprint Plan (6 weeks)
| Week | Deliverable |
|------|-------------|
| 0 | Repo bootstrap, ArcGIS Personal licence linked, Excel→DuckDB ETL green. |
| 1 | ArcGIS Scene – show lines & substations (static). |
| 2 | Build graph service (Empresa‑Linea‑Sub‑Barra).  API returns affected nodes for asset list. |
| 3 | N‑1 interactive removal + diff overlay. |
| 4 | Outage simulator UI stub; PDF/CSV export. |
| 5 | Polish, performance, pilot demo to Transelec / SEC. |

---
## 6 · KPIs
* **Time‑to‑Insight** < 5 min for an engineer to simulate a 500 kV line outage.  
* **Daily Active Users** ≥ 5 (pilot)  
* **Outage Scenario Exports** ≥ 30 / month  
* **Feedback Score** ≥ 4⁄5 from pilot engineers.

---
## 7 · Assumptions & Risks
* ArcGIS Personal licence is sufficient for dev; prod will require Enterprise Named Users.  
* IDE‑Energía shapefiles lag real‑world changes; Excel inventory is source‑of‑truth.  
* NetworkX‑in‑browser for >5 k nodes may hit performance; fallback is server‑side service.  
* Utility Network licensing may add cost; budget needed if we move beyond dev.

---
## 8 · Open Issues / Next Steps
1. Decide final cloud hosting (ArcGIS Online vs. Portal).  
2. Validate mapping of `patio_subestacion_id` ↔ `Subestaciones.id`.  
3. Align CSV price feed with ArcGIS time slider (future layer).  
4. Prototype N‑1 algorithm narrowing to **Empresa → Subestación** path to keep JSON payload small.

---
*Last updated: 2025‑05‑05*
