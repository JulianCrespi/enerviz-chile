#!/usr/bin/env python
import geopandas as gpd, pathlib
SRC = pathlib.Path("data/raw/Lineas_220/Lineas_220.shp")
DST = pathlib.Path("public/lines.geojson")
gdf = gpd.read_file(SRC)

# optional: keep only the columns you want
gdf = gdf[["ID_LIN_TRA", "NOMBRE", "CIRCUITO", "TENSION_KV", "geometry"]]

# simplify geometry to reduce file size (0.0001° ≈ 11 m)
gdf["geometry"] = gdf["geometry"].simplify(0.0001, preserve_topology=True)

DST.parent.mkdir(parents=True, exist_ok=True)
gdf.to_file(DST, driver="GeoJSON")
print("✅ wrote", DST, DST.stat().st_size/1024, "KB")
