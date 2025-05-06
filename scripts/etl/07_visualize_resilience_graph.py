#!/usr/bin/env python3
# scripts/etl/07_visualize_resilience_graph.py

"""
Visualizador de resiliencia SEN: Empresa → Línea → Subestación → Barra
con dependencias.

Nodos:
  - Empresa
  - Línea (Tramo)
  - Subestación
  - Barra

Aristas:
  - owns     : Empresa → Línea, Empresa → Subestación
  - feeds    : Línea → Subestación (feed)
  - contains : Subestación → Barra
  - shares_sub: Empresa — Empresa (comparten Subestación)
  - shares_bar: Empresa — Empresa (comparten Barra)

Uso:
  pip install pyvis pandas networkx openpyxl
  python scripts/etl/07_visualize_resilience_graph.py \
    --xlsx data/raw/instalaciones_activos.xlsx \
    --out data/processed/resilience_graph.html
"""
import argparse
import pandas as pd
import networkx as nx
import itertools
from pathlib import Path
from pyvis.network import Network

# Estilos de nodo: color y tamaño
NODE_STYLE = {
    'Empresa':     {'color':'#d62728','size':25},  # rojo
    'Linea':       {'color':'#ff7f0e','size':15},  # naranja
    'Subestacion': {'color':'#1f77b4','size':12},  # azul
    'Barra':       {'color':'#2ca02c','size':8},   # verde
}

# Estilos de arista: color, grosor y flechas
EDGE_STYLE = {
    'owns':       {'color':'#555555','width':1,'arrows':'to'},
    'feeds':      {'color':'#999999','width':1,'arrows':'to'},
    'contains':   {'color':'#bbbbbb','width':1,'arrows':'to'},
    'shares_sub': {'color':'purple','width':2,'arrows':False},
    'shares_bar': {'color':'darkgreen','width':2,'arrows':False},
}


def build_resilience_graph(xlsx_path: str, out_html: str):
    # Carga dinámica de nombres de hoja
    xls = pd.ExcelFile(xlsx_path)
    # detectar hojas por keywords
    sheet_emp = next(s for s in xls.sheet_names if 'empres' in s.lower())
    sheet_lin = next(s for s in xls.sheet_names if 'tram' in s.lower() or 'linea' in s.lower())
    sheet_sub = next(s for s in xls.sheet_names if 'subest' in s.lower())
    sheet_bar = next(s for s in xls.sheet_names if 'bar' in s.lower())

    df_emp = pd.read_excel(xlsx_path, sheet_name=sheet_emp, dtype=str)
    df_lin = pd.read_excel(xlsx_path, sheet_name=sheet_lin, dtype=str)
    df_sub = pd.read_excel(xlsx_path, sheet_name=sheet_sub, dtype=str)
    df_bar = pd.read_excel(xlsx_path, sheet_name=sheet_bar, dtype=str)

    # detectar columnas clave
    emp_id_col = next(c for c in df_emp.columns if c.lower()=='id')
    emp_name_col = next((c for c in df_emp.columns if 'razon' in c.lower() or 'name' in c.lower()), emp_id_col)

    lin_id_col = next(c for c in df_lin.columns if c.lower()=='id')
    lin_name_col = next((c for c in df_lin.columns if 'nombre' in c.lower()), lin_id_col)
    lin_owner_col = next((c for c in df_lin.columns if 'propietar' in c.lower() or 'empresa' in c.lower()), None)
    lin_sub_cols = [c for c in df_lin.columns if 'subestac' in c.lower()]

    sub_id_col = next(c for c in df_sub.columns if c.lower()=='id')
    sub_name_col = next((c for c in df_sub.columns if 'nombre' in c.lower()), sub_id_col)
    sub_owner_col = next((c for c in df_sub.columns if 'propietar' in c.lower() or 'empresa' in c.lower()), None)

    bar_id_col = next(c for c in df_bar.columns if c.lower()=='id')
    bar_name_col = next((c for c in df_bar.columns if 'nombre' in c.lower()), bar_id_col)
    bar_parent_col = next((c for c in df_bar.columns if 'subestac' in c.lower()), None)

    # Mapas de relación
    sub2emp = df_sub.set_index(sub_id_col)[sub_owner_col].astype(str).to_dict() if sub_owner_col else {}
    lin2emp = df_lin.set_index(lin_id_col)[lin_owner_col].astype(str).to_dict() if lin_owner_col else {}
    bar2sub = df_bar.set_index(bar_id_col)[bar_parent_col].astype(str).to_dict() if bar_parent_col else {}

    # Construir grafo dirigido
    G = nx.DiGraph()

    # Nodos Empresa
    for _, r in df_emp.iterrows():
        eid = str(r[emp_id_col])
        label = r.get(emp_name_col, eid)
        G.add_node(f"E_{eid}", type='Empresa', label=str(label))

    # Nodos Linea + owns
    for _, r in df_lin.iterrows():
        lid = str(r[lin_id_col])
        label = r.get(lin_name_col, lid)
        G.add_node(f"L_{lid}", type='Linea', label=str(label))
        owner = lin2emp.get(lid)
        if owner and G.has_node(f"E_{owner}"):
            G.add_edge(f"E_{owner}", f"L_{lid}", relation='owns')

    # Nodos Subestacion + owns
    for _, r in df_sub.iterrows():
        sid = str(r[sub_id_col])
        label = r.get(sub_name_col, sid)
        G.add_node(f"S_{sid}", type='Subestacion', label=str(label))
        owner = sub2emp.get(sid)
        if owner and G.has_node(f"E_{owner}"):
            G.add_edge(f"E_{owner}", f"S_{sid}", relation='owns')

    # Nodos Barra + contains
    for _, r in df_bar.iterrows():
        bid = str(r[bar_id_col])
        label = r.get(bar_name_col, bid)
        G.add_node(f"B_{bid}", type='Barra', label=str(label))
        parent = bar2sub.get(bid)
        if parent and G.has_node(f"S_{parent}"):
            G.add_edge(f"S_{parent}", f"B_{bid}", relation='contains')

    # Conexiones feeds: Linea -> Subestacion
    for _, r in df_lin.iterrows():
        lid = str(r[lin_id_col])
        for col in lin_sub_cols:
            sid = r.get(col)
            if pd.notna(sid):
                sid_str = str(int(float(sid))) if not isinstance(sid, str) else sid
                if G.has_node(f"S_{sid_str}"):
                    G.add_edge(f"L_{lid}", f"S_{sid_str}", relation='feeds')

    # shares_sub: empresas que comparten subestacion
    for sid, owner in sub2emp.items():
        users = {owner}
        # empresas de lineas conectadas
        for lid, emp in lin2emp.items():
            matches = df_lin[df_lin[lin_id_col]==lid][lin_sub_cols].values.flatten()
            if any(str(sid)==str(r) for r in matches if pd.notna(r)):
                users.add(emp)
        for a,b in itertools.combinations(sorted(users),2):
            G.add_edge(f"E_{a}", f"E_{b}", relation='shares_sub')

    # shares_bar: empresas que comparten barra (vía subestacion)
    bar_to_emps = {}
    for bid, sid in bar2sub.items():
        emp = sub2emp.get(sid)
        if emp:
            bar_to_emps.setdefault(bid,set()).add(emp)
    for owners in bar_to_emps.values():
        for a,b in itertools.combinations(sorted(owners),2):
            G.add_edge(f"E_{a}", f"E_{b}", relation='shares_bar')

    # Render con PyVis
    net = Network(
        height='800px', width='100%', 
        bgcolor='#ffffff', font_color='black', 
        directed=True, notebook=False
    )
    net.toggle_physics(True)

    for n,d in G.nodes(data=True):
        style = NODE_STYLE[d['type']]
        net.add_node(
            n, label=d['label'], title=d['label'],
            color=style['color'], size=style['size']
        )
    for u,v,d in G.edges(data=True):
        style = EDGE_STYLE.get(d['relation'], EDGE_STYLE['feeds'])
        net.add_edge(
            u, v,
            color=style['color'], width=style['width'],
            arrows=style['arrows'], title=d['relation']
        )

    out = Path(out_html)
    net.write_html(str(out), open_browser=False)
    print(f"✓ Resilience graph generado: {out}")

if __name__=='__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--xlsx', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    build_resilience_graph(args.xlsx, args.out)
