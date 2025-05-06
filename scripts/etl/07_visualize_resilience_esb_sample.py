#!/usr/bin/env python3
# scripts/etl/07_visualize_resilience_esb_sample.py

"""
Mini‐grafo de resiliencia SEN: Empresa → Subestación → Barra
(se salta temporalmente las Líneas para validar tablas y columnas).

Usage:
    pip install pandas pyvis openpyxl
    python scripts/etl/07_visualize_resilience_esb_sample.py \
      --xlsx data/raw/instalaciones_activos.xlsx \
      --out data/processed/resilience_esb_sample.html
"""

import argparse
import pandas as pd
from pathlib import Path
from pyvis.network import Network

def build_esb_sample(xlsx_path: str, output_html: str):
    # 1) Carga y dump de diagnóstico
    xls = pd.ExcelFile(xlsx_path)
    print(">> Available sheets:", xls.sheet_names)

    # 2) Detectar hojas
    sheet_emp = next(s for s in xls.sheet_names if 'empresa' in s.lower())
    sheet_sub = next(s for s in xls.sheet_names if 'subest' in s.lower())
    sheet_bar = next(s for s in xls.sheet_names if 'barra' in s.lower())

    print(f">> Using sheets -> Empresa: {sheet_emp}, Subestaciones: {sheet_sub}, Barras: {sheet_bar}")

    # 3) Leer DataFrames
    df_emp = pd.read_excel(xlsx_path, sheet_name=sheet_emp, dtype=str)
    df_sub = pd.read_excel(xlsx_path, sheet_name=sheet_sub, dtype=str)
    df_bar = pd.read_excel(xlsx_path, sheet_name=sheet_bar, dtype=str)

    # 4) Dump columnas
    print(">> Columns Empresa:", df_emp.columns.tolist())
    print(">> Columns Subestaciones:", df_sub.columns.tolist())
    print(">> Columns Barras:", df_bar.columns.tolist())

    # 5) Identificar columnas clave
    emp_id_col   = next(c for c in df_emp.columns if c.lower()=='id')
    emp_name_col = next((c for c in df_emp.columns if 'nombre' in c.lower() or 'name' in c.lower()), emp_id_col)

    sub_id_col   = next(c for c in df_sub.columns if c.lower()=='id')
    sub_name_col = next((c for c in df_sub.columns if 'nombre' in c.lower() or 'name' in c.lower()), sub_id_col)

    bar_id_col   = next(c for c in df_bar.columns if c.lower()=='id')
    bar_name_col = next((c for c in df_bar.columns if 'nombre' in c.lower() or 'name' in c.lower()), bar_id_col)
    bar_sub_col  = next(c for c in df_bar.columns if 'subest' in c.lower())

    print(f">> Mapped cols -> emp_id: {emp_id_col}, emp_name: {emp_name_col}")
    print(f">> sub_id: {sub_id_col}, sub_name: {sub_name_col}")
    print(f">> bar_id: {bar_id_col}, bar_name: {bar_name_col}, bar_sub: {bar_sub_col}")

    # 6) Top 10 subestaciones por # de barras
    top10_subs = (
        df_bar[bar_sub_col]
        .value_counts()
        .head(10)
        .index
        .tolist()
    )
    print(">> Top10 Subestaciones (IDs):", top10_subs)

    # 7) Filtrar
    df_emp  = df_emp[df_emp[emp_id_col].isin(df_sub[sub_id_col].unique())]
    df_sub  = df_sub[df_sub[sub_id_col].isin(top10_subs)]
    df_bar  = df_bar[df_bar[bar_sub_col].isin(top10_subs)]

    # 8) Construir mini‐grafo con PyVis
    net = Network(height='700px', width='100%', directed=True)
    net.barnes_hut(gravity=-20000, spring_length=200, spring_strength=0.001)
    net.toggle_physics(True)

    # Empresa → Subestación
    for _, r in df_emp.iterrows():
        eid, name = r[emp_id_col], r[emp_name_col]
        net.add_node(f"E_{eid}", label=name, title=f"Empresa: {name}",
                     color='red', size=30)
    for _, r in df_sub.iterrows():
        sid, name, owner = r[sub_id_col], r[sub_name_col], r.get('propietario_id') or r.get('propietario')
        net.add_node(f"S_{sid}", label=name, title=f"S/E: {name}",
                     color='blue', size=25)
        if pd.notna(owner):
            net.add_edge(f"E_{owner}", f"S_{sid}", title='owns', color='gray')

    # Subestación → Barra
    for _, r in df_bar.iterrows():
        bid, name, parent = r[bar_id_col], r[bar_name_col], r[bar_sub_col]
        net.add_node(f"B_{bid}", label=name, title=f"Barra: {name}",
                     color='green', size=15)
        net.add_edge(f"S_{parent}", f"B_{bid}", title='contains', color='darkgreen')

    # 9) Exportar HTML
    out = Path(output_html)
    net.show(str(out))
    print(f"✅ ESB mini‐grafo generado en {out}")

if __name__=='__main__':
    p = argparse.ArgumentParser(description="Mini ESB: Empresa→S/E→Barra (top10)")
    p.add_argument('--xlsx', required=True, help="instalaciones_activos.xlsx")
    p.add_argument('--out',  required=True, help="Salida HTML")
    args = p.parse_args()
    build_esb_sample(args.xlsx, args.out)
