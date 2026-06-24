import { useLocation } from "react-router-dom";
import ChartCard from "../components/utils/Chart";
import "../styles/informative.css";

// function ChartCard({ chart, fallbackTitle }) {
//   return (
//     <div className="chart-card">
//       <h2 className="chart-title">{chart?.title || fallbackTitle}</h2>
//       <div className="chart">
//         {chart
//           ? <Chart spec={chart.vega_lite} />
//           : <span className="chart-placeholder">{fallbackTitle} placeholder</span>}
//       </div>
//       {chart?.summary && <p className="chart-description">{chart.summary}</p>}
//     </div>
//   );
// }

export default function Informative() {
  const location = useLocation();
  const visSpec = location.state?.vis_spec;
  const title = visSpec?.title || "Informative Dashboard";
  const description = visSpec?.description || "This is a description";
  const charts = visSpec?.charts ?? [];
  const primaries = charts.filter((c) => c.role === "primary");
  const supportives = charts.filter((c) => c.role === "supporting");

  return (
    <div className="informative-div">
      <div className="metadata-div">
        <h1 className="title">{title}</h1>
        <p className="description"><b>Description:</b> {description}</p>
      </div>

      <div className="charts-div">
        <div className="primary-charts-div">
          <ChartCard chart={primaries[0]} fallbackTitle="Primary Chart One" />
          <ChartCard chart={primaries[1]} fallbackTitle="Primary Chart Two" />
        </div>
        <div className="supportive-charts-div">
          <ChartCard chart={supportives[0]} fallbackTitle="Supporting Chart One" />
          <ChartCard chart={supportives[1]} fallbackTitle="Supporting Chart Two" />
          <ChartCard chart={supportives[2]} fallbackTitle="Supporting Chart Three" />
        </div>
      </div>
    </div>
  );
}