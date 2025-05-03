#!/usr/bin/env python3
"""
01_ingest_inventory.py
Carga:
  • instalaciones_activos.xlsx  (InfoTécnica)
  • uno o varios shapefiles IDE (66-500 kV)

Genera:
  data/curated/inventory.duckdb
  data/curated/subestacion.parquet
  data/curated/tramo_geom.parquet
"""
from __future__ import annotations
import argparse, pathlib
import duckdb, pandas as pd, pyogrio

# ───────────────────────── helpers ──────────────────────────
def ingest(xlsx_path: str, shp_paths: list[str]) -> None:
    curated = pathlib.Path("data/curated")
    curated.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(curated / "inventory.duckdb", read_only=False)

    # ---------- 1. hojas clave del Excel ----------
    sheet_map = {
        "linea":        "Linea",
        "circuito":     "Circuito",
        "tramo":        "Tramo",
        "subestacion":  "Subestaciones",
        "barra":        "Barras",
        "empresa":      "Empresa",
    }
    for tbl, sheet in sheet_map.items():
        print(f"→ hoja «{sheet}» → tabla {tbl}")
        df = pd.read_excel(xlsx_path, sheet_name=sheet)
        con.execute(f"CREATE OR REPLACE TABLE {tbl} AS SELECT * FROM df")

    # ---------- 2. geometría de líneas ----------
    con.execute(
        "CREATE OR REPLACE TABLE geom_tramo "
        "(tramo_ref_id BIGINT, kv DOUBLE, geom TEXT)"
    )

    for shp in shp_paths:
        print(f"→ leyendo shapefile {shp}")
        gdf = (
            pyogrio.read_dataframe(
                shp,
                columns=["ID_LIN_TRA", "TENSION_KV", "geometry"],
            )
            .rename(
                columns={
                    "ID_LIN_TRA": "tramo_ref_id",
                    "TENSION_KV": "kv",
                    "geometry": "geom",
                }
            )
            .astype({"tramo_ref_id": "int64", "kv": "float64"})
        )
        gdf["geom"] = gdf["geom"].apply(lambda g: g.wkt if g is not None else None)

        con.register("gdf", gdf)
        con.execute("INSERT INTO geom_tramo SELECT * FROM gdf")
        con.unregister("gdf")

    # ---------- 3. unir Tramo ←→ geometría ----------
    print("→ construyendo tabla tramo_geom")
    con.execute(
        """
        CREATE OR REPLACE TABLE tramo_geom AS
        SELECT t.*, g.geom, g.kv
        FROM tramo t
        LEFT JOIN geom_tramo g
        ON t.id = g.tramo_ref_id
        """
    )

    # ---------- 4. exportar Parquet para front-end ----------
    for tbl in ("subestacion", "tramo_geom"):
        out = curated / f"{tbl}.parquet"
        print(f"→ escribiendo {out}")
        con.execute(f"COPY {tbl} TO '{out}' (FORMAT 'parquet')")

    con.close()
    print("✔ ETL terminado")

# ────────────────────────── CLI ─────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True, help="ruta a instalaciones_activos.xlsx")
    ap.add_argument(
        "--shp",
        required=True,
        nargs="+",
        help="uno o varios shapefiles de líneas",
    )
    args = ap.parse_args()
    ingest(args.xlsx, args.shp)   # <<< ajuste clave

if __name__ == "__main__":
    main()
