# EnerViz Chile 🌐⚡️

A 3-D CesiumJS globe showing Chile’s transmission grid colour-coded by voltage,
with static arrows that flow **from generation sites toward consumption**, plus
live marginal-price orbs.

---

## Quick-start (clean Mac + VS Code)

```bash
# 0. clone
git clone https://github.com/<your-fork>/enerviz-chile.git
cd enerviz-chile

# 1. Python data prep  (one time or when raw data changes)
python3 -m venv .venv
source .venv/bin/activate
pip install geopandas shapely pandas openpyxl pyogrio

python scripts/extract_generation_barras.py   # from Coordinador Excel
python scripts/annotate_lines.py              # enrich line metadata
python scripts/tessellate_lines.py            # ≤256 pieces @ 0.05°

# 2. Front-end
pnpm install          # installs Cesium/React/Resium
pnpm run postinstall  # copies Cesium static assets
pnpm dev              # launches Vite → http://localhost:5173
