import { Outlet } from "react-router-dom";

import Header from "./header/header";
import Footer from "./footer/footer";

import "./layout.css";

export default function Layout() {
  return (
    <div className="layout">
      <Header />
      <main className="layout-content">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}