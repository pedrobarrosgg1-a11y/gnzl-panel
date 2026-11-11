import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "@fontsource/syne/latin-500.css";
import "@fontsource/syne/latin-800.css";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-500.css";

import "./styles/tokens.css";
import "./styles/global.css";

import App from "./App";

const container = document.getElementById("root");

if (!container) {
  throw new Error("Elemento #root não encontrado no index.html.");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
