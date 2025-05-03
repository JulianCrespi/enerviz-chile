import React from "react";
import ReactDOM from "react-dom/client";

import "cesium/Build/Cesium/Widgets/widgets.css";
import { Ion, buildModuleUrl } from "cesium";

Ion.defaultAccessToken = import.meta.env.VITE_CESIUM_ION_TOKEN;

// <-- ADD THIS LINE
buildModuleUrl.setBaseUrl("/cesium/");

import App from "./App.tsx";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
