import { Link, useNavigate } from "react-router-dom";
import "./header.css"

export default function Header() {
    const navigate = useNavigate();

    return (
        <div className="header-div">
            <button className="btn home" onClick={() => navigate("/")}>
                Home
            </button>
            <a className="btn github" href="https://github.com/JonathanVeys/LUCID" target="_blank" rel="noopener noreferrer">
                GitHub
            </a>

            <Link to="/about">About</Link>
            <Link to="/informative">Informative</Link>
            <Link to="/focused">Focused</Link>
        </div>
    )
}