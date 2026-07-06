import { Link, useNavigate } from "react-router-dom";
import "./header.css"

export default function Header() {
    const navigate = useNavigate();

    return (
        <div className="header-div">
            <Link to="/" className="btn">Home</Link>
            <a className="btn github" href="https://github.com/JonathanVeys/LUCID" target="_blank" rel="noopener noreferrer">
                GitHub
            </a>
            <Link to="/about" className="btn">About</Link>
            <Link to="/informative" className="btn">Informative</Link>
            <Link to="/focused" className="btn">Focused</Link>
        </div>
    )
}