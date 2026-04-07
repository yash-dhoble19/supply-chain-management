import { Suspense, lazy, useEffect, useState } from "react";
import type { AppPage } from "./types/app.types";
import { Login } from "./pages/Login";
import { DriverDashboard } from "./pages/DriverDashboard";
import { RetailerDashboard } from "./pages/RetailerDashboard";
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
const FinishedStocks = lazy(() =>
  import("./pages/FinishedStocks").then((module) => ({
    default: module.FinishedStocks,
  })),
);

const pathByPage: Record<AppPage, string> = {
  login: "/loginpage",
  dashboard: "/manufacturer-dashboard",
  driverDashboard: "/driver-dashboard",
  retailerDashboard: "/retailer-dashboard",
  inventory: "/inventory",
  logistics: "/logistics",
  procurement: "/procurement",
  purchaseOrders: "/purchase-orders",
  finishedStocks: "/finished-stocks",
};

function getPageFromPath(pathname: string): AppPage {
  switch (pathname) {
    case "/manufacturer-dashboard":
      return "dashboard";
    case "/driver-dashboard":
      return "driverDashboard";
    case "/retailer-dashboard":
      return "retailerDashboard";
    case "/loginpage":
      return "login";
    case "/inventory":
      return "inventory";
    case "/logistics":
      return "logistics";
    case "/purchase-orders":
      return "purchaseOrders";
    case "/finished-stocks":
      return "finishedStocks";
    case "/procurement":
      return "procurement";
    default:
      return "login";
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

const STORAGE_KEY = "chainmind-user";

function App() {
  const [activePage, setActivePage] = useState<AppPage>(() => getPageFromPath(window.location.pathname));
  const [authUser, setAuthUser] = useState<AuthUser | null>(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    try {
      return JSON.parse(stored) as AuthUser;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    const handlePopState = () => {
      const nextPage = getPageFromPath(window.location.pathname);

      if (nextPage === "login" && authUser) {
        setAuthUser(null);
        window.localStorage.removeItem(STORAGE_KEY);
        window.localStorage.removeItem("cm-access-token");
        setActivePage("login");
        return;
      }

      setActivePage(nextPage);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [authUser]);

  useEffect(() => {
    if (activePage === "login") {
      if (authUser) {
        setAuthUser(null);
        window.localStorage.removeItem(STORAGE_KEY);
        window.localStorage.removeItem("cm-access-token");
      }

      if (window.location.pathname !== pathByPage.login) {
        navigate("login");
      }
      return;
    }

    if (!authUser) {
      navigate("login");
      return;
    }

    if (authUser.role === "manufacturer") {
      if (activePage === "driverDashboard" || activePage === "retailerDashboard") {
        navigate("dashboard");
      }
      return;
    }

    if (authUser.role === "driver" && activePage !== "driverDashboard") {
      navigate("driverDashboard");
      return;
    }

    if (authUser.role === "retailer" && activePage !== "retailerDashboard") {
      navigate("retailerDashboard");
      return;
    }
  }, [activePage, authUser]);

  const navigate = (page: AppPage) => {
    const nextPath = pathByPage[page];
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, "", nextPath);
    }
    setActivePage(page);
  };

  const handleLogin = (user: AuthUser, token: string) => {
    setAuthUser(user);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    window.localStorage.setItem("cm-access-token", token);
    if (user.role === "manufacturer") {
      navigate("dashboard");
    } else if (user.role === "driver") {
      navigate("driverDashboard");
    } else {
      navigate("retailerDashboard");
    }
  };

  const handleLogout = () => {
    setAuthUser(null);
    window.localStorage.removeItem(STORAGE_KEY);
    window.localStorage.removeItem("cm-access-token");
    navigate("login");
  };

  return (
    <Suspense fallback={<AppShellFallback />}>
      {!authUser ? (
        <Login onLogin={handleLogin} />
      ) : authUser.role === "manufacturer" ? (
        <>
          {activePage === "dashboard" ? <Dashboard activePage={activePage} onNavigate={navigate} /> : null}
          {activePage === "inventory" ? <Inventory activePage={activePage} onNavigate={navigate} /> : null}
          {activePage === "logistics" ? <Logistics activePage={activePage} onNavigate={navigate} /> : null}
          {activePage === "purchaseOrders" ? (
            <PurchaseOrdersPage activePage={activePage} onNavigate={navigate} />
          ) : null}
          {activePage === "procurement" ? (
            <ProcurementIntelligence activePage={activePage} onNavigate={navigate} />
          ) : null}
          {activePage === "finishedStocks" ? (
            <FinishedStocks activePage={activePage} onNavigate={navigate} />
          ) : null}
        </>
      ) : authUser.role === "driver" ? (
        <DriverDashboard user={authUser} onLogout={handleLogout} />
      ) : (
        <RetailerDashboard user={authUser} onLogout={handleLogout} />
      )}
    </Suspense>
  );
}

export default App;
