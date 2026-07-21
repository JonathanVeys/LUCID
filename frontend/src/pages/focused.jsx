import { useLocation } from "react-router-dom";
import { useState } from "react";
import ChartCard from "../components/utils/Chart";
import SideBar from "../components/layout/side_panel/side_bar";
import "../styles/focused.css"


export default function Focused() {
  const location = useLocation();
  const visSpec = location.state?.vis_spec;
  const title = visSpec?.title || "Focused Dashboard";
  const description = visSpec?.description || "This is a description";
  const rationale = visSpec?.layout_rationale || "This is the model's rationale";
  const charts = visSpec?.charts ?? [];
  const primaries = charts.filter((c) => c.role === "primary");

  const [ elementData, setElementData ] = useState(null)

  return (
    <div className="focused-div">
      <div className="dashboard-div">
        <div className="metadata-div">
          <h1 className="title">{title}</h1>
          <p className="description"><b>Description:</b> {description} </p>
          <p className="description"><b>Model Rationale:</b> {rationale} </p>
        </div>
        <div className="charts-div">
          <div className="primary-chart">
            <ChartCard chart={primaries[0]} fallbackTitle="Primary Chart One" onSelect={setElementData} />
          </div>
        </div>
      </div>
      {console.log(elementData)}
      <SideBar elementData={elementData}/>
      {console.log(elementData)}
    </div>
  )
}