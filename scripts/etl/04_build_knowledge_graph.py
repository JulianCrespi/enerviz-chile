#!/usr/bin/env python3
# scripts/etl/04_build_knowledge_graph.py

"""
Construcción de un Knowledge Graph del SEN a partir de instalaciones_activos.xlsx.
Nodos tipados: Empresa, Subestacion, Barra, Linea, Circuito, Tramo.
Aristas etiquetadas: owns, part_of, has_circuito, has_tramo, connects.

Salida:
  • data/processed/kg_sen.graphml (GraphML completo)
  • data/processed/kg_sen.json    (GraphSON _opcional_)
"""
import argparse
import sys
import pandas as pd
import networkx as nx
from pathlib import Path


def build_kg(xlsx_path: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    G = nx.DiGraph()

    # 1) Empresas
    df_emp = pd.read_excel(xlsx_path, sheet_name='Empresa', dtype={'id': str})
    for _, r in df_emp.iterrows():
        node = f"E_{r['id']}"
        G.add_node(node, type='Empresa', name=r.get('name', ''))

    # 2) Subestaciones
    df_sub = pd.read_excel(xlsx_path, sheet_name='Subestaciones', dtype={'id': str, 'propietario_id': str})
    for _, r in df_sub.iterrows():
        node = f"S_{r['id']}"
        G.add_node(node, type='Subestacion', name=r.get('name', ''), lat=r.get('lat', None), lon=r.get('lon', None))
        owner = f"E_{r['propietario_id']}"
        if owner in G:
            G.add_edge(owner, node, relation='owns')

    # 3) Barras
    df_barra = pd.read_excel(xlsx_path, sheet_name='Barras', dtype={'id': str, 'patio_subestacion_id': str})
    for _, r in df_barra.iterrows():
        node = f"B_{r['id']}"
        G.add_node(node, type='Barra', tension_kV=r.get('tension_kV', None))
        parent = f"S_{r['patio_subestacion_id']}"
        if parent in G:
            G.add_edge(node, parent, relation='part_of')

    # 4) Lineas
    df_lin = pd.read_excel(xlsx_path, sheet_name='Linea', dtype={'id': str, 'propietario_id': str})
    for _, r in df_lin.iterrows():
        node = f"L_{r['id']}"
        G.add_node(node, type='Linea', name=r.get('name', ''), tension_kV=r.get('voltaje_kV', None))
        owner = f"E_{r['propietario_id']}"
        if owner in G:
            G.add_edge(owner, node, relation='owns')

    # 5) Circuitos
    df_cir = pd.read_excel(xlsx_path, sheet_name='Circuito', dtype={'id': str, 'linea_id': str})
    for _, r in df_cir.iterrows():
        node = f"C_{r['id']}"
        G.add_node(node, type='Circuito')
        parent = f"L_{r['linea_id']}"
        if parent in G:
            G.add_edge(parent, node, relation='has_circuito')

    # 6) Tramos
    df_tra = pd.read_excel(xlsx_path, sheet_name='Tramo', dtype={'id': str, 'circuito_id': str, 'nodo1_id': str, 'nodo2_id': str})
    for _, r in df_tra.iterrows():
        node = f"T_{r['id']}"
        G.add_node(node, type='Tramo')
        parent = f"C_{r['circuito_id']}"
        if parent in G:
            G.add_edge(parent, node, relation='has_tramo')
        # conectar a barras
        for end in ('nodo1_id','nodo2_id'):
            barr = f"B_{r[end]}"
            if barr in G:
                G.add_edge(node, barr, relation='connects')

    # 7) Guardar GraphML y JSON
    path_graphml = out / 'kg_sen.graphml'
    nx.write_graphml(G, path_graphml)
    print(f"GraphML guardado en {path_graphml}")

    try:
        import json
        data = nx.readwrite.json_graph.node_link_data(G)
        with open(out / 'kg_sen.json', 'w') as f:
            json.dump(data, f)
        print(f"GraphSON guardado en {out / 'kg_sen.json'}")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description='Construir Knowledge Graph del SEN')
    parser.add_argument('--xlsx', required=True, help='ruta a instalaciones_activos.xlsx')
    parser.add_argument('--out', default='data/processed', help='directorio de salida')
    args = parser.parse_args()
    build_kg(args.xlsx, args.out)

if __name__ == '__main__':
    main()
