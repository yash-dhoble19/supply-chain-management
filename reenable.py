import sys

def modifyFile():
    with open('frontend/src/pages/CreateForecast.tsx', 'r', encoding='utf-8') as f:
        content = f.read()

    # Re-enable redirect in useEffect
    content = content.replace('// onNavigate(\"demandForecasting\");', 'onNavigate(\"demandForecasting\");')
    content = content.replace('// setForecastRequested(false);', 'setForecastRequested(false);')
    
    # Re-enable setTimeout redirect
    content = content.replace('// setTimeout', 'setTimeout')

    with open('frontend/src/pages/CreateForecast.tsx', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    modifyFile()
