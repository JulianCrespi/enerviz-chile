#!/usr/bin/env python3
# scripts/etl/05_export_graphml.py

"""
Construye y exporta el Knowledge Graph del SEN directamente a GraphML limpio.

Uso:
  python scripts/etl/05_export_graphml.py \
    --xlsx data/raw/instalaciones_activos.xlsx \
    --out data/processed/kg_sen.graphml

Esto evita dependencias de JSON intermedio y limpia valores None antes de exportar.
"""
import argparse
import sys
import pandas as pd
import networkx as nx
from pathlib import Path


def build_and_export(xlsx_path: str, out_path: str) -> None:
    # Crear grafo dirigido
    G = nx.DiGraph()

    # 1) Empresas
    df_emp = pd.read_excel(xlsx_path, sheet_name='Empresa', dtype={'id': str})
    for _, r in df_emp.iterrows():
        G.add_node(f"E_{r['id']}", type='Empresa', name=r.get('name',''))

    # 2) Subestaciones
    df_sub = pd.read_excel(xlsx_path, sheet_name='Subestaciones', dtype={'id': str, 'propietario_id': str})
    for _, r in df_sub.iterrows():
        sub = f"S_{r['id']}"
        G.add_node(sub, type='Subestacion', name=r.get('name',''), lat=r.get('lat',None), lon=r.get('lon',None))
        prop = f"E_{r['propietario_id']}"
        if G.has_node(prop):
            G.add_edge(prop, sub, relation='owns')

    # 3) Barras
    df_bar = pd.read_excel(xlsx_path, sheet_name='Barras', dtype={'id': str, 'patio_subestacion_id': str})
    for _, r in df_bar.iterrows():
        bar = f"B_{r['id']}"
        G.add_node(bar, type='Barra', tension_kV=r.get('tension_kV',None), name=r.get('name',''))
        parent = f"S_{r['patio_subestacion_id']}"
        if G.has_node(parent):
            G.add_edge(bar, parent, relation='part_of')

    # 4) Lineas
    df_lin = pd.read_excel(xlsx_path, sheet_name='Linea', dtype={'id': str, 'propietario_id': str})
    for _, r in df_lin.iterrows():
        lin = f"L_{r['id']}"
        G.add_node(lin, type='Linea', name=r.get('name',''), tension_kV=r.get('voltaje_kV',None))
        owner = f"E_{r['propietario_id']}"
        if G.has_node(owner):
            G.add_edge(owner, lin, relation='owns')

    # 5) Circuitos
    df_cir = pd.read_excel(xlsx_path, sheet_name='Circuito', dtype={'id': str, 'linea_id': str})
    for _, r in df_cir.iterrows():
        cir = f"C_{r['id']}"
        G.add_node(cir, type='Circuito')
        parent = f"L_{r['linea_id']}"
        if G.has_node(parent):
            G.add_edge(parent, cir, relation='has_circuito')

    # 6) Tramos
    df_tra = pd.read_excel(xlsx_path, sheet_name='Tramo', dtype={'id': str, 'circuito_id': str, 'nodo1_id': str, 'nodo2_id': str})
    for _, r in df_tra.iterrows():
        tra = f"T_{r['id']}"
        G.add_node(tra, type='Tramo')
        parent = f"C_{r['circuito_id']}"
        if G.has_node(parent):
            G.add_edge(parent, tra, relation='has_tramo')
        # conectar a barras (nodos)
        for end in ['nodo1_id','nodo2_id']:
            b = f"B_{r[end]}"
            if G.has_node(b):
                G.add_edge(tra, b, relation='connects')

    # 7) Limpiar None en atributos
    for _, attrs in G.nodes(data=True):
        for k,v in list(attrs.items()):
            if v is None:
                attrs[k] = ''
    for u,v,attrs in G.edges(data=True):
        for k,val in list(attrs.items()):
            if val is None:
                attrs[k] = ''

    # 8) Exportar GraphML
    out = Path(out_path)
    nx.write_graphml(G, out)
    print(f"GraphML limpio guardado en {out}")


def main():
    parser = argparse.ArgumentParser(description='Exportar SEN KG a GraphML limpio')
    parser.add_argument('--xlsx', required=True, help='ruta a instalaciones_activos.xlsx')
    parser.add_argument('--out', required=True, help='ruta de salida .graphml')
    args = parser.parse_args()
    build_and_export(args.xlsx, args.out)

if __name__ == '__main__':
    main()
