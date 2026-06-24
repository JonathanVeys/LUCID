import { useLocation } from "react-router-dom";
import ChartCard from "../components/utils/Chart";
import "../styles/focused.css"

export default function Focused() {
  const location = useLocation();
  const visSpec = location.state?.vis_spec;
  const title = visSpec?.title || "Focused Dashboard";
  const description = visSpec?.description || "This is a description";
  const primaries = [];

  return (
    <div className="focused-div">
      <div className="metadata-div">
        <h1 className="title">{title}</h1>
        <p className="description"><b>Description:</b> {description}</p>
      </div>
      <div className="charts-div">
        <div className="primary-chart">
          <ChartCard chart={primaries[0]} fallbackTitle="Primary Chart One" />
        </div>
      </div>
    </div>
  )
}