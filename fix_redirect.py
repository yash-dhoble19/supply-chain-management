import sys

def modifyFile():
    with open('frontend/src/pages/CreateForecast.tsx', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Disable redirect and reset in useEffect at line 1440
    content = content.replace('onNavigate(\"demandForecasting\");', '// onNavigate(\"demandForecasting\");')
    content = content.replace('setForecastRequested(false);', '// setForecastRequested(false);')

    # 2. Update rendering condition to keep output visible (even if forecastRequested was toggled)
    content = content.replace('{forecastRequested && overallForecastSection && (', '{overallForecastSection && (')

    with open('frontend/src/pages/CreateForecast.tsx', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    modifyFile()
