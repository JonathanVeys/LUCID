import "./side_bar.css";

export default function SideBar({ elementData }) {
  return (
    <div className={`side-bar ${elementData && elementData.label ? "open" : ""}`}>
      {elementData && <h1>{elementData.label}</h1>}
    </div>
  );
}