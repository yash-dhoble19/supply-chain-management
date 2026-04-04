import { useState } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import type { AppPage } from "../types/app.types";

interface CreateForecastProps {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

export function CreateForecast({ activePage, onNavigate }: CreateForecastProps) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const lastUpdated = new Date();

  return (
    <div className="demand-page">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activePage={activePage}
        onNavigate={onNavigate}
      />

      <main className="demand-main">
        <Header
          title="AI Demand Intelligence"
          lastUpdated={lastUpdated}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onRefresh={() => setSidebarOpen((prev) => prev)}
          onMenuClick={() => setSidebarOpen(true)}
          showHelp
          showSearch={false}
        />

        <div className="demand-content">
          <div className="demand-hero">
            <div className="demand-hero-icon">
              <span className="demand-hero-icon-inner">{null}</span>
            </div>
            <div>
              <h2>AI Demand Intelligence</h2>
              <p>Last updated: Just now</p>
              <div style={{ marginTop: 12, display: "flex", gap: 16 }}>
                <span className="material-symbols-outlined">refresh</span>
                <span className="material-symbols-outlined">notifications</span>
                <span className="material-symbols-outlined">help_outline</span>
              </div>
            </div>
          </div>

          <div className="demand-feature-grid" style={{ marginTop: 0 }}>
            <div className="demand-feature-card" style={{ borderTopColor: "#3b82f6" }}>
              <div className="demand-feature-icon" style={{ background: "#dbeafe" }}>
                {null}
              </div>
              <div className="demand-feature-label">Coming Soon</div>
              <p className="demand-feature-desc">The forecast creation workspace will appear here.</p>
            </div>
            <div className="demand-feature-card" style={{ borderTopColor: "#22c55e" }}>
              <div className="demand-feature-icon" style={{ background: "#dcfce7" }}>
                {null}
              </div>
              <div className="demand-feature-label">Stay Tuned</div>
              <p className="demand-feature-desc">We'll add a guided experience shortly.</p>
            </div>
            <div className="demand-feature-card" style={{ borderTopColor: "#f59e0b" }}>
              <div className="demand-feature-icon" style={{ background: "#fef3c7" }}>
                {null}
              </div>
              <div className="demand-feature-label">Refresh</div>
              <p className="demand-feature-desc">Use the controls above to refresh or open help.</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default CreateForecast;
