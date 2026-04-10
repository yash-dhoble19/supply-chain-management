import os

def modify():
    path = 'frontend/src/pages/CreateForecast.tsx'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Disable redirect for good
    content = content.replace('onNavigate("demandForecasting");', '// onNavigate("demandForecasting");')
    content = content.replace('setTimeout(() => onNavigate("demandForecasting"), 300);', '// setTimeout(() => onNavigate("demandForecasting"), 300);')

    # Add scroll to top
    if 'window.scrollTo' not in content:
        content = content.replace('setForecastRequested(false);', 'setForecastRequested(false);\n    window.scrollTo({ top: 0, behavior: "smooth" });')

    # Content swapper
    # Find the start of demand-content
    target_start = '<div className="demand-content">'
    if target_start in content:
        # We want to put the Output at the top if it exists
        # And only show the workspace if it doesn't
        content = content.replace('<div className="forecast-workspace">', '{!overallForecastSection && (\n              <div className="forecast-workspace">')
        
        # We need to find where the workspace ends. It ends before the overallForecastSection check.
        content = content.replace('{overallForecastSection && (', '              </div>\n            )}\n\n            {overallForecastSection && (')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    modify()
