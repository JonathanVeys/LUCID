import Markdown from 'react-markdown';
import md from "../../../../README.md?raw";
import "./popup.css";


export default function Popup({ onClose }) {
  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-content" onClick={(e) => e.stopPropagation()}>
        <button className="popup-close" onClick={onClose}>×</button>
        <Markdown>{md}</Markdown>
      </div>
    </div>
  );
}