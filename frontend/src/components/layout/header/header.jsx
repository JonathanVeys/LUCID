import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import "./header.css"

export default function Header({ onAboutClick }) {
    const navigate = useNavigate();

    return (
        <div className="header-div">
            <Link to="/" className="btn">Home</Link>
            <a className="btn github" href="https://github.com/JonathanVeys/LUCID" target="_blank" rel="noopener noreferrer">
                GitHub
            </a>
            <button onClick={onAboutClick} className="btn">About</button>
            <Link to="/informative" className="btn">Informative</Link>
            <Link to="/focused" className="btn">Focused</Link>
            <Link to="/scalar" className="btn">Scalar</Link>
        </div>
    )
}