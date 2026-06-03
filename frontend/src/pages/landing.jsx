import {useState} from "react";
import { sendQuery } from "../../services/api";
import "../styles/landing.css";

function Landing() {
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async() => {
        setLoading(true);
        const result = await sendQuery(query);
        console.log(result);
        setLoading(false);
    }

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
                />
                <button className="btn-submit" onClick={handleSubmit}>→</button>
            </div>
        </div>
    )
}

export default Landing