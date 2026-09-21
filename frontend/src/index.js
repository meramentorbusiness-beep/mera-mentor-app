import React from "react";
import ReactDOM from "react-dom/client";
import DataAnalyticsLandingPage from "@/landing/DataAnalyticsLandingPage";

const root = ReactDOM.createRoot(document.getElementById("root"));
// Keep the dashboard, charts, router and its styles out of the public landing bundle.
if (window.location.pathname.replace(/\/$/, '') === '/courses/data-analytics') {
  root.render(<DataAnalyticsLandingPage />);
} else {
  import('@/App').then(({ default: App }) => root.render(<React.StrictMode><App /></React.StrictMode>));
}
