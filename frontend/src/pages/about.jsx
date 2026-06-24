import Markdown from 'react-markdown';
import md from "../../README.md?raw";
import "../styles/about.css";


export default function About() {
    return (
        <div className="about-div">
            <Markdown>{md}</Markdown>
        </div>
    )
}