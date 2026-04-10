import { useState, useEffect } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import type { AppPage } from "../types/app.types";
import type { CSSProperties, KeyboardEvent } from "react";
import { getLatestForecastSnapshot, subscribeToForecastUpdates } from "../services/forecastStore";
import ForecastOutput from "./ForecastOutput";
import type { ForecastSnapshot } from "../types/forecast.types";

const icons = {
  logo: (
    <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" width="18" height="18">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  ),
  barChart: (
    <svg viewBox="0 0 24 24" fill="none" width="32" height="32">
      <rect x="3" y="10" width="4" height="10" rx="1" fill="#3b82f6" opacity="0.6" />
      <rect x="10" y="6" width="4" height="14" rx="1" fill="#3b82f6" opacity="0.8" />
      <rect x="17" y="3" width="4" height="17" rx="1" fill="#3b82f6" />
      <circle cx="20" cy="2" r="2" fill="#60a5fa" />
    </svg>
  ),
  waveLine: (
    <svg viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2.5" width="18" height="18">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  ),
  grid: (
    <svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2" width="18" height="18">
      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
    </svg>
  ),
  star: (
    <svg viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2" width="18" height="18">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  ),
};

const features = [
  {
    icon: icons.waveLine,
    iconBg: "#dbeafe",
    borderColor: "#3b82f6",
    label: "Intelligent Forecasting",
    desc: "Turn historical data and current trends into accurate demand predictions using AI.",
  },
  {
    icon: icons.grid,
    iconBg: "#dcfce7",
    borderColor: "#22c55e",
    label: "Multi-Dimensional Insights",
    desc: "Analyze demand across products, locations, and time horizons for smarter planning.",
  },
  {
    icon: icons.star,
    iconBg: "#fef3c7",
    borderColor: "#f59e0b",
    label: "Scenario Simulation",
    desc: "Simulate pricing, promotions, and market changes to evaluate their impact on demand.",
  },
];

export function DemandForecasting({ activePage, onNavigate }: { activePage: AppPage, onNavigate: (page: AppPage) => void }) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [latestSnapshot, setLatestSnapshot] = useState<ForecastSnapshot | null>(getLatestForecastSnapshot());
  const [showLatest, setShowLatest] = useState(false);

  useEffect(() => {
    return subscribeToForecastUpdates(() => {
      setLatestSnapshot(getLatestForecastSnapshot());
    });
  }, []);

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
          title="📈 AI Demand Intelligence"
          onMenuClick={() => setSidebarOpen(true)}
          showSearch={false}
        />

        <div className="demand-content">
          {showLatest && latestSnapshot ? (
            <div className="forecast-analysis-view">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h2 style={{ fontSize: "1.5rem", color: "#1e293b" }}>Forecast Intelligence Report</h2>
                <button 
                  className="demand-cta" 
                  style={{ width: "fit-content", padding: "8px 16px", background: "white", color: "#3b82f6", border: "1px solid #d1d5db" }}
                  onClick={() => setShowLatest(false)}
                >
                  ← Back to Home
                </button>
              </div>
              <ForecastOutput 
                section={latestSnapshot.section}
                forecastLevel={latestSnapshot.forecastLevel}
                productCategoryOptions={latestSnapshot.productCategoryOptions}
                productOptions={latestSnapshot.productOptions}
                selectedCategory={latestSnapshot.selectedCategory}
                selectedProductKey={latestSnapshot.selectedProductKey}
                onCategoryChange={() => {}} 
                onProductChange={() => {}}
                locationFieldConfig={latestSnapshot.locationFieldConfig}
                locationOptionsByField={latestSnapshot.locationOptionsByField}
                locationSelections={latestSnapshot.locationSelections}
                onLocationChange={() => {}}
                insightHighlights={latestSnapshot.insightHighlights}
              />
            </div>
          ) : (
            <>
              <div className="demand-hero">
                <div className="demand-hero-icon">
                  <span className="demand-hero-icon-inner">{icons.barChart}</span>
                </div>
                <div>
                  <p className="demand-welcome">Welcome back, User 👋</p>
                  <h2>Start your first forecast</h2>
                  <p>Turn data into demand insights with intelligent forecasting.</p>
                </div>
              </div>

              <div style={{ display: "flex", gap: 12, marginBottom: 32 }}>
                <button
                  className="demand-cta"
                  type="button"
                  onClick={() => onNavigate("createForecast")}
                >
                  🚀 Create Demand Forecast
                </button>
                {latestSnapshot && (
                  <button
                    className="demand-cta"
                    style={{ background: "white", color: "#3b82f6", border: "1px solid #3b82f6" }}
                    onClick={() => setShowLatest(true)}
                  >
                    📊 View Latest Results
                  </button>
                )}
              </div>

              <div className="demand-feature-grid">
                {features.map((f) => (
                  <div key={f.label} className="demand-feature-card" style={{ borderTopColor: f.borderColor }}>
                    <div className="demand-feature-icon" style={{ background: f.iconBg }}>{f.icon}</div>
                    <div className="demand-feature-label">{f.label}</div>
                    <p className="demand-feature-desc">{f.desc}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default DemandForecasting;

// anything
