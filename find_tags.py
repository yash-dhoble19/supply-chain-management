import sys

def find_tags(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if '<>' in line or '</>' in line or '{hasParsedData && (' in line or '{!overallForecastSection && (' in line or '{overallForecastSection && (' in line:
            print(f"L{i+1}: {line.strip()}")

find_tags('frontend/src/pages/CreateForecast.tsx')
