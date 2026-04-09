import os

def fix_quotes(filename):
    if not os.path.exists(filename):
        print(f"File {filename} not found")
        return
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove the backslashes before quotes that were added by PowerShell
    fixed = content.replace('\\\"', '\"')
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(fixed)

if __name__ == '__main__':
    fix_quotes('frontend/src/pages/DemandForecasting.tsx')
    fix_quotes('frontend/src/pages/CreateForecast.tsx')
