#!/usr/bin/env python3
# scripts/etl/02_build_transmission_graph.py

"""
Construcción del grafo de transmisión del SEN usando el inventario maestro
(instalaciones_activos.xlsx) como fuente única de verdad para la topología.

**Nota**: Dado que el shapefile de IDE Energía no siempre está actualizado, este script:
  - Usa exclusivamente la hoja "Tramo" del Excel maestro para definir todas las conexiones lógicas
    (nodo1_id ↔ nodo2_id).
  - Integra geometría donde esté disponible en `tramo_geom.parquet`.
  - Marca y exporta las aristas faltantes de geometría para auditoría.

Salida esperada:
  - Métricas generales impresas en consola.
  - `data/processed/node_degrees.csv`: grado de cada nodo.
  - `data/processed/edges_missing_geom.csv`: aristas sin geometría.
  - `data/processed/transmission_graph_sample.png`: imagen de un subgrafo de muestra.
"""
import argparse
import sys
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path


def build_graph(xlsx_path: str, parquet_path: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1) Leer inventario maestro con pandas
    try:
        df_tramo = pd.read_excel(
            xlsx_path,
            sheet_name='Tramo',
            dtype={'id': int, 'circuito_id': int, 'nodo1_id': int, 'nodo2_id': int}
        )
    except Exception as e:
        print(f"ERROR al leer hoja 'Tramo' del Excel: {e}", file=sys.stderr)
        sys.exit(1)
    df_tramo = df_tramo.rename(columns={'id': 'tramo_id'})
    df_tramo = df_tramo[['tramo_id', 'circuito_id', 'nodo1_id', 'nodo2_id']]
    print(f"Total de tramos en Excel: {len(df_tramo)}")

    # 2) Leer geometría disponible de parquet
    try:
        df_geom = pd.read_parquet(parquet_path, columns=['id', 'geom'])
    except Exception as e:
        print(f"ERROR al leer Parquet {parquet_path}: {e}", file=sys.stderr)
        sys.exit(1)
    df_geom = df_geom.rename(columns={'id': 'tramo_id'})
    print(f"Tramos con geometría parquet: {len(df_geom)}")

    # 3) Unir lógica + geometría
    df_edges = df_tramo.merge(df_geom, on='tramo_id', how='left')
    missing_geom = df_edges['geom'].isna().sum()
    print(f"Aristas sin geometría (faltantes en shapefile): {missing_geom}")

    # 4) Construir grafo con nodos y aristas
    G = nx.Graph()
    for _, r in df_edges.iterrows():
        u = int(r['nodo1_id'])
        v = int(r['nodo2_id'])
        G.add_edge(u, v, tramo_id=int(r['tramo_id']), has_geom=not pd.isna(r['geom']))

    # 5) Métricas de grafo y componentes
    print(f"Nodos totales: {G.number_of_nodes()}")
    print(f"Aristas totales: {G.number_of_edges()}")
    comps = list(nx.connected_components(G))
    print(f"Componentes conectados: {len(comps)}")
    print(f"Tamaño componente mayor: {len(max(comps, key=len))}")

    # 6) Exportar métricas de nodo
    degrees = pd.DataFrame(G.degree(), columns=['node_id', 'degree'])
    degrees.to_csv(out / 'node_degrees.csv', index=False)
    print(f"Node degree CSV guardado en {out / 'node_degrees.csv'}")

    # 7) Exportar aristas sin geometría para auditoría
    missing_edges = df_edges.loc[
        df_edges['geom'].isna(), ['tramo_id', 'circuito_id', 'nodo1_id', 'nodo2_id']
    ]
    missing_edges.to_csv(out / 'edges_missing_geom.csv', index=False)
    print(f"Audit log de aristas sin geometría guardado en {out / 'edges_missing_geom.csv'}")

    # 8) Visualizar subgrafo de muestra
    sample_edges = list(G.edges())[:200]
    Gs = G.edge_subgraph(sample_edges).copy()
    pos = nx.spring_layout(Gs, seed=42)
    plt.figure(figsize=(8, 8))
    nx.draw(Gs, pos, node_size=20, node_color='skyblue', edge_color='gray', linewidths=0.2)
    plt.title('Subgrafo de 200 aristas (topología SEN)')
    plt.axis('off')
    plt.tight_layout()
    img_path = out / 'transmission_graph_sample.png'
    plt.savefig(img_path, dpi=150)
    print(f"Imagen de muestra guardada en {img_path}")


def main():
    parser = argparse.ArgumentParser(description='Construir grafo de transmisión desde Excel maestro')
    parser.add_argument('--xlsx', required=True, help='ruta a instalaciones_activos.xlsx')
    parser.add_argument('--parquet', required=True, help='ruta a tramo_geom.parquet')
    parser.add_argument('--out', default='data/processed', help='directorio de salida')
    args = parser.parse_args()
    build_graph(args.xlsx, args.parquet, args.out)

if __name__ == '__main__':
    main()
