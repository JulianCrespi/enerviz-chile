#!/usr/bin/env python
"""
Parse the NOMBRE field (format 'BARRA1 - BARRA2 ...') and save a new GeoJSON
with startBarra / endBarra string props.
"""
import geopandas as gpd, pathlib, re, unicodedata, json

RAW = pathlib.Path("data/raw/Lineas_220/Lineas_220.shp")
OUT = pathlib.Path("public/lines_barras.geojson")

def clean(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    return re.sub(r"\s+", " ", s.strip()).lower()

gdf = gpd.read_file(RAW)
bar1, bar2 = [], []

for name in gdf["NOMBRE"]:
    parts = re.split(r"-|/", name)[:2]            # 'A - B'  or 'A/B'
    a, b = (clean(parts[0]), clean(parts[1] if len(parts)>1 else parts[0]))
    bar1.append(a); bar2.append(b)

gdf["startBarra"] = bar1
gdf["endBarra"]   = bar2
gdf = gdf[["startBarra", "endBarra", "geometry"]]  # drop huge attrs

OUT.parent.mkdir(parents=True, exist_ok=True)
gdf.to_file(OUT, driver="GeoJSON")
print("✅ wrote", OUT, "with", len(gdf), "features")
