import { Suspense, lazy, useEffect, useState } from "react";
import type { AppPage } from "./types/app.types";
import type { AuthUser } from "./services/authService";

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
const CreateForecast = lazy(() =>
  import("./pages/CreateForecast").then((module) => ({
    default: module.CreateForecast,
  })),
);
const DemandForecasting = lazy(() =>
  import("./pages/DemandForecasting").then((module) => ({
    default: module.DemandForecasting,
  })),
);
const AiTools = lazy(() =>
  import("./pages/AiTools").then((module) => ({
    default: module.AiTools,
  })),
);
const Login = lazy(() =>
  import("./pages/Login").then((module) => ({
    default: module.Login,
  })),
);
const DriverDashboard = lazy(() =>
  import("./pages/DriverDashboard").then((module) => ({
    default: module.DriverDashboard,
  })),
);
const RetailerDashboard = lazy(() =>
  import("./pages/RetailerDashboard").then((module) => ({
    default: module.RetailerDashboard,
  })),
);
const FinishedStocks = lazy(() =>
  import("./pages/FinishedStocks").then((module) => ({
    default: module.FinishedStocks,
  })),
);

const pathByPage: Record<AppPage, string> = {
  dashboard: "/dashboard",
  inventory: "/inventory",
  logistics: "/logistics",
  procurement: "/procurement",
  purchaseOrders: "/purchase-orders",
  demandForecasting: "/demand-forecasting",
  createForecast: "/create-forecast",
  aiTools: "/ai-tools",
  login: "/loginpage",
  driverDashboard: "/driver-dashboard",
  retailerDashboard: "/retailer-dashboard",
  finishedStocks: "/finished-stocks",
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
    case "/create-forecast":
      return "createForecast";
    case "/ai-tools":
      return "aiTools";
    case "/loginpage":
      return "login";
    case "/driver-dashboard":
      return "driverDashboard";
    case "/retailer-dashboard":
      return "retailerDashboard";
    case "/finished-stocks":
      return "finishedStocks";
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
  const [user, setUser] = useState<AuthUser | null>(() => {
    const saved = localStorage.getItem("scm-user");
    return saved ? JSON.parse(saved) : null;
  });

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

  const handleLogin = (newUser: AuthUser, token: string) => {
    setUser(newUser);
    localStorage.setItem("scm-token", token);
    localStorage.setItem("scm-user", JSON.stringify(newUser));
    // Redirect based on role
    if (newUser.role === "driver") {
      navigate("driverDashboard");
    } else if (newUser.role === "retailer") {
      navigate("retailerDashboard");
    } else {
      navigate("dashboard");
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("scm-token");
    localStorage.removeItem("scm-user");
    navigate("login");
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
      {activePage === "createForecast" ? (
        <CreateForecast activePage={activePage} onNavigate={navigate} />
      ) : null}
      {activePage === "procurement" ? (
        <ProcurementIntelligence activePage={activePage} onNavigate={navigate} />
      ) : null}
      {activePage === "aiTools" ? <AiTools activePage={activePage} onNavigate={navigate} /> : null}
      
      {activePage === "login" ? <Login onLogin={handleLogin} /> : null}
      
      {activePage === "driverDashboard" ? (
        user ? <DriverDashboard user={user} onLogout={handleLogout} /> : <Login onLogin={handleLogin} />
      ) : null}
      
      {activePage === "retailerDashboard" ? (
        user ? <RetailerDashboard user={user} onLogout={handleLogout} /> : <Login onLogin={handleLogin} />
      ) : null}

      {activePage === "finishedStocks" ? <FinishedStocks activePage={activePage} onNavigate={navigate} /> : null}
    </Suspense>
  );
}

export default App;

// anything
