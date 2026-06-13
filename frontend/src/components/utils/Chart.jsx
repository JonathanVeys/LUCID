import { VegaEmbed } from "react-vega";

export default function Chart({ spec, width, height }) {
  const sizedSpec = { ...spec, width, height, background: "transparent" };
  return (
    <VegaEmbed spec={sizedSpec} options={{ actions: false }}
      onError={(e) => console.error("Vega error:", e)} />
  );
}