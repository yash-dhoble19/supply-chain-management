import os

path = 'frontend/src/pages/ForecastOutput.tsx'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'Business Scenario Simulator' in line and '<h3' in line:
        line = line.replace('fontSize: "1.25rem"', 'fontSize: "1.6rem", fontWeight: 800')
        line = line.replace('color: "#0f172a"', 'color: "#1e293b"')
        line = line.replace('gap: 10', 'gap: 14')
    if 'Business Scenario Simulator' in line and '<span style={{ fontSize: "1.4rem" }}>🎯</span>' in line:
        line = line.replace('fontSize: "1.4rem"', 'fontSize: "1.8rem"')
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.write("".join(new_lines))
