import {
  Viewer, GeoJsonDataSource, Entity,
} from "resium";
import {
  Ion, Cartesian3, PolylineArrowMaterialProperty,
  Color, HeightReference, JulianDate,
} from "cesium";

import { usePrices, normalise } from "./hooks/usePrices";
import { colorForPrice } from "./utils/colorRamp";

Ion.defaultAccessToken = import.meta.env.VITE_CESIUM_ION_TOKEN;

/* voltage colour */
const vCol = (v?: number) =>
  v === undefined ? Color.GRAY.withAlpha(0.6)
  : v >= 400 ? Color.RED.withAlpha(0.9)
  : v >= 200 ? Color.CYAN.withAlpha(0.9)
  : v >= 100 ? Color.LIME.withAlpha(0.9)
  : Color.YELLOW.withAlpha(0.9);

const toA = (p: any): Cartesian3[] =>
  Array.isArray(p) ? p : p.getValue(JulianDate.now()) as Cartesian3[];

/* generation barras */
const genSet = new Set<string>();
fetch("/generation_barras.json")
  .then(r => r.json())
  .then((l: string[]) => l.forEach(b => genSet.add(normalise(b))))
  .catch(console.error);

export default function App() {
  const prices = usePrices();

  return (
    <Viewer full baseLayerPicker>
      <GeoJsonDataSource
        data="/lines_barras_tess.geojson"
        clampToGround
        onLoad={ds => {
          ds.entities.values.forEach(ent => {
            if (!ent.polyline) return;
            const p      = ent.properties;
            const volt   = p.volt?.getValue() as number | undefined;
            const tipo   = p.tipo?.getValue();
            const aId    = normalise(p.startBarra?.getValue() ?? "");
            const bId    = normalise(p.endBarra?.getValue()   ?? "");
            const aGen   = genSet.has(aId);
            const bGen   = genSet.has(bId);

            /* direction */
            let forward: boolean;
            if (tipo && String(tipo).toLowerCase() === "dedicado") {
              forward = true;               // IDE stores gen → grid
            } else if (aGen !== bGen) {
              forward = aGen;               // out of generator
            } else {
              // keep shapefile order (best guess)
              forward = true;
            }
            if (!forward) {
              const rev = toA(ent.polyline.positions).slice().reverse();
              ent.polyline.positions = rev;
            }

            ent.polyline.material = new PolylineArrowMaterialProperty(vCol(volt));
            ent.polyline.width    = 8;

            /* tooltip only on segments that still carry 'nombre' */
            if (p.nombre) {
              const fmt = (v:any)=>v??"—";
              ent.description = `
<strong>${fmt(p.nombre.getValue())}</strong><br/>
<b>Voltaje:</b> ${volt ?? "—"} kV<br/>
<b>Circuito:</b> ${fmt(p.circuit?.getValue())}<br/>
<b>Longitud:</b> ${Number(p.length_km?.getValue()??0).toFixed(2)} km<br/>
<b>Tipo:</b> ${fmt(tipo)}<br/>
<b>Empresa:</b> ${fmt(p.owner?.getValue())}<br/>
<b>Estado:</b> ${fmt(p.estado?.getValue())}<br/>
<b>Comuna:</b> ${fmt(p.comuna?.getValue())}
`;
            }
          });
        }}
      />

      {/* price orbs */}
      {prices.map(rec => (
        <Entity
          key={rec.barra + rec.ts}
          position={Cartesian3.fromDegrees(rec.lon, rec.lat)}
          billboard={{
            image: "/orb.svg",
            color: colorForPrice(rec.price),
            scale: 0.4,
            heightReference: HeightReference.CLAMP_TO_GROUND,
          }}
          description={`<b>${rec.barra}</b><br/>${rec.ts}<br/><b>$${rec.price}</b> USD/MWh`}
        />
      ))}
    </Viewer>
  );
}
