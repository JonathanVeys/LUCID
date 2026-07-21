import { useLocation } from "react-router-dom";
import { useState } from "react";
import ChartCard from "../components/utils/Chart";
import SideBar from "../components/layout/side_panel/side_bar";
import "../styles/scalar.css"


export default function Scalar() {
    const location = useLocation();
    const visSpec = location.state?.vis_spec;
    console.log(visSpec)
    const title = visSpec?.title || "Scalar Dashboard";
    const value = visSpec?.value || "Scalar Value";
    const unit = visSpec?.unit || "units";
    const qualifier = visSpec?.qualifier || "qualifier";
    const urls = visSpec?.urls || [];

    const [ elementData, setElementData ] = useState(null)

    return (
        <div className="scalar-div">
            <div className="metadata-div">
                <h1 className="title">{title}</h1>
                <hr className="rule" />
            </div>

            <div className="data-div">
                <div className="scalar-card">
                    <div className="value-row">
                        <span className="scalar-value">{value}</span>
                        <span className="scalar-unit"> {unit}</span>
                    </div>
                    <p className="qualifier">{qualifier}</p>
                    <btn className="btn urls" onClick={() => setElementData({ label: title,urls: urls ?? [], })}>
                        View {urls.length} source articles
                    </btn>
                </div>
            </div>
            <SideBar elementData={elementData} onClose={() => setElementData(null)}/>
        </div>
    )
}