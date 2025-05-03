import { Color } from "cesium";

/**
 * Map price (USD/MWh) ➜ Cesium Color.
 *  0–40  : green,   <= cheap
 * 40–60  : yellow
 * 60–80  : orange
 * 80+    : red,     <= expensive
 */
export function colorForPrice(p: number): Color {
  if (p < 40)  return Color.LIME.withAlpha(0.9);
  if (p < 60)  return Color.YELLOW.withAlpha(0.9);
  if (p < 80)  return Color.ORANGE.withAlpha(0.9);
  return Color.RED.withAlpha(0.9);
}
