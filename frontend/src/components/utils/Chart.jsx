import vegaEmbed from "vega-embed";
import { useEffect, useRef, useState } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";

function isGeoshape(spec) {
  const mark = spec?.mark;
  const type = typeof mark === "object" && mark !== null ? mark.type : mark;
  return type === "geoshape";
}

function Chart({ spec, onSelect }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    let timeout;
    const observer = new ResizeObserver(([entry]) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        const { width, height } = entry.contentRect;
        setSize({ width: Math.floor(width), height: Math.floor(height) });
      }, 150);   // wait 150ms after resizing stops
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const map = isGeoshape(spec);

  // Embed whenever the spec or size changes.
  useEffect(() => {
    if (!chartRef.current || size.width === 0 || size.height === 0) return;

    const sizedSpec = {
      ...spec,
      width: size.width,
      height: size.height,
      autosize: { type: "fit", contains: "padding" },
    };

    let view;
    vegaEmbed(chartRef.current, sizedSpec, {
      actions: false,
      renderer: map ? "svg" : "canvas",
    })
      .then((result) => {
        view = result.view;
        view.addSignalListener("select", (name, value) => {
          const ids = value?._vgsid_;
          if (!ids || ids.size === 0) {
            onSelect?.(null);   
            return;
          }

          const datasetNames = ["source_0", "data_0", "marks"];  // try common names
          let selected;
          for (const dsName of datasetNames) {
            try {
              const ds = view.data(dsName);
              if (ds && ds.length) {
                const match = ds.find((d) => ids.has(d._vgsid_));
                if (match) { selected = match; break; }
              }
            } catch {}
          }
          
          // const allData = view.data("source_0");  
          // const selected = allData.find((d) => ids.has(d._vgsid_));
          onSelect?.(selected ?? null);
        });
      })
      .catch((err) => console.error("vegaEmbed error:", err));

    return () => {
      if (view) view.finalize();
    };
  }, [spec, size.width, size.height, map, onSelect]);

  return (
    <div ref={containerRef} style={{ width: "100%", height: "100%", overflow: "hidden" }}>
      {size.width > 0 && size.height > 0 &&
        (map ? (
          <TransformWrapper
            minScale={1}
            maxScale={8}
            doubleClick={{ mode: "reset" }}
            wheel={{ step: 0.15 }}
          >
            <TransformComponent
              wrapperStyle={{ width: "100%", height: "100%" }}
              contentStyle={{ width: "100%", height: "100%" }}
            >
              <div ref={chartRef} style={{ width: "100%", height: "100%" }} />
            </TransformComponent>
          </TransformWrapper>
        ) : (
          <div ref={chartRef} style={{ width: "100%", height: "100%" }} />
        ))}
    </div>
  );
}

export default function ChartCard({ chart, fallbackTitle, onSelect }) {
  return (
    <div className="chart-card">
      <h2 className="chart-title">{chart?.title || fallbackTitle}</h2>
      <div className="chart">
        {chart ? (
          <Chart spec={chart.vega_lite}  onSelect={onSelect}/>
        ) : (
          <span className="chart-placeholder">{fallbackTitle} placeholder</span>
        )}
      </div>
      {chart?.summary && <p className="chart-description">{chart.summary}</p>}
    </div>
  );
}