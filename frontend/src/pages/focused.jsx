import { useLocation } from "react-router-dom";
import Chart from "../components/utils/Chart";
import "../styles/focused.css";

export default function Focused() {
  const { state } = useLocation();

  const title = state?.title ?? "Focused View";
  const overview = state?.overview ?? null;
  const insights = state?.insights ?? [];          // array of short strings
  const main = state?.main ?? null;                // { title, caption, spec }
  const supporting = state?.supporting ?? null;    // { title, caption, spec }

  console.log(main);

  return (
    <div className="focused-page">
      <header className="focused-header">
        <h1>{title}</h1>
        {overview
          ? <p className="overview">{overview}</p>
          : <p className="placeholder">Overview will appear here.</p>}
      </header>

      <div className="focused-body">
        <section className="main-panel">
          <h2>{main?.title ?? "Main chart"}</h2>
          {main?.spec
            ? <Chart spec={main.spec} width={700} height={420} />
            : <p className="placeholder">Main chart placeholder</p>}
          {main?.caption && <p className="caption">{main.caption}</p>}
        </section>

        <aside className="side-panel">
          <section className="supporting">
            <h3>{supporting?.title ?? "Supporting chart"}</h3>
            {supporting?.spec
              ? <Chart spec={supporting.spec} width={340} height={260} />
              : <p className="placeholder">Supporting chart placeholder</p>}
            {supporting?.caption && <p className="caption">{supporting.caption}</p>}
          </section>

          <section className="insights">
            <h3>Key insights</h3>
            {insights.length > 0
              ? <ul>{insights.map((point, i) => <li key={i}>{point}</li>)}</ul>
              : <p className="placeholder">Insights will appear here.</p>}
          </section>
        </aside>
      </div>
    </div>
  );
}