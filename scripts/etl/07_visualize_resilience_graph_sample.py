#!/usr/bin/env python3
import argparse
import pandas as pd
from pyvis.network import Network

def build_resilience_graph_sample(xlsx_path: str, output_html: str):
    # 1) Cargamos todas las hojas relevantes
    xls = pd.ExcelFile(xlsx_path)

    df_emp = xls.parse('Empresas', dtype=str)          # columnas: id, nombre
    df_lin = xls.parse('Lineas', dtype=str)            # columnas: id, nombre, empresa_id, subestacion_origen_id, subestacion_destino_id
    df_sub = xls.parse('Subestaciones', dtype=str)     # columnas: id, nombre
    df_bar = xls.parse('Barras', dtype=str)            # columnas: id, nombre, subestacion_id

    # 2) Seleccionamos las 10 subestaciones más “alimentadas”
    all_sub_ids = pd.concat([
        df_lin['subestacion_origen_id'],
        df_lin['subestacion_destino_id']
    ]).value_counts()
    top10_subs = all_sub_ids.head(10).index.tolist()

    # 3) Filtramos cada DataFrame a estas 10 subestaciones y sus líneas/barras/empresas asociadas
    df_sub = df_sub[df_sub['id'].isin(top10_subs)]

    df_lin = df_lin[
        df_lin['subestacion_origen_id'].isin(top10_subs) |
        df_lin['subestacion_destino_id'].isin(top10_subs)
    ]

    emp_ids = df_lin['empresa_id'].unique().tolist()
    df_emp = df_emp[df_emp['id'].isin(emp_ids)]

    df_bar = df_bar[df_bar['subestacion_id'].isin(top10_subs)]

    # 4) Creamos la visualización con PyVis
    net = Network(height='800px', width='100%', directed=True)
    net.barnes_hut(gravity=-20000, central_gravity=0.3,
                   spring_length=200, spring_strength=0.001)
    net.toggle_physics(True)

    # 5) Añadimos nodos de Empresa (rojo)
    for _, r in df_emp.iterrows():
        net.add_node(f"E_{r['id']}",
                     label=r['nombre'],
                     title=f"Empresa: {r['nombre']}",
                     color='red',
                     size=30)

    # 6) Añadimos nodos de Línea (naranja) y aristas owns→
    for _, r in df_lin.iterrows():
        net.add_node(f"L_{r['id']}",
                     label=r['nombre'],
                     title=f"Línea: {r['nombre']}",
                     color='orange',
                     size=20)
        # —> CORRECCIÓN: cierro la comilla del primer f-string
        net.add_edge(f"E_{r['empresa_id']}", f"L_{r['id']}",
                     title='owns', color='darkred')

    # 7) Añadimos nodos de Subestación (azul) y aristas feeds→
    for _, r in df_sub.iterrows():
        net.add_node(f"S_{r['id']}",
                     label=r['nombre'],
                     title=f"S/E: {r['nombre']}",
                     color='blue',
                     size=25)
    for _, r in df_lin.iterrows():
        dst = r['subestacion_destino_id']
        if dst in top10_subs:
            net.add_edge(f"L_{r['id']}", f"S_{dst}",
                         title='feeds', color='darkblue')

    # 8) Añadimos nodos de Barra (verde) y aristas contains→
    for _, r in df_bar.iterrows():
        net.add_node(f"B_{r['id']}",
                     label=r['nombre'],
                     title=f"Barra: {r['nombre']}",
                     color='green',
                     size=15)
        net.add_edge(f"S_{r['subestacion_id']}", f"B_{r['id']}",
                     title='contains', color='darkgreen')

    # 9) Generamos el HTML
    net.show(output_html)
    print(f"Mini-grafo de resiliencia (10 subest.) generado en: {output_html}")

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--xlsx',   required=True,
                   help="Instalaciones maestro (instalaciones_activos.xlsx)")
    p.add_argument('--out',    required=True,
                   help="Salida .html de PyVis")
    args = p.parse_args()
    build_resilience_graph_sample(args.xlsx, args.out)
