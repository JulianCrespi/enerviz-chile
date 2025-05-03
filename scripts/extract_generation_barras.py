#!/usr/bin/env python
"""
Create generation_barras.json from Coordinador Excel (sheet 'Centrales')
Column:
  11.1.2 Puntos de conexión al SI a través de los cuales inyecta energía.
Auto-finds the Excel file under data/raw/**.
"""
import pandas as pd, unicodedata, re, pathlib, json, sys, glob

RAW_DIR = pathlib.Path("data/raw")
OUT     = pathlib.Path("public/generation_barras.json")
SHEET   = "Centrales"
COL     = "11.1.2 Puntos de conexión al SI a través de los cuales inyecta energía."

def clean(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii","ignore").decode()
    t = re.sub(r"\b\d+\s*k?v\b", "", t, flags=re.I)  # strip '220 kV'
    return re.sub(r"\s+", " ", t.lower()).strip()

# locate Excel containing the sheet
xlsx = None
for p in RAW_DIR.rglob("*.xlsx"):
    try:
        if SHEET in pd.ExcelFile(p).sheet_names:
            xlsx = p; break
    except Exception:
        pass
if not xlsx:
    sys.exit(f"❌ Excel with sheet '{SHEET}' not found under {RAW_DIR}")

print(f"ℹ️  using {xlsx.relative_to(RAW_DIR)}")
df = pd.read_excel(xlsx, sheet_name=SHEET, header=6, engine="openpyxl")
if COL not in df.columns:
    sys.exit(f"❌ Column not found: {COL}")

barras = {clean(b) for raw in df[COL].dropna()
          for b in re.split(r"[;,/]| y | Y |-|\n", str(raw)) if b.strip()}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(sorted(barras), indent=0))
print(f"✅ wrote {len(barras)} barras → {OUT}")
