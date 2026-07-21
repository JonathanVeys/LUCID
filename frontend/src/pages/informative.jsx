import { useLocation } from "react-router-dom";
import { useState } from "react";
import ChartCard from "../components/utils/Chart";
import SideBar from "../components/layout/side_panel/side_bar";
import "../styles/informative.css";


export default function Informative() {
  const location = useLocation();
  const visSpec = location.state?.vis_spec;
  const title = visSpec?.title || "Informative Dashboard";
  const description = visSpec?.description || "This is a description";
  const rationale = visSpec?.layout_rationale || "This is the model's rationale";
  const charts = visSpec?.charts ?? [];
  const primaries = charts.filter((c) => c.role === "primary");
  const supportives = charts.filter((c) => c.role === "supporting");

  const [ elementData, setElementData ] = useState(null)

  return (
    <div className="informative-div">
      <div className="metadata-div">
        <h1 className="title">{title}</h1>
        <hr className="rule"></hr>
        <p className="description"><b>Description:</b> {description}</p>
        <p className="description"><b>Model Rationale:</b> {rationale} </p>
      </div>

      <div className="charts-div">
        <div className="primary-charts-div">
          <ChartCard chart={primaries[0]} fallbackTitle="Primary Chart One" onSelect={setElementData}/>
        </div>
        <div className="supportive-charts-div">
          <ChartCard chart={supportives[0]} fallbackTitle="Supporting Chart One" onSelect={setElementData}/>
          <ChartCard chart={supportives[1]} fallbackTitle="Supporting Chart Two" onSelect={setElementData}/>
        </div>
      </div>
      <SideBar elementData={elementData} onClose={() => setElementData(null)}/>
      {console.log(elementData)}
    </div>
  );
}