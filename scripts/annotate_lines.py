#!/usr/bin/env python
"""
Create lines_barras.geojson with rich, ASCII-safe attributes.

Columns kept (all renamed to ASCII): startBarra, endBarra, volt, owner,
circuit, tipo, estado, comuna, nombre, length_km.
"""
import geopandas as gpd, unicodedata, re, pathlib

RAW = pathlib.Path("data/raw/Lineas_220/Lineas_220.shp")
OUT = pathlib.Path("public/lines_barras.geojson")

def ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()

def clean_name(txt: str) -> str:
    return re.sub(r"\s+", " ", ascii(txt).lower()).strip()

# ------------------------------------------------------------------ #
gdf = gpd.read_file(RAW)

# split NOMBRE into start / end barras
starts, ends = [], []
for name in gdf["NOMBRE"]:
    parts = re.split(r"-|/", name, maxsplit=1)
    a = parts[0]; b = parts[1] if len(parts) > 1 else parts[0]
    starts.append(clean_name(a))
    ends.append(clean_name(b))

gdf = gdf.assign(
    startBarra = starts,
    endBarra   = ends,
    volt       = gdf["TENSION_KV"].fillna(0).astype(int),
    owner      = gdf["PROPIEDAD"].fillna("—").apply(ascii),
    circuit    = gdf["CIRCUITO"].fillna("—").apply(ascii),
    tipo       = gdf["TIPO"].fillna("—").apply(ascii),
    estado     = gdf["ESTADO"].fillna("—").apply(ascii),
    comuna     = gdf["COMUNA"].fillna("—").apply(ascii),
    nombre     = gdf["NOMBRE"].apply(ascii),
)

# precise length in km (World Mercator metres)
gdf_proj = gdf.to_crs(3395)
gdf["length_km"] = gdf_proj.length / 1_000

cols = ["startBarra","endBarra","volt","owner","circuit",
        "tipo","estado","comuna","length_km","nombre","geometry"]
gdf[cols].to_file(OUT, driver="GeoJSON")
print("✅ wrote", OUT, "features:", len(gdf))
