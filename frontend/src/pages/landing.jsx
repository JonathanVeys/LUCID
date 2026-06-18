import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { sendQuery } from "../../services/api";
import Spinner from "../components/shared/spinner/spinner";

import "../styles/landing.css";

function Landing() {
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const navigate = useNavigate();

    const ROUTES = {
        focused: "/focused",
        informative: "/informative",
    };

    const handleSubmit = async () => {
        if (loading || !query.trim()) return;
        setLoading(true);
        try {
            const response = await sendQuery(query);
            const spec = response.spec
            
            if (spec.answerable){
                const vis_spec = response.spec.vis_spec;
                const route = ROUTES[vis_spec.layout_mode];

                navigate(route, { state: { vis_spec } });
            } else{
                setError(spec.reason);
            }
        } catch (err) {
            console.error("Query failed:", err);
        } finally {
            setLoading(false);
            setQuery("");
        }
    };

    useEffect(() => {
        if (!error) return;                      // nothing to clear
        const id = setTimeout(() => setError(""), 10000);
        return () => clearTimeout(id);           // cancel if error changes or component unmounts
    }, [error]);

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
                <button className="prompt-submit" onClick={handleSubmit} disabled={loading}>{loading ? <Spinner /> : "→"}</button>
            </div>
            <div className="error-container">
                {error}
            </div>
        </div>
    )
}

export default Landing