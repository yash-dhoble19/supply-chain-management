import { useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { ProcurementIntelligence } from "./pages/ProcurementIntelligence";
import { PurchaseOrdersPage } from "./pages/PurchaseOrdersPage";
import type { AppPage } from "./types/app.types";

function App() {
  const [activePage, setActivePage] = useState<AppPage>("procurement");

  if (activePage === "dashboard") {
    return <Dashboard activePage={activePage} onNavigate={setActivePage} />;
  }

  if (activePage === "purchaseOrders") {
    return <PurchaseOrdersPage activePage={activePage} onNavigate={setActivePage} />;
  }

  return <ProcurementIntelligence activePage={activePage} onNavigate={setActivePage} />;
}

export default App;
