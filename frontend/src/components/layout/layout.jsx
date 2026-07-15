import { Outlet } from "react-router-dom";
import { useState, useEffect } from "react";

import Header from "./header/header";
import Footer from "./footer/footer";
import Popup from "./popup/popup";

import "./layout.css";

export default function Layout() {
  const [popupOpen, setPopupOpen] = useState(false);

  useEffect(() => {
    if (!sessionStorage.getItem("onboarding_seen")) {
      setPopupOpen(true);
      sessionStorage.setItem("onboarding_seen", "true");
    }
  }, []);

  return (
    <div className="layout">
      <Header onAboutClick={() => setPopupOpen(true)} />
      <main className="layout-content">
        <Outlet />
      </main>
      {popupOpen && <Popup onClose={() => setPopupOpen(false)} />}
      <Footer />
    </div>
  );
}