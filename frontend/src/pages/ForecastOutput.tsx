/**
 * ForecastOutput.tsx
 *
 * Drop-in replacement for the `forecastRequested` section in CreateForecast.tsx.
 *
 * HOW TO USE:
 *  1. Copy this file into your project alongside CreateForecast.tsx.
 *  2. In CreateForecast.tsx, replace the entire block:
 *       {forecastRequested && ( ... )}
 *     with:
 *       {forecastRequested && overallForecastSection && (
 *         <ForecastOutput
 *           section={overallForecastSection}
 *           forecastLevel={forecastLevel}
 *           productCategoryOptions={productCategoryOptions}
 *           productOptions={productOptions}
 *           selectedCategory={selectedCategory}
 *           selectedProductKey={selectedProductKey}
 *           onCategoryChange={(v) => { setSelectedCategory(v); setSelectedProductKey(""); }}
 *           onProductChange={setSelectedProductKey}
 *           locationFieldConfig={locationFieldConfig}
 *           locationOptionsByField={locationOptionsByField}
 *           locationSelections={locationSelections}
 *           onLocationChange={updateLocationSelection}
 *         />
 *       )}
 *  3. Add the import at the top of CreateForecast.tsx:
 *       import { ForecastOutput } from "./ForecastOutput";
 *
 * WHAT CHANGED (display only — zero logic changes):
 *  - Summary KPI cards (total, avg daily, min, max)
 *  - Badge row (trend / confidence / demand type / model)
 *  - Simple forecast table with festival annotations
 *  - Product / Location drill-down selectors (existing logic, improved layout)
 */

import { useEffect, useMemo, useState } from "react";
import type { ForecastSection } from "./forecastEngine";

interface ProductOption {
  key: string;
  label: string;
}

interface LocationField {
  key: string;
  label: string;
  column: string;
}

interface ForecastOutputProps {
  section: ForecastSection;
  forecastLevel: "overall" | "product" | "location" | "combined";
  productCategoryOptions: string[];
  productOptions: ProductOption[];
  selectedCategory: string;
  selectedProductKey: string;
  onCategoryChange: (v: string) => void;
  onProductChange: (v: string) => void;
  locationFieldConfig: LocationField[];
  locationOptionsByField: Record<string, string[]>;
  locationSelections: Record<string, string>;
  onLocationChange: (fieldKey: string, value: string) => void;
}

const fmtMoney = (value: number) =>
  value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function ForecastOutput({
  section,
  forecastLevel,
  productCategoryOptions,
  productOptions,
  selectedCategory,
  selectedProductKey,
  onCategoryChange,
  onProductChange,
  locationFieldConfig,
  locationOptionsByField,
  locationSelections,
  onLocationChange,
}: ForecastOutputProps) {
  const smart = section.smart;
  const kpis = [
    { label: "Total forecast", value: fmtMoney(section.metrics.totalForecast), icon: "📊" },
    { label: "Avg daily", value: fmtMoney(section.metrics.avgDailyForecast), icon: "📈" },
    { label: "Lowest (p10)", value: fmtMoney(section.metrics.minForecast), icon: "📉" },
    { label: "Highest (p90)", value: fmtMoney(section.metrics.maxForecast), icon: "📈" },
  ];

  const [tablePage, setTablePage] = useState(1);
  const pageSize = 10;
  const totalPages = Math.max(1, Math.ceil(section.table.length / pageSize));
  const tableRows = useMemo(() => {
    const start = (tablePage - 1) * pageSize;
    return section.table.slice(start, start + pageSize);
  }, [section.table, tablePage]);

  useEffect(() => {
    setTablePage(1);
  }, [section.table.length]);

  useEffect(() => {
    if (tablePage > totalPages) {
      setTablePage(totalPages);
    }
  }, [tablePage, totalPages]);

  const festivalSet = new Set(
    smart.forecast.filter((point) => point.festivalName).map((point) => point.date)
  );

  const minForecastValue = useMemo(
    () => Math.min(...section.table.map((point) => point.forecast)),
    [section.table]
  );

  const maxForecastValue = useMemo(
    () => Math.max(...section.table.map((point) => point.forecast)),
    [section.table]
  );

  return (
    <>
      <section className="forecast-section overall-forecast-output" style={{ marginTop: 20 }}>
        <div className="forecast-section-header">
          <div>
            <h3>Demand Forecast</h3>
            <p className="forecast-section-subtitle">
              Simple moving average of the cleaned data.
            </p>
          </div>
        </div>

        <div className="forecast-kpi-card-grid">
          {kpis.map((kpi) => (
            <article className="forecast-kpi-card" key={kpi.label}>
              <span className="forecast-kpi-icon" aria-hidden="true">
                {kpi.icon}
              </span>
              <span className="forecast-kpi-label">{kpi.label}</span>
              <strong className="forecast-kpi-value">{kpi.value}</strong>
            </article>
          ))}
        </div>

        <div className="forecast-badge-row">
          <span className={`forecast-badge forecast-badge-demand ${smart.summary.demandType.toLowerCase()}`}>
            {smart.summary.demandType} Demand
          </span>
          <span className={`forecast-badge forecast-badge-trend ${smart.summary.trend}`}>
            {smart.summary.trend} Trend
          </span>
          <span className={`forecast-badge forecast-badge-confidence ${smart.summary.confidence.toLowerCase()}`}>
            {smart.summary.confidence} Confidence
          </span>
        </div>

        <p className="mapping-helper" style={{ marginTop: 8 }}>
          <strong>Model: {section.smart.model.name}</strong>
          <br />
          {section.smart.model.reason}
        </p>

        <div className="forecast-output-table" style={{ marginTop: 12 }}>
          <div className="forecast-table-row forecast-table-header">
            <span className="forecast-table-cell forecast-table-date">Date</span>
            <span className="forecast-table-cell forecast-table-number">Forecast</span>
            <span className="forecast-table-cell forecast-table-number">Lower Bound</span>
            <span className="forecast-table-cell forecast-table-number">Upper Bound</span>
          </div>
          {tableRows.map((row, index) => {
            const isLowest = row.forecast === minForecastValue;
            const isHighest = row.forecast === maxForecastValue;
            return (
              <div
                className={`forecast-table-row ${index % 2 === 0 ? "even" : "odd"} ${
                  isLowest ? "row-lowest" : ""
                } ${isHighest ? "row-highest" : ""}`}
                key={row.date + index}
              >
                <span className="forecast-table-cell forecast-table-date">{row.date || "N/A"}</span>
                <span className="forecast-table-cell forecast-table-number forecast-value">
                  {fmtMoney(row.forecast)}
                </span>
                <span className="forecast-table-cell forecast-table-number forecast-muted">
                  {fmtMoney(row.lowerBound)}
                </span>
                <span className="forecast-table-cell forecast-table-number">
                  {fmtMoney(row.upperBound)}
                  {festivalSet.has(row.date) && (
                    <span style={{ marginLeft: 6, color: "#92400e", fontSize: 0.75 }}>
                      ★ Festival
                    </span>
                  )}
                </span>
              </div>
            );
          })}
          <div className="forecast-table-pagination">
            <button
              type="button"
              className="pagination-button"
              onClick={() => setTablePage((prev) => Math.max(1, prev - 1))}
              disabled={tablePage === 1}
            >
              ← Previous
            </button>
            <span className="forecast-pagination-label">
              Page {tablePage} of {totalPages}
            </span>
            <button
              type="button"
              className="pagination-button"
              onClick={() => setTablePage((prev) => Math.min(totalPages, prev + 1))}
              disabled={tablePage === totalPages}
            >
              Next →
            </button>
          </div>
        </div>
      </section>

      {(forecastLevel === "product" || forecastLevel === "combined") && (
        <div className="forecast-flow-panel" style={{ marginTop: 18 }}>
          <label className="config-field">
            <span>Category</span>
            <select
              value={selectedCategory}
              onChange={(event) => onCategoryChange(event.target.value)}
            >
              <option value="">All categories</option>
              {productCategoryOptions.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
          <label className="config-field">
            <span>Product</span>
            <select
              value={selectedProductKey}
              onChange={(event) => onProductChange(event.target.value)}
            >
              <option value="">Select product</option>
              {productOptions.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      {(forecastLevel === "location" || forecastLevel === "combined") && (
        <div className="forecast-flow-panel" style={{ marginTop: 18 }}>
          {locationFieldConfig.length ? (
            locationFieldConfig.map((field) => (
              <label className="config-field" key={field.key}>
                <span>
                  {field.label}
                  <small className="mapping-helper" style={{ fontSize: "0.8rem", marginLeft: 4 }}>
                    Column: {field.column}
                  </small>
                </span>
                <select
                  value={locationSelections[field.key] ?? ""}
                  onChange={(event) => onLocationChange(field.key, event.target.value)}
                >
                  <option value="">All {field.label}</option>
                  {(locationOptionsByField[field.key] ?? []).map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
            ))
          ) : (
            <p className="mapping-helper">
              No location columns detected yet. Add country/state/city/store data to unlock this view.
            </p>
          )}
        </div>
      )}
    </>
  );
}

export default ForecastOutput;
