import os

def modify():
    path = 'frontend/src/pages/CreateForecast.tsx'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add the "Edit Configuration" button above ForecastOutput
    target = '{overallForecastSection && ('
    replacement = target + """\n                  <div className=\"forecast-results-header\" style={{ display: \"flex\", justifyContent: \"space-between\", alignItems: \"center\", marginBottom: 24 }}>\n                    <h2 style={{ fontSize: \"1.5rem\", margin: 0 }}>Forecast Analysis Results</h2>\n                    <button className=\"demand-cta\" style={{ width: \"fit-content\", padding: \"8px 20px\" }} onClick={() => setOverallForecastSection(null)}>⚙️ Edit Configuration</button>\n                  </div>"""
    
    content = content.replace(target, replacement)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    modify()
