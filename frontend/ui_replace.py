import sys
import re

with open('src/pages/ForecastOutput.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update fetchAiExplanation to include externalInsights
c = c.replace(
    'const [aiModelUsed, setAiModelUsed] = useState<string | null>(null);',
    '''const [aiModelUsed, setAiModelUsed] = useState<string | null>(null);
  const [externalContext, setExternalContext] = useState<string[]>([]);'''
)

fetch_ai_old = '''      const configuredLocation = Object.values(locationSelections || {}).filter(Boolean).join(", ") || "India";

      const payload = {'''

fetch_ai_new = '''      const configuredLocation = Object.values(locationSelections || {}).filter(Boolean).join(", ") || "India";
      
      // Fetch external Twitter + Weather insights dynamically
      const { generateInsights } = await import("./externalIntelligence");
      const productName = productOptions.find(p => p.key === selectedProductKey)?.label || selectedCategory || "Products";
      const dates = section.smart.forecast.map(f => f.date);
      const extInsights = await generateInsights(productName, selectedCategory || "retail", dates);
      setExternalContext(extInsights);

      const payload = {
        externalContext: extInsights.join(" | "),'''

if fetch_ai_old in c:
    c = c.replace(fetch_ai_old, fetch_ai_new)
else:
    print("FAILED on fetch_ai_old")


# 2. Update insights UI rendering
insights_box_old = '''<div className="insights-summary ai-generated-content" style={{ 
              padding: "12px 16px", 
              background: "rgba(16, 185, 129, 0.1)", 
              borderLeft: "4px solid #10b981", 
              borderRadius: "0 8px 8px 0",
              maxHeight: "250px",
              overflowY: "auto"
            }}>
              <div style={{ fontSize: "0.75rem", color: "#10b981", marginBottom: 8, fontWeight: "bold" }}>Powered by {aiModelUsed}</div>
              <div 
                style={{ whiteSpace: "pre-wrap", lineHeight: 1.5, color: "#374151", fontSize: "0.9rem" }} 
                dangerouslySetInnerHTML={{ 
                  __html: aiExplanation
                    .replace(/\\n/g, '<br/>')
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color: #111827">$1</strong>')
                    .replace(/## (.*?)<br\\/>/g, '<h4 style="color: #065f46; margin-top: 12px; margin-bottom: 6px">$1</h4>')
                    .replace(/- (.*?)<br\\/>/g, '<li style="margin-left: 20px; list-style-type: disc; color: #4b5563;">$1</li>')
                }} 
              />
            </div>'''

insights_box_new = '''<div className="insights-summary ai-generated-content" style={{ 
              padding: "20px 24px", 
              background: "#eef2ff", 
              borderLeft: "6px solid #3b82f6", 
              borderRadius: "8px",
              boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
              color: "#334155"
            }}>
              <div style={{ fontSize: "1.05rem", color: "#0ea5e9", marginBottom: 12, fontWeight: "bold", display: "flex", alignItems: "center", gap: "8px" }}>
                <span>✨</span> AI Insight: {productOptions.find(p => p.key === selectedProductKey)?.label || selectedCategory || "Overall Demand"}
              </div>
              <div 
                style={{ whiteSpace: "pre-wrap", lineHeight: 1.6, color: "#334155", fontSize: "0.95rem" }} 
                dangerouslySetInnerHTML={{ 
                  __html: aiExplanation
                    .replace(/\\n/g, '<br/>')
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color: #0f172a">$1</strong>')
                    .replace(/## (.*?)<br\\/>/g, '<br/>')
                    .replace(/- (.*?)<br\\/>/g, '$1 ')
                }} 
              />
              {externalContext.length > 0 && (
                <div style={{ marginTop: 24, fontSize: "0.85rem", color: "#475569", fontWeight: "bold", borderTop: "1px solid #cbd5e1", paddingTop: 12 }}>
                  Context: {externalContext.join(" | ")}
                </div>
              )}
            </div>'''

if insights_box_old in c:
    c = c.replace(insights_box_old, insights_box_new)
else:
    print("FAILED on insights_box")


# 3. Update Chart Definition completely!
chart_old_start = 'const ForecastTimelineChart = ({'
chart_old_end = 'export function ForecastOutput({'

chart_new = '''const ForecastTimelineChart = ({
  historical,
  forecast,
  trend,
  confidence,
  category,
}: ForecastChartProps) => {

  const points = useMemo(() => {
    const combined = [...historical, ...forecast];
    if (!combined.length) return null;

    const values = [
      ...historical.map((row) => row.value),
      ...forecast.map((row) => row.forecast),
      ...forecast.map((row) => row.lowerBound),
      ...forecast.map((row) => row.upperBound),
    ].filter(v => v !== undefined && !isNaN(v));
    
    const minValue = Math.min(0, ...values);
    const maxValue = Math.max(...values, 1);
    const valueRange = maxValue - minValue;

    const totalPoints = combined.length - 1 || 1;

    const toY = (value: number) =>
      CHART_HEIGHT - ((value - minValue) / valueRange) * (CHART_HEIGHT - 60) - 30; // padding top/bottom

    const toX = (index: number) => (index / totalPoints) * (CHART_WIDTH - 60) + 30; // padding left/right

    const historyPoints = historical.map((row, index) => ({
      x: toX(index),
      y: toY(row.value),
      label: row.date,
      value: row.value,
    }));

    const forecastPoints = forecast.map((row, index) => ({
      x: toX(historyPoints.length + index),
      y: toY(row.forecast),
      p10: toY(row.lowerBound),
      p90: toY(row.upperBound),
      label: row.date,
    }));

    return { historyPoints, forecastPoints, minValue, maxValue };
  }, [historical, forecast]);

  if (!points || points.historyPoints.length === 0 || points.forecastPoints.length === 0) {
    return null;
  }

  const { historyPoints, forecastPoints } = points;

  const historyPath = historyPoints
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");

  const forecastPath = forecastPoints
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");

  const areaSegments = [
    ...forecastPoints.map((point) => ({ x: point.x, y: point.p90 })),
    ...forecastPoints.slice().reverse().map((point) => ({ x: point.x, y: point.p10 })),
  ];

  const areaPath = areaSegments
    .map((segment, index) => `${index === 0 ? "M" : "L"} ${segment.x.toFixed(2)} ${segment.y.toFixed(2)}`)
    .concat(["Z"])
    .join(" ");

  const lastHistoryPoint = historyPoints[historyPoints.length - 1];
  const firstForecastPoint = forecastPoints[0];

  return (
    <>
      <div className="forecast-chart" style={{ width: "100%", marginTop: 24, background: "#f8fafc", padding: "16px 0", borderRadius: 8, position: "relative" }}>
        
        {/* Title and Legend HTML overlay */}
        <div style={{ display: "flex", justifyContent: "space-between", padding: "0 30px", marginBottom: 12 }}>
          <div style={{ fontSize: "1.1rem", fontWeight: "bold", color: "#1e293b", display: "flex", alignItems: "center", gap: 8 }}>
            📊 Demand Forecast: {category || "Products"}
          </div>
          <div style={{ display: "flex", gap: 16, fontSize: "0.75rem", color: "#475569", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <svg width="24" height="10"><path d="M0,5 L24,5" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 4"/><circle cx="12" cy="5" r="3" fill="#3b82f6"/></svg>
              AI Forecast
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <svg width="24" height="10"><path d="M0,5 L24,5" stroke="#10b981" strokeWidth="2"/><circle cx="12" cy="5" r="3" fill="#10b981"/></svg>
              Historical Sales
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div style={{ width: 24, height: 10, background: "#dbeafe" }}></div>
              Confidence Interval
            </div>
          </div>
        </div>

        <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} style={{ width: "100%", height: 320 }}>
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map(pct => {
            const y = 30 + (CHART_HEIGHT - 60) * pct;
            const val = points.maxValue - (points.maxValue - points.minValue) * pct;
            return (
              <g key={`grid-y-${pct}`}>
                <line x1="30" y1={y} x2={CHART_WIDTH - 30} y2={y} stroke="#e2e8f0" strokeWidth="1" />
                <text x="25" y={y + 4} fill="#94a3b8" fontSize="10" textAnchor="end">{val >= 1000 ? (val/1000).toFixed(1) + 'k' : Math.round(val)}</text>
              </g>
            );
          })}
          
          {areaSegments.length > 2 && (
            <path d={areaPath} fill="#eff6ff" stroke="none" />
          )}
          
          <path d={historyPath} fill="none" stroke="#10b981" strokeWidth="3" strokeLinecap="round" />
          {historyPoints.map((pt, i) => <circle key={i} cx={pt.x} cy={pt.y} r="4" fill="#10b981" stroke="#fff" strokeWidth="1.5" />)}
          
          <path d={forecastPath} fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="6 4" />
          {forecastPoints.map((pt, i) => <polygon key={`f-${i}`} points={`${pt.x},${pt.y-4} ${pt.x+4},${pt.y} ${pt.x},${pt.y+4} ${pt.x-4},${pt.y}`} fill="#3b82f6" stroke="#fff" strokeWidth="1" />)}

          {lastHistoryPoint && firstForecastPoint && (
            <line x1={lastHistoryPoint.x} y1={lastHistoryPoint.y} x2={firstForecastPoint.x} y2={firstForecastPoint.y} stroke="#94a3b8" strokeWidth="2" strokeDasharray="4 4" />
          )}
        </svg>

        {/* X Axis labels HTML overlay */}
        <div style={{ display: "flex", justifyContent: "space-between", padding: "0 30px", marginTop: "-10px", color: "#64748b", fontSize: "0.75rem" }}>
          {historyPoints.filter((_, i) => i % Math.max(1, Math.floor(historyPoints.length/5)) === 0).map((pt, i) => (
            <div key={i} style={{ position: "absolute", left: `${(pt.x / CHART_WIDTH) * 100}%`, transform: "translateX(-50%)" }}>
              {new Date(pt.label).toLocaleDateString(undefined, {month: "short", year: "numeric", day: "numeric"})}
            </div>
          ))}
          {forecastPoints.filter((_, i) => i % Math.max(1, Math.floor(forecastPoints.length/3)) === 0).map((pt, i) => (
            <div key={`fx-${i}`} style={{ position: "absolute", left: `${(pt.x / CHART_WIDTH) * 100}%`, transform: "translateX(-50%)" }}>
              {new Date(pt.label).toLocaleDateString(undefined, {month: "short", year: "numeric", day: "numeric"})}
            </div>
          ))}
        </div>
        <div style={{ textAlign: "center", width: "100%", color: "#475569", fontSize: "0.85rem", marginTop: 24, fontWeight: "bold" }}>
          Date ({section.smart.model.name})
        </div>
      </div>
    </>
  );
};

export function ForecastOutput({'''

import re
old_block_match = re.search(r'const ForecastTimelineChart = \(\{(.*?)\nexport function ForecastOutput\(\{', c, re.DOTALL)
if old_block_match:
    c = c.replace(old_block_match.group(0), chart_new)
else:
    print("FAILED on chart rendering replacement")
    
with open('src/pages/ForecastOutput.tsx', 'w', encoding='utf-8') as f:
    f.write(c)
print("COMPLETED SUCCESS")
