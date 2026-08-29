import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "@/app/App";
import { initApiAuth } from "@/shared/services/api-auth";
import "@/styles/globals.css";

function renderApp(): void {
  ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}

void initApiAuth().finally(renderApp);
