import os

def modify():
    path = 'frontend/src/pages/CreateForecast.tsx'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add resultsRef definition
    if 'const resultsRef = useRef' not in content:
        content = content.replace('const fileInputRef = useRef', 'const resultsRef = useRef<HTMLDivElement>(null);\n  const fileInputRef = useRef')

    # 2. Add scroll effect
    scroll_effect = """
  useEffect(() => {
    if (overallForecastSection && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [overallForecastSection]);
"""
    if 'resultsRef.current.scrollIntoView' not in content:
        content = content.replace('const updateLocationSelection =', scroll_effect + '\n  const updateLocationSelection =')

    # 3. Clean up the demand-content block
    # Restore the workspace to be always visible
    content = content.replace('{!overallForecastSection && (', '')
    content = content.replace('<div className="forecast-workspace">', '<div className="forecast-workspace">')
    
    # 4. Correct the results section at the bottom
    # We find the end of the workspace div and insert the results there
    # This is tricky because there are many closing divs. 
    # Let's find the closing of </section> for config (last step)
    
    # Let's find the specific block for overallForecastSection and move it or update it.
    if '{overallForecastSection && (' in content:
        results_block = """
            {overallForecastSection && (
              <div ref={resultsRef} className="forecast-results-container animate-fade-in" style={{ marginTop: 60, borderTop: "2px solid #e2e8f0", paddingTop: 40, paddingBottom: 60 }}>
                  <div className="forecast-results-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
                    <h2 style={{ fontSize: "1.85rem", fontWeight: 800, color: "#0f172a", letterSpacing: "-0.02em" }}>Intelligence Analysis Dashboard</h2>
                    <button 
                      className="demand-cta" 
                      style={{ 
                        width: "fit-content", 
                        padding: "12px 28px", 
                        background: "linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)", 
                        borderRadius: 14,
                        boxShadow: "0 10px 15px -3px rgba(79, 70, 229, 0.4)",
                        border: "none",
                        color: "white",
                        fontWeight: 600,
                        cursor: "pointer"
                      }} 
                      onClick={() => {
                        window.scrollTo({ top: 0, behavior: "smooth" });
                        setTimeout(() => {
                          setOverallForecastSection(null);
                          setHasParsedData(false);
                          setDataSummary(null);
                          setUploadedFileName("");
                          setPreviewRows([]);
                          setColumns([]);
                          setCleanedRows([]);
                          setStatusMessage("");
                          setHasSavedForecast(false);
                        }, 400);
                      }}
                    >
                      🚀 Create New Forecast
                    </button>
                  </div>
                  <ForecastOutput
                    section={overallForecastSection}
                    forecastLevel={forecastLevel}
                    productCategoryOptions={productCategoryOptions}
                    productOptions={productOptions}
                    selectedCategory={selectedCategory}
                    selectedProductKey={selectedProductKey}
                    onCategoryChange={(v) => { setSelectedCategory(v); setSelectedProductKey(""); }}
                    onProductChange={setSelectedProductKey}
                    locationFieldConfig={locationFieldConfig}
                    locationOptionsByField={locationOptionsByField}
                    locationSelections={locationSelections}
                    onLocationChange={updateLocationSelection}
                    insightHighlights={insightHighlights}
                  />
              </div>
            )}
"""
        # Find where to put it. We want it after the last section.
        # But for now let's just replace the existing overallForecastSection block.
        # I'll use a regex-like replace for the whole block from '{overallForecastSection && (' to ')}'
        # but since I don't have regex tool, I'll search for unique anchors.
        
        # Actually, my previous turn already moved it to the bottom-ish.
        # I'll just replace the button text and adding the ref.
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    modify()
