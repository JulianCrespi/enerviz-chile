/* ------------------------------------------------------------------
   Price hook + barra-name utilities
------------------------------------------------------------------ */
import { useEffect, useState } from "react";

/* ---------- price record type ---------- */
export interface PriceRec {
  barra: string;
  ts:    string;
  price: number;
  lat:   number;
  lon:   number;
}

/* ---------- fetch the sample JSON ---------- */
export function usePrices(): PriceRec[] {
  const [data, setData] = useState<PriceRec[]>([]);

  useEffect(() => {
    const load = () => 
      fetch(`/prices_sample.json?${Date.now()}`)
        .then(r => r.json())
        .then(setData);
    
    load();
    const id = setInterval(load, 5 * 60 * 1000); // 5 minutes
    
    return () => clearInterval(id);
  }, []);

  return data;
}

/* ---------- barra alias table ------------ */
import aliasCsv from "../data/barra_alias.csv?raw";

const aliasMap = new Map<string, string>();
aliasCsv.trim().split("\n").slice(1).forEach(l => {
  const [alias, barra] = l.split(",");
  aliasMap.set(alias.trim().toLowerCase(), barra.trim().toLowerCase());
});

/* ---------- helpers to clean / normalise names ---------- */
function removeAccents(s: string) {
  return s.normalize("NFD").replace(/\p{Diacritic}/gu, "");
}
function clean(txt: string) {
  return removeAccents(txt)
    .toLowerCase()
    .replace(/\b\d+\s*k?v\b/g, "")   // strip "220kv", "154 kV", …
    .replace(/\s+/g, " ")
    .trim();
}
export function normalise(name: string): string {
  const k = clean(name);
  return aliasMap.get(k) ?? k;
}
