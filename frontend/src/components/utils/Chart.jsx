import { VegaEmbed } from "react-vega";
import { useEffect, useRef, useState } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";

// mark is a string ("bar") for normal charts but an object ({type:"geoshape"}) for maps
function isGeoshape(spec) {
  const mark = spec?.mark;
  const type = typeof mark === "object" && mark !== null ? mark.type : mark;
  return type === "geoshape";
}

function Chart({ spec }) {
  const containerRef = useRef(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({ width: Math.floor(width), height: Math.floor(height) });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const map = isGeoshape(spec);

  const sizedSpec = {
    ...spec,
    width: size.width,
    height: size.height,
    autosize: { type: "fit", contains: "padding" },
  };

  const embed = (
    <VegaEmbed spec={sizedSpec} actions={false} renderer={map ? "svg" : "canvas"} />
  );

  return (
    <div ref={containerRef} style={{ width: "100%", height: "100%", overflow: "hidden" }}>
      {size.width > 0 && size.height > 0 &&
        (map ? (
          <TransformWrapper
            minScale={1}
            maxScale={8}
            doubleClick={{ mode: "reset" }}   // double-click to reset the view
            wheel={{ step: 0.15 }}
          >
            <TransformComponent
              wrapperStyle={{ width: "100%", height: "100%" }}
              contentStyle={{ width: "100%", height: "100%" }}
            >
              {embed}
            </TransformComponent>
          </TransformWrapper>
        ) : (
          embed
        ))}
    </div>
  );
}

export default function ChartCard({ chart, fallbackTitle }) {
  return (
    <div className="chart-card">
      <h2 className="chart-title">{chart?.title || fallbackTitle}</h2>
      <div className="chart">
        {chart ? (
          <Chart spec={chart.vega_lite} />
        ) : (
          <span className="chart-placeholder">{fallbackTitle} placeholder</span>
        )}
      </div>
      {chart?.summary && <p className="chart-description">{chart.summary}</p>}
    </div>
  );
}