#!/usr/bin/env python
"""
Tessellate each line into ≤256 pieces (0.05° ≈ 5–6 km) **and keep all
tooltip fields** so the viewer can colour by voltage and show rich info.

File size ≈ 25 MB (unzipped) – acceptable, and arrow spacing identical to the
version you liked.
"""
import geopandas as gpd, shapely.ops as ops, shapely.geometry as geom, pathlib

SRC = pathlib.Path("public/lines_barras.geojson")
DST = pathlib.Path("public/lines_barras_tess.geojson")

MAX_PIECES = 256
STEP_DEG   = 0.05        # split when >0.05°

tooltip_fields = [
    "startBarra", "endBarra", "volt",
    "owner", "circuit", "tipo",
    "estado", "comuna", "length_km", "nombre"
]

def split_line(line: geom.LineString):
    if line.length <= STEP_DEG:
        return [line]
    n = min(int(line.length / STEP_DEG) + 1, MAX_PIECES)
    return [ops.substring(line, i / n, (i + 1) / n, normalized=True) for i in range(n)]

print("↻ reading", SRC)
gdf_in = gpd.read_file(SRC)

rows = []
for _, row in gdf_in.iterrows():
    for part in split_line(row.geometry):
        rows.append({fld: row[fld] for fld in tooltip_fields} |
                    {"geometry": part})

gdf_out = gpd.GeoDataFrame(rows, crs="EPSG:4326")
DST.parent.mkdir(parents=True, exist_ok=True)
gdf_out.to_file(DST, driver="GeoJSON")

print(f"✅ tessellated → {DST}  segments: {len(gdf_out)}  "
      f"size: {DST.stat().st_size/1_048_576:.1f} MB")
