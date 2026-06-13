import { BrowserRouter, Routes, Route } from "react-router-dom";

import Landing from "./pages/landing";
import Informative from "./pages/informative";
import Focused from "./pages/focused";
import Layout from "./components/layout/layout";

import "./styles/global.css";

export default function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/informative" element={<Informative />} />
          <Route path="/focused" element={<Focused />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

