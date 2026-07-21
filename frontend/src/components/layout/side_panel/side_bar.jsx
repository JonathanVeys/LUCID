import "./side_bar.css";

export default function SideBar({ elementData }) {
  const urls = elementData?.urls ?? [];
  const listItems = urls.map((url) =>
    <li>
      <a href={url} className="url" target="_blank">{url}</a>
    </li>
  );

  return (
    <div className={`side-bar ${elementData && elementData.label ? "open" : ""}`}>
      {elementData && <h1>{elementData.label}</h1>}
      <ul>
        {listItems}
      </ul>
    </div>
  );
}