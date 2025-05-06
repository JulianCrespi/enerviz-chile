#!/usr/bin/env python3
# scripts/etl/03_review_shapefile.py

"""
Compara el shapefile de IDE Energía con el inventario maestro de líneas
(obtenido de la hoja "Linea" de instalaciones_activos.xlsx).
Acepta ruta a un archivo .shp o a un directorio que contenga un shapefile.
"""
import argparse
import sys
from pathlib import Path
import pandas as pd
import geopandas as gpd


def find_shapefile(path: Path) -> Path:
    """Retorna el primer archivo .shp válido en un directorio o el mismo si es un archivo shapefile."""
    if path.is_file() and path.suffix.lower() == '.shp':
        return path
    if path.is_dir():
        candidates = [f for f in path.iterdir() if f.suffix.lower() == '.shp' and not f.name.lower().endswith('.shp.xml')]
        if not candidates:
            raise FileNotFoundError(f"No se encontró ningún .shp válido en {path}")
        return candidates[0]
    raise FileNotFoundError(f"Ruta inválida para shapefile: {path}")


def review(xlsx_path: str, shp_input: str) -> None:
    # 1) Cargar hoja 'Linea' del Excel maestro
    try:
        df = pd.read_excel(
            xlsx_path,
            sheet_name='Linea',
            dtype={'id': str},
        )
    except Exception as e:
        print(f"ERROR al leer hoja 'Linea': {e}", file=sys.stderr)
        sys.exit(1)
    # Renombrar columnas de interés
    df = df.rename(columns={'id': 'ID_LIN_TRA', 'name': 'NOMBRE'})
    # Ajustar nombre de columna para tensión si existe
    if 'voltaje_kV' in df.columns:
        df = df.rename(columns={'voltaje_kV': 'TENSION_KV'})
    master_ids = set(df['ID_LIN_TRA'].astype(str))
    print(f"Maestro Excel: {len(master_ids)} líneas únicas detectadas.")

    # 2) Encontrar y cargar shapefile
    shp_path = Path(shp_input)
    try:
        shp_file = find_shapefile(shp_path)
        print(f"Usando shapefile: {shp_file}")
    except FileNotFoundError as e:
        print(f"ERROR shapefile: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        gdf = gpd.read_file(shp_file)
    except Exception as e:
        print(f"ERROR al leer {shp_file}: {e}", file=sys.stderr)
        sys.exit(1)

    # 3) Detectar campo ID de línea en shapefile
    cols = list(gdf.columns)
    id_fields = [c for c in cols if 'id_lin' in c.lower()]
    if not id_fields:
        print(f"ERROR: No se encontró columna de ID línea en {shp_file}. Columnas: {cols}", file=sys.stderr)
        sys.exit(1)
    field = id_fields[0]
    gdf['ID_LIN_TRA'] = gdf[field].astype(str)
    print(f"Campo de ID usado en shapefile: '{field}'")
    shp_ids = set(gdf['ID_LIN_TRA'])
    print(f"Shapefile: {len(shp_ids)} líneas detectadas en geometría.")

    # 4) Comparar conjuntos de IDs
    only_master = sorted(master_ids - shp_ids)
    only_shp = sorted(shp_ids - master_ids)
    print(f"En Excel pero no en shapefile: {len(only_master)} IDs")
    if only_master:
        print("  Ejemplos:", only_master[:10], '...')
    print(f"En shapefile pero no en Excel: {len(only_shp)} IDs")
    if only_shp:
        print("  Ejemplos:", only_shp[:10], '...')

    # 5) Mostrar ejemplos detallados
    if only_master:
        print("\nEjemplos de líneas faltantes en shapefile:")
        sample = df[df['ID_LIN_TRA'].isin(only_master[:5])]
        cols_master = ['ID_LIN_TRA', 'NOMBRE']
        if 'TENSION_KV' in sample.columns:
            cols_master.append('TENSION_KV')
        print(sample[cols_master].to_string(index=False))
    if only_shp:
        print("\nEjemplos de geometrías en shapefile sin registro en Excel:")
        cols_shp = ['ID_LIN_TRA', field]
        if 'TENSION_KV' in gdf.columns:
            cols_shp.append('TENSION_KV')
        print(gdf[gdf['ID_LIN_TRA'].isin(only_shp[:5])][cols_shp].to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Comparar shapefile IDE vs inventario maestro de líneas")
    parser.add_argument('--xlsx', required=True, help="Archivo instalaciones_activos.xlsx")
    parser.add_argument('--shp', required=True, help="Archivo .shp o directorio con shapefile IDE")
    args = parser.parse_args()
    review(args.xlsx, args.shp)
