import { useEffect, useState } from "react";
import {
  Viewer,
  GeoJsonDataSource,
} from "resium";
import {
  Ion,
  BingMapsImageryProvider,
  BingMapsStyle,
  createWorldTerrainAsync,     // ✅ new async helper
  TerrainProvider,
} from "cesium";

Ion.defaultAccessToken = import.meta.env.VITE_CESIUM_ION_TOKEN;

const bingLabels = new BingMapsImageryProvider({
  url: "https://dev.virtualearth.net",
  key: Ion.defaultAccessToken,
  mapStyle: BingMapsStyle.AERIAL_WITH_LABELS,
});

export default function App() {
  const [terrain, setTerrain] = useState<TerrainProvider | undefined>();

  useEffect(() => {
    createWorldTerrainAsync().then(setTerrain);
  }, []);

  return (
    <Viewer
      full
      imageryProvider={bingLabels}
      terrainProvider={terrain}   // undefined until loaded
    >
      <GeoJsonDataSource data="/lines.geojson" clampToGround />
    </Viewer>
  );
}
