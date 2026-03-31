import { useEffect, useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { Inventory } from "./pages/Inventory";
import { Logistics } from "./pages/Logistics";
import { ProcurementIntelligence } from "./pages/ProcurementIntelligence";
import { PurchaseOrdersPage } from "./pages/PurchaseOrdersPage";
import type { AppPage } from "./types/app.types";

const pathByPage: Record<AppPage, string> = {
  dashboard: "/dashboard",
  inventory: "/inventory",
  logistics: "/logistics",
  procurement: "/procurement",
  purchaseOrders: "/purchase-orders",
};

function getPageFromPath(pathname: string): AppPage {
  switch (pathname) {
    case "/dashboard":
      return "dashboard";
    case "/inventory":
      return "inventory";
    case "/logistics":
      return "logistics";
    case "/purchase-orders":
      return "purchaseOrders";
    case "/":
    case "/procurement":
    default:
      return "procurement";
  }
}

function App() {
  const [activePage, setActivePage] = useState<AppPage>(() => getPageFromPath(window.location.pathname));

  useEffect(() => {
    const handlePopState = () => setActivePage(getPageFromPath(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = (page: AppPage) => {
    const nextPath = pathByPage[page];
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, "", nextPath);
    }
    setActivePage(page);
  };

  if (activePage === "dashboard") {
    return <Dashboard activePage={activePage} onNavigate={navigate} />;
  }

  if (activePage === "inventory") {
    return <Inventory activePage={activePage} onNavigate={navigate} />;
  }

  if (activePage === "logistics") {
    return <Logistics activePage={activePage} onNavigate={navigate} />;
  }

  if (activePage === "purchaseOrders") {
    return <PurchaseOrdersPage activePage={activePage} onNavigate={navigate} />;
  }

  return <ProcurementIntelligence activePage={activePage} onNavigate={navigate} />;
}

export default App;
