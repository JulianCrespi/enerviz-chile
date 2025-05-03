#!/usr/bin/env python3
"""
Descarga y normaliza datasets SIP (Coordinador Eléctrico Nacional).

Ejemplos:
  python fetch_sip.py list
  python fetch_sip.py fetch cmg_linea --month 2025-03
  python fetch_sip.py peek  cmg_linea
"""
from __future__ import annotations
import argparse, csv, gzip, io, random, sys, textwrap
from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup   # pip install beautifulsoup4

# ─────────────────────────  Config  ─────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0."
        f"{random.randint(1000,4000)}.{random.randint(10,99)} Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://www.coordinador.cl/",
}
DATA_DIR = Path(__file__).with_suffix("").parent / "data"

TARGETS = {
    # key           base-url                                             filtros        plantilla
    "cmg_linea": (
        "https://www.coordinador.cl/mercados/graficos/costos-marginales/costo-marginal-en-linea",
        ["month"], "cmg_linea_{month}.tsv",
    ),
    "cmg_online_hist": (
        "https://www.coordinador.cl/mercados/graficos/costos-marginales/costo-marginal-online",
        ["date"],  "cmg_online_{date}.tsv",
    ),
    "cmg_real": (
        "https://www.coordinador.cl/mercados/graficos/costos-marginales/costo-marginal-real",
        ["year", "month", "barra"], "cmg_real_{year}-{month:02d}.tsv",
    ),
    "demanda": (
        "https://www.coordinador.cl/operacion/graficos/operacion-real/demanda-real",
        ["date"], "demanda_real_{date}.tsv",
    ),
    "generacion": (
        "https://www.coordinador.cl/operacion/graficos/operacion-real/generacion-real",
        ["month"], "generacion_{month}.tsv",
    ),
    "potencia_transitada": (
        "https://www.coordinador.cl/operacion/graficos/operacion-real/potencia-transitada-por-el-sistema-de-transmision",
        ["date"], "pot_transitada_{date}.tsv",
    ),
    "embalses": (
        "https://www.coordinador.cl/operacion/graficos/operacion-real/cotas-y-niveles-de-embalses-reales",
        ["date"], "embalses_{date}.tsv",
    ),
}

# ────────────────────────  Helpers  ────────────────────────
def build_query(base: str, **p) -> str:
    if "date" in p:
        return f"{base}?fechaInicio={p['date']}&fechaFin={p['date']}"
    if "month" in p:
        y, m = p["month"].split("-")
        return f"{base}?mes={m}&anio={y}"
    if "year" in p:
        url = f"{base}?anio={p['year']}"
        if "month" in p:
            url += f"&mes={p['month']:02d}"
        if "barra" in p:
            url += f"&barra={p['barra']}"
        return url
    return base

def download(url: str) -> tuple[bytes, str]:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.content, r.headers.get("Content-Type", "")

def is_html(raw: bytes, ctype: str) -> bool:
    return ("html" in ctype.lower()) or raw.strip().lower().startswith(b"<!doctype")

def parse_tsv(raw: bytes) -> pd.DataFrame:
    text = raw.decode("utf-8", "replace")
    # 1) intentamos autodetectar
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(text.splitlines()[0])
        df = pd.read_csv(io.StringIO(text), delimiter=dialect.delimiter)
        if len(df.columns) > 1:
            return df
    except Exception:
        pass
    # 2) intentamos separador tab
    for sep in ("\t", ";", "|"):
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep, engine="python", on_bad_lines="skip")
            if len(df.columns) > 1:
                return df
        except Exception:
            continue
    raise ValueError("No pude detectar un separador válido.")

def save(df: pd.DataFrame, name: str) -> None:
    out = DATA_DIR / f"{name}.csv.gz"
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8") as zf:
        df.to_csv(zf, index=False, sep="|")
    print(f"✔ Guardado {out} ({out.stat().st_size/1024:.0f} KB)")

def fetch(target: str, **flt) -> None:
    base, allowed, tmpl = TARGETS[target]
    if bad := [k for k in flt if k not in allowed]:
        sys.exit(f"Filtros {bad} no permitidos para {target}")
    url = build_query(base, **flt)
    print("→", url)

    raw, ctype = download(url)
    if is_html(raw, ctype):
        print("✖ El servidor respondió HTML. Probablemente:")
        print("   • el dataset para esos filtros aún no está publicado, o")
        print("   • los parámetros son incorrectos.")
        sys.exit(1)

    df = parse_tsv(raw)
    df.columns = [c.strip().lower() for c in df.columns]
    save(df, tmpl.format(**flt))

def peek(target: str) -> None:
    """Muestra los meses disponibles leyendo el HTML del selector <option>."""
    base, allowed, _ = TARGETS[target]
    if "month" not in allowed:
        sys.exit("peek solo funciona en targets mensuales (--month).")
    html, _ = download(base)
    soup = BeautifulSoup(html, "html.parser")
    opts = [o["value"] for o in soup.select("select option[value]") if o["value"]]
    print("Meses disponibles:", ", ".join(sorted(opts)))

# ─────────────────────────  CLI  ───────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            Downloader robusto de datos SIP.

            Comandos:
              list                           Lista targets y filtros
              fetch <target> [filtros]       Descarga dataset
              peek  <target>                 Muestra meses disponibles (HTML)
        """),
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")

    fp = sub.add_parser("fetch")
    fp.add_argument("target", choices=TARGETS.keys())
    fp.add_argument("--date")        # YYYY-MM-DD
    fp.add_argument("--month")       # YYYY-MM
    fp.add_argument("--year", type=int)
    fp.add_argument("--barra")

    pp = sub.add_parser("peek")
    pp.add_argument("target", choices=[k for k, (_, f, _) in TARGETS.items() if "month" in f])

    args = p.parse_args()

    if args.cmd == "list":
        for k, (_, f, _) in TARGETS.items():
            print(f"{k:20} filtros: {f}")
        return
    if args.cmd == "peek":
        peek(args.target)
        return
    if args.cmd == "fetch":
        flt = {k: v for k, v in vars(args).items() if k in ("date", "month", "year", "barra") and v}
        fetch(args.target, **flt)

if __name__ == "__main__":
    main()
