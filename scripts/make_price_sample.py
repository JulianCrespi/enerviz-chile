#!/usr/bin/env python
"""
Builds a lightweight 24-hour price sample with coordinates so
the React/Cesium viewer can load data offline.

Inputs:
    data/raw/costo_marginal_<YYYYMM>.tsv   (JSON payload!)
    data/processed/barra_lookup.csv        barra , lat , lon
Output:
    public/prices_sample.json              [{barra, ts, price, lat, lon}, …]
"""
import json, pandas as pd, pathlib, unicodedata, sys

MONTH = pathlib.Path("data/raw/costo_marginal_202503.tsv")   # adjust if file name differs
LOOK  = pathlib.Path("data/processed/barra_lookup.csv")
OUT   = pathlib.Path("public/prices_sample.json")

def norm(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return txt.lower().strip()

# --- load lookup table -------------------------------------------------------
lookup = (pd.read_csv(LOOK)
            .assign(barra_norm=lambda d: d["barra"].apply(norm))
            .set_index("barra_norm"))

# --- load monthly JSON -------------------------------------------------------
with open(MONTH, "r", encoding="utf-8") as f:
    raw = pd.DataFrame(json.load(f))

if raw.empty:
    sys.exit(f"[ERROR] {MONTH} is empty or path is wrong")

# --- pick the first calendar day present ------------------------------------
first_day = raw["fecha"].iloc[0][:10]      # e.g. '2020-05-04'
mask = raw["fecha"].str.startswith(first_day)

sample = []
for _, row in raw[mask].iterrows():
    bnorm = norm(row["barra"])
    if bnorm not in lookup.index:
        continue                          # skip barras we can't locate
    lat, lon = lookup.loc[bnorm, ["lat", "lon"]]
    sample.append({
        "barra": row["barra"],
        "ts"   : f"{row['fecha']}-04:00", # Chile time-zone for display
        "price": float(row["cmg"]),
        "lat"  : float(lat),
        "lon"  : float(lon)
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(sample, f, indent=0)

print(f"✅ wrote {len(sample)} records ({first_day}) → {OUT}")
