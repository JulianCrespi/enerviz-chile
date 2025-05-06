#!/usr/bin/env python3
# scripts/etl/06_export_pyvis.py

"""
Genera un viewer HTML standalone interactivo del Knowledge Graph SEN usando PyVis.

Incluye todos los tipos de nodos (Empresa, Subestacion, Linea, Barra, Circuito, Tramo)
con labels legibles y tooltips con tipo y nombre.

Uso:
  pip install pyvis pandas networkx openpyxl
  python scripts/etl/06_export_pyvis.py \
    --xlsx data/raw/instalaciones_activos.xlsx \
    --out data/processed/kg_sen_pyvis.html

Salida:
  • HTML interactivo donde explorar activos y relaciones.
"""
import argparse
import sys
from pathlib import Path
import pandas as pd
import networkx as nx
from pyvis.network import Network


def build_pyvis(xlsx_path: str, out_html: str) -> None:
    # Crear grafo
    G = nx.Graph()

    # 1) Empresas
    df_emp = pd.read_excel(xlsx_path, sheet_name='Empresa', dtype={'id': str})
    for _, r in df_emp.iterrows():
        node = f"E_{r['id']}"
        G.add_node(node, type='Empresa', name=r.get('name',''))

    # 2) Subestaciones
    df_sub = pd.read_excel(xlsx_path, sheet_name='Subestaciones', dtype={'id': str, 'propietario_id': str, 'name': str})
    for _, r in df_sub.iterrows():
        node = f"S_{r['id']}"
        G.add_node(node, type='Subestacion', name=r.get('name',''))
        owner = f"E_{r['propietario_id']}"
        if G.has_node(owner):
            G.add_edge(owner, node, relation='owns')

    # 3) Lineas
    df_lin = pd.read_excel(xlsx_path, sheet_name='Linea', dtype={'id': str, 'propietario_id': str, 'name': str})
    for _, r in df_lin.iterrows():
        node = f"L_{r['id']}"
        G.add_node(node, type='Linea', name=r.get('name',''))
        owner = f"E_{r['propietario_id']}"
        if G.has_node(owner):
            G.add_edge(owner, node, relation='owns')

    # 4) Barras
    df_bar = pd.read_excel(xlsx_path, sheet_name='Barras', dtype={'id': str, 'patio_subestacion_id': str, 'name': str})
    for _, r in df_bar.iterrows():
        node = f"B_{r['id']}"
        G.add_node(node, type='Barra', name=r.get('name',''))
        parent = f"S_{r['patio_subestacion_id']}"
        if G.has_node(parent):
            G.add_edge(node, parent, relation='part_of')

    # 5) Circuitos
    df_cir = pd.read_excel(xlsx_path, sheet_name='Circuito', dtype={'id': str, 'linea_id': str})
    for _, r in df_cir.iterrows():
        node = f"C_{r['id']}"
        G.add_node(node, type='Circuito', name='')
        parent = f"L_{r['linea_id']}"
        if G.has_node(parent):
            G.add_edge(parent, node, relation='has_circuito')

    # 6) Tramos
    df_tra = pd.read_excel(xlsx_path, sheet_name='Tramo', dtype={'id': str, 'circuito_id': str, 'nodo1_id': str, 'nodo2_id': str})
    for _, r in df_tra.iterrows():
        node = f"T_{r['id']}"
        G.add_node(node, type='Tramo', name='')
        parent = f"C_{r['circuito_id']}"
        if G.has_node(parent):
            G.add_edge(parent, node, relation='has_tramo')
        # Conectar a las barras (nodos)
        for end in ['nodo1_id', 'nodo2_id']:
            barra = f"B_{r[end]}"
            if G.has_node(barra):
                G.add_edge(node, barra, relation='connects')

    # 7) Limpiar posibles None en atributos
    for _, attrs in G.nodes(data=True):
        for k, v in list(attrs.items()):
            if v is None:
                attrs[k] = ''
    for u, v, attrs in G.edges(data=True):
        for k, val in list(attrs.items()):
            if val is None:
                attrs[k] = ''

    # 8) Configurar PyVis
    net = Network(
        height='800px', width='100%',
        bgcolor='#ffffff', font_color='black',
        directed=False, notebook=False
    )
    net.force_atlas_2based()

    # Color por tipo
    color_map = {
        'Empresa': 'red',
        'Subestacion': 'blue',
        'Linea': 'orange',
        'Barra': 'green',
        'Circuito': 'purple',
        'Tramo': 'gray'
    }

    # 9) Añadir nodos y tooltips
    for node, data in G.nodes(data=True):
        label = data['name'] or f"{data['type']} {node.split('_',1)[1]}"
        title = f"Type: {data['type']}<br>Name: {data.get('name','')}<br>ID: {node.split('_',1)[1]}"
        net.add_node(
            node,
            label=label,
            title=title,
            color=color_map.get(data['type'], 'black'),
            size=10
        )

    # 10) Añadir aristas con relación
    for u, v, data in G.edges(data=True):
        title = data.get('relation', '')
        net.add_edge(u, v, title=title)

    # 11) Exportar HTML
    out = Path(out_html)
    net.write_html(str(out), open_browser=False)
    print(f"HTML interactivo guardado en {out}")


def main():
    parser = argparse.ArgumentParser(description='Exportar SEN KG a HTML interactivo PyVis')
    parser.add_argument('--xlsx', required=True, help='ruta a instalaciones_activos.xlsx')
    parser.add_argument('--out', required=True, help='archivo de salida HTML')
    args = parser.parse_args()
    build_pyvis(args.xlsx, args.out)

if __name__ == '__main__':
    main()
