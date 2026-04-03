import { Suspense, lazy, useEffect, useState } from "react";
import type { AppPage } from "./types/app.types";

const Dashboard = lazy(() =>
  import("./pages/Dashboard").then((module) => ({
    default: module.Dashboard,
  })),
);
const Inventory = lazy(() =>
  import("./pages/Inventory").then((module) => ({
    default: module.Inventory,
  })),
);
const Logistics = lazy(() =>
  import("./pages/Logistics").then((module) => ({
    default: module.Logistics,
  })),
);
const ProcurementIntelligence = lazy(() =>
  import("./pages/ProcurementIntelligence").then((module) => ({
    default: module.ProcurementIntelligence,
  })),
);
const PurchaseOrdersPage = lazy(() =>
  import("./pages/PurchaseOrdersPage").then((module) => ({
    default: module.PurchaseOrdersPage,
  })),
);
const DemandForecasting = lazy(() =>
  import("./pages/DemandForecasting").then((module) => ({
    default: module.DemandForecasting,
  })),
);

const pathByPage: Record<AppPage, string> = {
  dashboard: "/dashboard",
  inventory: "/inventory",
  logistics: "/logistics",
  procurement: "/procurement",
  purchaseOrders: "/purchase-orders",
  demandForecasting: "/demand-forecasting",
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
    case "/demand-forecasting":
      return "demandForecasting";
    case "/":
    case "/procurement":
    default:
      return "procurement";
  }
}

function AppShellFallback() {
  return (
    <div className="min-h-screen bg-background px-4 py-8 text-on-surface sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="h-10 w-64 animate-pulse rounded-xl bg-surface-container-high" />
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="h-64 animate-pulse rounded-3xl bg-surface-container-high" />
          <div className="h-64 animate-pulse rounded-3xl bg-surface-container-high" />
        </div>
        <div className="h-80 animate-pulse rounded-3xl bg-surface-container-high" />
      </div>
    </div>
  );
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

  return (
    <Suspense fallback={<AppShellFallback />}>
      {activePage === "dashboard" ? <Dashboard activePage={activePage} onNavigate={navigate} /> : null}
      {activePage === "inventory" ? <Inventory activePage={activePage} onNavigate={navigate} /> : null}
      {activePage === "logistics" ? <Logistics activePage={activePage} onNavigate={navigate} /> : null}
      {activePage === "purchaseOrders" ? (
        <PurchaseOrdersPage activePage={activePage} onNavigate={navigate} />
      ) : null}
      {activePage === "demandForecasting" ? (
        <DemandForecasting activePage={activePage} onNavigate={navigate} />
      ) : null}
      {activePage === "procurement" ? (
        <ProcurementIntelligence activePage={activePage} onNavigate={navigate} />
      ) : null}
    </Suspense>
  );
}

export default App;
