import { useState } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import type { AppPage } from "../types/app.types";
import type { KeyboardEvent } from "react";

const icons = {
  logo: (
    <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" width="18" height="18">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  ),
  dashboard: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
    </svg>
  ),
  inventory: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <path d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2z" />
      <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
    </svg>
  ),
  shipments: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <rect x="1" y="3" width="15" height="13" rx="1" />
      <path d="M16 8h4l3 3v5h-7V8z" />
      <circle cx="5.5" cy="18.5" r="2.5" /><circle cx="18.5" cy="18.5" r="2.5" />
    </svg>
  ),
  forecast: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  ),
  suppliers: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
    </svg>
  ),
  analytics: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  ),
  bell: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0" />
    </svg>
  ),
  help: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01" />
    </svg>
  ),
  play: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="16" height="16">
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  ),
  download: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="13" height="13">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
    </svg>
  ),
  table: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="13" height="13">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
      <line x1="3" y1="9" x2="21" y2="9" />
      <line x1="9" y1="21" x2="9" y2="9" />
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
    <svg viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2" width="18" height="18">
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

interface DemandForecastingProps {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

export function DemandForecasting({ activePage, onNavigate }: DemandForecastingProps) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [intelModalOpen, setIntelModalOpen] = useState(false);
  const [multiDimModalOpen, setMultiDimModalOpen] = useState(false);
  const [scenarioModalOpen, setScenarioModalOpen] = useState(false);

  const openFeatureModal = (label: string) => {
    if (label === "Intelligent Forecasting") {
      setIntelModalOpen(true);
      return;
    }
    if (label === "Multi-Dimensional Insights") {
      setMultiDimModalOpen(true);
      return;
    }
    if (label === "Scenario Simulation") {
      setScenarioModalOpen(true);
    }
  };

  const handleFeatureKeyDown =
    (label: string) => (event: KeyboardEvent<HTMLDivElement>) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openFeatureModal(label);
      }
    };

  const isInteractiveFeature = (label: string) =>
    label === "Intelligent Forecasting" ||
    label === "Multi-Dimensional Insights" ||
    label === "Scenario Simulation";

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
          title="📈 AI Demand Intelligence"
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
              <span className="demand-hero-icon-inner">{icons.barChart}</span>
            </div>
            <div>
              <p className="demand-welcome">Welcome back, Marcus 👋</p>
              <h2>Start your first forecast</h2>
              <p>Turn data into demand insights with intelligent forecasting.</p>
              <p className="demand-steps-title">Get started in 3 simple steps:</p>
              <ol className="demand-steps">
                <li>1. Upload historical data</li>
                <li>2. Select products &amp; timeframe</li>
                <li>3. Generate forecast</li>
              </ol>
            </div>
          </div>

          <button
            className="demand-cta"
            type="button"
            onClick={() => onNavigate("createForecast")}
          >
            🚀 Create Demand Forecast
          </button>

          <div className="demand-feature-grid">
            {features.map((f) => {
              const interactive = isInteractiveFeature(f.label);
              return (
                <div
                  key={f.label}
                  className="demand-feature-card"
                  style={{ borderTopColor: f.borderColor }}
                  role={interactive ? "button" : undefined}
                  tabIndex={interactive ? 0 : undefined}
                  onClick={interactive ? () => openFeatureModal(f.label) : undefined}
                  onKeyDown={interactive ? handleFeatureKeyDown(f.label) : undefined}
                >
                  <div className="demand-feature-icon" style={{ background: f.iconBg }}>
                    {f.icon}
                  </div>
                  <div className="demand-feature-label">{f.label}</div>
                  <p className="demand-feature-desc">{f.desc}</p>
                </div>
              );
            })}
          </div>

          <div className="demand-conclusion">
            <p className="demand-conclusion-body">
              -: Predict Smarter, Stock Better, Decide Faster — ChainMind keeps insights transparent, demand-ready, and ready for action :-
            </p>
          </div>
          {intelModalOpen && (
            <div className="demand-modal-backdrop" onClick={() => setIntelModalOpen(false)}>
              <div className="demand-modal" onClick={(event) => event.stopPropagation()}>
                <button
                  type="button"
                  className="demand-modal-close"
                  aria-label="Close details"
                  onClick={() => setIntelModalOpen(false)}
                >
                  ×
                </button>
                <h3><strong>Intelligent Data-Driven Forecasting</strong></h3>
                <p className="demand-modal-description">
                  We analyze sales trends, seasonality, and external factors like weather and events to generate reliable forecasts.
                </p>
                <div className="demand-modal-flow demand-modal-flow-steps">
                  <span>Raw Data</span>
                  <span className="demand-modal-flow-arrow">↓</span>
                  <span>Data Cleaning</span>
                  <span className="demand-modal-flow-arrow">↓</span>
                  <span>Feature Extraction</span>
                  <span className="demand-modal-flow-arrow">↓</span>
                  <span>Data Segmentation</span>
                  <span className="demand-modal-flow-arrow">↓</span>
                  <span>ML Models</span>
                  <span className="demand-modal-flow-arrow">↓</span>
                  <span>Forecast Generation</span>
                </div>
                <div className="demand-modal-capabilities">
                  <div className="demand-modal-cap-heading">Key Capabilities:</div>
                  <ul>
                    <li>✔ AI models (Random Forest, Gradient Boosting)</li>
                    <li>✔ Baseline comparison (Moving Average)</li>
                    <li>✔ Smart segmentation (seasonal, stable, irregular demand)</li>
                    <li>✔ Continuous learning and model improvement</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
          {multiDimModalOpen && (
            <div className="demand-modal-backdrop" onClick={() => setMultiDimModalOpen(false)}>
              <div className="demand-modal" onClick={(event) => event.stopPropagation()}>
                <button
                  type="button"
                  className="demand-modal-close"
                  aria-label="Close details"
                  onClick={() => setMultiDimModalOpen(false)}
                >
                  ×
                </button>
                <h3><strong>Make better decisions by analyzing patterns across products, locations, and time.</strong></h3>
                <p className="demand-modal-description">
                  Use these insights to optimize inventory, improve logistics planning, and make data-driven business decisions.
                </p>
                <div className="demand-modal-flow">
                  <span>Product → What will sell</span>
                  <span>Location → Where it will sell</span>
                  <span>Time → When demand will rise</span>
                  <span>Season → Why demand changes</span>
                </div>
                <div className="demand-modal-capabilities">
                  <div className="demand-modal-cap-heading">Key Capabilities:</div>
                  <ul>
                    <li>✔ Product-level forecasts</li>
                    <li>✔ Location insights (city, warehouse, region)</li>
                    <li>✔ Flexible time horizons (7, 30, 90 days)</li>
                    <li>✔ Seasonal trend analysis</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
          {scenarioModalOpen && (
            <div className="demand-modal-backdrop" onClick={() => setScenarioModalOpen(false)}>
              <div className="demand-modal" onClick={(event) => event.stopPropagation()}>
                <button
                  type="button"
                  className="demand-modal-close"
                  aria-label="Close details"
                  onClick={() => setScenarioModalOpen(false)}
                >
                  ×
                </button>
                <h3><strong>Test business decisions before applying them in the real world.</strong></h3>
                <div className="demand-modal-flow demand-modal-flow-steps">
                  <span>Modify Inputs</span>
                  <span className="demand-modal-flow-arrow">↓</span>
                  <span>Recalculate Demand</span>
                  <span className="demand-modal-flow-arrow">↓</span>
                  <span>Compare Results</span>
                </div>
                <div className="demand-modal-capabilities">
                  <div className="demand-modal-cap-heading">What you can simulate:</div>
                  <ul>
                    <li>✔ Price changes</li>
                    <li>✔ Discounts and promotions</li>
                    <li>✔ Festivals and seasonal events</li>
                    <li>✔ Weather impact</li>
                    <li>✔ Market trends</li>
                  </ul>
                </div>
                <div className="demand-modal-capabilities">
                  <div className="demand-modal-cap-heading">What you get:</div>
                  <ul>
                    <li>✔ Updated demand forecast</li>
                    <li>✔ Impact analysis (% change)</li>
                    <li>✔ Before vs After comparison</li>
                    <li>✔ Clear decision insights</li>
                  </ul>
                </div>
                <div className="demand-modal-example">
                  <p>Example:</p>
                  <p className="demand-modal-example-quote">
                    “Reduce price by 10%” → Instantly see demand impact"
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default DemandForecasting;
