import pandas as pd
import requests
import pathlib
import pytz
import datetime as dt

URL = "https://coordinador.cl/api/v1/mercados/precios_mercado?formato=csv"
csv = requests.get(URL, timeout=60).content.decode("latin1")
df = pd.read_csv(pd.compat.StringIO(csv), sep=";")
df = df.rename(columns={"barra": "barra", "cmg": "price", "fecha": "ts"})

# keep last 24 h only
now = dt.datetime.now(pytz.timezone("America/Santiago"))
df = df[pd.to_datetime(df.ts) > now - dt.timedelta(hours=24)]

out = pathlib.Path("public/prices_sample.json")
out.write_text(df.to_json(orient="records", force_ascii=False))
print("✅ price JSON updated:", out) 