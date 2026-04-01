import React from "react";
import ReactDOM from "react-dom/client";
import App from "./app";
import { BrowserRouter } from "react-router-dom";

ReactDOM.createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);

// This file is the entry point that mounts the root React component (App) into the DOM and wraps it with BrowserRouter for routing support