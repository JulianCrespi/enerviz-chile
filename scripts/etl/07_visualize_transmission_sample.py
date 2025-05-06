#!/usr/bin/env python3
# scripts/etl/07_visualize_transmission_sample.py

"""
Mini‐grafo de la topología física SEN: Línea → Subestación → Barra
(usa sólo las 10 subestaciones más “alimentadas”).

Este script incluye logs de diagnóstico para validar
nombres de hojas y columnas antes de filtrar.

Usage:
    pip install pandas pyvis openpyxl
    python scripts/etl/07_visualize_transmission_sample.py \
        --xlsx data/raw/instalaciones_activos.xlsx \
        --out data/processed/resilience_graph_sample.html
"""

import argparse
import pandas as pd
from pathlib import Path
from pyvis.network import Network

def build_transmission_sample(xlsx_path: str, output_html: str):
    # 1) Cargar Excel y listar hojas
    xls = pd.ExcelFile(xlsx_path)
    print(">> Available sheets:", xls.sheet_names)

    # 2) Detectar nombres de hoja relevantes
    sheet_lin = next(s for s in xls.sheet_names if 'line' in s.lower() or 'tram' in s.lower())
    sheet_sub = next(s for s in xls.sheet_names if 'subest' in s.lower())
    sheet_bar = next(s for s in xls.sheet_names if 'barra' in s.lower() or 'patio' in s.lower())

    print(f">> Using sheets -> Lines: {sheet_lin}, Subestaciones: {sheet_sub}, Barras: {sheet_bar}")

    # 3) Leer las hojas
    df_lin = pd.read_excel(xlsx_path, sheet_name=sheet_lin, dtype=str)
    df_sub = pd.read_excel(xlsx_path, sheet_name=sheet_sub, dtype=str)
    df_bar = pd.read_excel(xlsx_path, sheet_name=sheet_bar, dtype=str)

    # 4) Log columnas disponibles
    print(">> Columns in Lines sheet:", df_lin.columns.tolist())
    print(">> Columns in Subestaciones sheet:", df_sub.columns.tolist())
    print(">> Columns in Barras sheet:", df_bar.columns.tolist())

    # 5) Determinar campos clave (ajusta si difieren)
    # Línea: columna ID, columnas Subestación origen/destino
    lin_id_col    = next(c for c in df_lin.columns if c.lower() in ('id','line_id','linea_id'))
    sub_or_col    = next(c for c in df_lin.columns if 'origen' in c.lower() and 'subest' in c.lower())
    sub_dst_col   = next(c for c in df_lin.columns if 'destino' in c.lower() and 'subest' in c.lower())

    # Subestación: columna ID
    sub_id_col    = next(c for c in df_sub.columns if c.lower() in ('id','subestacion_id'))

    # Barra: columna ID y columna subestacion parent
    bar_id_col    = next(c for c in df_bar.columns if c.lower() in ('id','barra_id'))
    bar_sub_col   = next(c for c in df_bar.columns if 'subest' in c.lower())

    print(f">> Detected columns -> lin_id: {lin_id_col}, sub_or: {sub_or_col}, sub_dst: {sub_dst_col}")
    print(f">> sub_id: {sub_id_col}; bar_id: {bar_id_col}, bar_sub: {bar_sub_col}")

    # 6) Top 10 subestaciones más “alimentadas”
    all_subs = pd.concat([
        df_lin[sub_or_col],
        df_lin[sub_dst_col]
    ]).value_counts()
    top10 = all_subs.head(10).index.tolist()
    print(">> Top10 Subestaciones IDs:", top10)

    # 7) Filtrar DataFrames
    df_sub = df_sub[df_sub[sub_id_col].isin(top10)]
    df_lin = df_lin[
        df_lin[sub_or_col].isin(top10) |
        df_lin[sub_dst_col].isin(top10)
    ]
    df_bar = df_bar[df_bar[bar_sub_col].isin(top10)]

    # 8) Montar PyVis
    net = Network(height='700px', width='100%', directed=True)
    net.barnes_hut(gravity=-20000, spring_length=200, spring_strength=0.001)
    net.toggle_physics(True)

    # 9) Añadir nodos y aristas
    # Líneas → Subestaciones
    for _, r in df_lin.iterrows():
        lid = r[lin_id_col]
        name = r.get('nombre', lid)
        net.add_node(f"L_{lid}", label=name, color='orange', size=20)
        # origen
        o = r[sub_or_col]
        if pd.notna(o):
            net.add_node(f"S_{o}", label=o, color='blue', size=25)
            net.add_edge(f"L_{lid}", f"S_{o}", title='feeds', color='darkblue')
        # destino
        d = r[sub_dst_col]
        if pd.notna(d):
            net.add_node(f"S_{d}", label=d, color='blue', size=25)
            net.add_edge(f"L_{lid}", f"S_{d}", title='feeds', color='darkblue')

    # Subestaciones → Barras
    for _, r in df_bar.iterrows():
        bid = r[bar_id_col]
        bar_name = r.get('nombre', bid)
        sid = r[bar_sub_col]
        net.add_node(f"B_{bid}", label=bar_name, color='green', size=15)
        net.add_edge(f"S_{sid}", f"B_{bid}", title='contains', color='darkgreen')

    # 10) Guardar HTML
    out = Path(output_html)
    net.show(str(out))
    print(f"✅ Sample transmission graph generated: {out}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mini‐grafo L→S→B (top10 subs)")
    parser.add_argument('--xlsx', required=True, help="instalaciones_activos.xlsx")
    parser.add_argument('--out',  required=True, help="Salida .html")
    args = parser.parse_args()
    build_transmission_sample(args.xlsx, args.out)
