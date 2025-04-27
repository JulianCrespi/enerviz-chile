// viewer/src/App.tsx
import { usePrices } from "./hooks/usePrices";
import { colorForPrice } from "./utils/colorRamp";

import {
  Viewer,
  GeoJsonDataSource,
  Entity,
} from "resium";
import {
  Ion,
  Cartesian3,
  PolylineArrowMaterialProperty,
  Color,
  HeightReference,
} from "cesium";

// ---------------------------------------------------------------------
//  Cesium ion – keep your token in .env  (VITE_CESIUM_ION_TOKEN=…)
//  ➜ Cesium will automatically load Bing Aerial with Labels.
// ---------------------------------------------------------------------
Ion.defaultAccessToken = import.meta.env.VITE_CESIUM_ION_TOKEN;

// Demo arrow — choose two coords that lie on a real line
const demoArrowPositions = Cartesian3.fromDegreesArray([
  -71.07965, -35.827,
  -71.08326, -35.83933,
]);

export default function App() {
  const prices = usePrices(); // loads /prices_sample.json once

  return (
    <Viewer      /* default baseLayerPicker = true */
      full
      timeline={true}
      animation={true}
    >
      {/* Transmission network */}
      <GeoJsonDataSource data="/lines.geojson" clampToGround />

      {/* Price orbs */}
      {prices.map((rec, i) => (
        <Entity
          key={i}
          name={rec.barra}
          position={Cartesian3.fromDegrees(rec.lon, rec.lat, 0)}
          billboard={{
            image: "/orb.svg",           // 32×32 icon in /viewer/public
            color: colorForPrice(rec.price),
            scale: 0.4,
            heightReference: HeightReference.CLAMP_TO_GROUND,
          }}
          description={
            `<b>${rec.barra}</b><br/>${rec.ts}<br/>$${rec.price} USD/MWh`
          }
        />
      ))}

      {/* Prototype flow-arrow on one line segment */}
      <Entity
        polyline={{
          positions: demoArrowPositions,
          width: 6,
          clampToGround: true,
          material: new PolylineArrowMaterialProperty(
            Color.CYAN.withAlpha(0.9)
          ),
        }}
      />
    </Viewer>
  );
}
