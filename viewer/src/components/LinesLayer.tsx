import { useEffect, useState } from "react";
import { GeoJsonDataSource } from "resium";
import {
  Color,
  PolylineArrowMaterialProperty,   // ← viene de **cesium**, no de resium
} from "cesium";

/* Paleta por tensión (kV) */
const kvColor = (kv: number): Color =>
  kv >= 500 ? Color.RED.withAlpha(0.9)
  : kv >= 220 ? Color.ORANGE.withAlpha(0.9)
  : kv >= 154 ? Color.YELLOW.withAlpha(0.9)
  : kv >= 110 ? Color.CYAN.withAlpha(0.9)
  : Color.GRAY.withAlpha(0.6);

export default function LinesLayer() {
  const [source, setSource] = useState<GeoJsonDataSource>();

  useEffect(() => {
    const ds = new GeoJsonDataSource("lines");
    ds.load("/lines_barras_tess.geojson", {
      clampToGround: true,
      stroke: Color.WHITE,
      strokeWidth: 2,
    })
      .then(() => {
        ds.entities.values.forEach(ent => {
          if (!ent.polyline) return;
          const kv = ent.properties?.volt?.getValue() as number | undefined;
          ent.polyline.material = new PolylineArrowMaterialProperty(kvColor(kv ?? 0));
          ent.polyline.width = 10;

          /* Tooltip enriquecido */
          const p = ent.properties;
          const fmt = (x: any) => x ?? "—";
          ent.description = `
<strong>${fmt(p.nombre?.getValue())}</strong><br/>
<b>Voltaje:</b> ${fmt(kv)} kV<br/>
<b>Circuito:</b> ${fmt(p.circuit?.getValue())}<br/>
<b>Longitud:</b> ${Number(p.length_km?.getValue() || 0).toFixed(2)} km<br/>
<b>Tipo:</b> ${fmt(p.tipo?.getValue())}<br/>
<b>Empresa:</b> ${fmt(p.owner?.getValue())}<br/>
<b>Estado:</b> ${fmt(p.estado?.getValue())}<br/>
<b>Comuna:</b> ${fmt(p.comuna?.getValue())}
`;
        });
        setSource(ds);
      })
      .catch(console.error);

    return () => {
      if (source) source.entities.removeAll();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!source) return null;
  return <primitive object={source} />;
}
