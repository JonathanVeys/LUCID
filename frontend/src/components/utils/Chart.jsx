import { VegaEmbed } from "react-vega";
import { useEffect, useRef, useState } from "react";

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

  const sizedSpec = {
    ...spec,
    width: size.width,
    height: size.height,
    autosize: { type: "fit", contains: "padding" },
  };

  return (
    <div ref={containerRef} style={{ width: "100%", height: "100%"}}>
      {size.width > 0 && size.height > 0 && (
        <VegaEmbed spec={sizedSpec} actions={false} />
      )}
    </div>
  );
}


export default function ChartCard({ chart, fallbackTitle }) {
  return (
    <div className="chart-card">
      <h2 className="chart-title">{chart?.title || fallbackTitle}</h2>
      <div className="chart">
        {chart
          ? <Chart spec={chart.vega_lite} />
          : <span className="chart-placeholder">{fallbackTitle} placeholder</span>}
      </div>
      {chart?.summary && <p className="chart-description">{chart.summary}</p>}
    </div>
  );
}