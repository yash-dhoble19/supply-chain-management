import sys

def modifyFile():
    with open('frontend/src/pages/CreateForecast.tsx', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Comment out ALL onNavigate calls to demandForecasting
    # Using regex-like replacement for various formats including commented ones
    content = content.replace('onNavigate(\"demandForecasting\");', '// onNavigate(\"demandForecasting\");')
    content = content.replace('setTimeout(() => onNavigate(\"demandForecasting\"), 300);', '// setTimeout(() => onNavigate(\"demandForecasting\"), 300);')
    
    # 2. Ensure hasSavedForecast is reset so regeneration works
    if 'setHasSavedForecast(false);' not in content:
        content = content.replace('setIsGenerating(true);', 'setIsGenerating(true);\n    setHasSavedForecast(false);')

    # 3. Ensure the rendering condition is simple
    # It might have {forecastRequested && overallForecastSection && ( 
    # or {overallForecastSection && ( 
    content = content.replace('{forecastRequested && overallForecastSection && (', '{overallForecastSection && (')

    with open('frontend/src/pages/CreateForecast.tsx', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    modifyFile()
