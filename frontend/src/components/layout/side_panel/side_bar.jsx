import { useEffect, useRef } from "react";
import "./side_bar.css";

export default function SideBar({ elementData, onClose }) {
  const urls = elementData?.urls ?? [];
  const panelRef = useRef(null);
  const listItems = urls.map((url) =>
    <li>
      <a href={url} className="url" target="_blank">{url}</a>
    </li>
  );

  useEffect(() => {
    if (!elementData) return;

    const handleClick = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        onClose();
      }
    };

    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [elementData, onClose]);

  return (
    <div ref={panelRef} className={`side-bar ${elementData && elementData.label ? "open" : ""}`}>
      {elementData && <h1>{elementData.label}</h1>}
      <ul>
        {listItems}
      </ul>
    </div>
  );
}