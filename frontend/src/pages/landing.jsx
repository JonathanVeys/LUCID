import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { sendQuery } from "../../services/api";
import Spinner from "../components/shared/spinner/spinner";

import "../styles/landing.css";

function Landing() {
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async () => {
        if (loading || !query.trim()) return;
        setLoading(true);
        try {
            const result = await sendQuery(query);
            const { vis_spec } = JSON.parse(result.response);   
            console.log(vis_spec);

            navigate("/focused", {
            state: {
                title: vis_spec.title,
                overview: vis_spec.overview,
                insights: vis_spec.insights,
                main: vis_spec.main,
                supporting: vis_spec.supporting,
            },
            });
        } catch (err) {
            console.error("Query failed:", err);
        } finally {
            setLoading(false);
            setQuery("");
        }
    };

    return (
        <div className="landing-page">
            <div className="prompt-container">
                <input 
                    type="text" 
                    className="prompt-input" 
                    placeholder={"What do you want to learn about your data?"} 
                    value = {query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                    disabled={loading}
                />
                <button className="btn-submit" onClick={handleSubmit} disabled={loading}>{loading ? <Spinner /> : "→"}</button>
            </div>
        </div>
    )
}

export default Landing