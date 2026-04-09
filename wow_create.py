import sys
import os

def modifyFile():
    path = 'frontend/src/pages/CreateForecast.tsx'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add window.scrollTo(0,0) in handleGenerateForecast when overallForecastSection is set
    # Using a slightly different approach: find where setOverallForecastSection is called and add scroll there
    # But it's easier to put it in the useEffect that handles the snapshot
    target = 'setForecastRequested(false);'
    replacement = 'setForecastRequested(false);\n    window.scrollTo({ top: 0, behavior: \"smooth\" });'
    content = content.replace(target, replacement)

    # 2. Swap the content order: If output exists, show it at the TOP, then hide the form parts
    # We find the start of demand-content and insert our logic
    start_tag = '<div className=\"demand-content\">'
    split_content = content.split(start_tag)
    if len(split_content) > 1:
        prefix = split_content[0] + start_tag
        rest = split_content[1]
        
        # New logic: If output exists, show a Header and the Output. 
        # Then, only show the stepper/form if output does NOT exist.
        swapper = \"\"\"\n            {overallForecastSection ? (\n              <div className=\"forecast-results-view animate-fade-in\">\n                <div style={{ display: \"flex\", justifyContent: \"space-between\", alignItems: \"center\", marginBottom: 24, padding: \"0 4px\" }}>\n                  <div>\n                    <h2 style={{ fontSize: \"1.75rem\", fontWeight: 800, color: \"#0f172a\", margin: 0 }}>Forecast Intelligence Report</h2>\n                    <p style={{ color: \"#64748b\", marginTop: 4 }}>High-fidelity Prophet model results powered by ChainMind AI</p>\n                  </div>\n                  <button \n                    className=\"demand-cta\" \n                    style={{ width: \"fit-content\", padding: \"10px 24px\", borderRadius: 12, boxShadow: \"0 4px 12px rgba(59, 130, 246, 0.2)\" }}\n                    onClick={() => setOverallForecastSection(null)}\n                  >\n                    ⚙️ Edit Configuration\n                  </button>\n                </div>\n                \n                <ForecastOutput\n                  section={overallForecastSection}\n                  forecastLevel={forecastLevel}\n                  productCategoryOptions={productCategoryOptions}\n                  productOptions={productOptions}\n                  selectedCategory={selectedCategory}\n                  selectedProductKey={selectedProductKey}\n                  onCategoryChange={(v) => { setSelectedCategory(v); setSelectedProductKey(\"\"); }}\n                  onProductChange={setSelectedProductKey}\n                  locationFieldConfig={locationFieldConfig}\n                  locationOptionsByField={locationOptionsByField}\n                  locationSelections={locationSelections}\n                  onLocationChange={updateLocationSelection}\n                  insightHighlights={insightHighlights}\n                />\n                \n                <div style={{ marginTop: 40, padding: 24, background: \"#f8fafc\", borderRadius: 16, border: \"1px dashed #cbd5e1\", textAlign: \"center\" }}>\n                  <p style={{ color: \"#475569\", margin: 0 }}>Need to adjust the model? Click <strong>Edit Configuration</strong> above to change horizons or filters.</p>\n                </div>\n              </div>\n            ) : (\n\"\"\"
        
        # Now we need to find the matching close for the forecast-workspace and all its children
        # This is hard with pure text. Let's instead just use the existing conditions but make them swappable.
        
        # Simpler approach:
        # Wrap the entire forecast-workspace in {!overallForecastSection && (
        content = content.replace('<div className=\"forecast-workspace\">', '{!overallForecastSection && (\\n              <div className=\"forecast-workspace\">')
        
        # And close it before the last ForecastOutput block
        # The ForecastOutput block was around 3492
        target_close = '{overallForecastSection && ('
        content = content.replace(target_close, ')}' + target_close)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    modifyFile()
