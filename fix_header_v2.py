import os

path = 'frontend/src/pages/ForecastOutput.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Targeted multiline replacement
old_h3 = """<h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: 10, color: "#0f172a", fontSize: "1.25rem" }}>
            <span style={{ fontSize: "1.4rem" }}>🎯</span> Business Scenario Simulator
          </h3>"""

new_h3 = """<h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: 14, color: "#1e293b", fontSize: "1.65rem", fontWeight: 800, letterSpacing: "-0.02em" }}>
            <span style={{ fontSize: "1.85rem" }}>🎯</span> Business Scenario Simulator
          </h3>"""

if old_h3 in content:
    content = content.replace(old_h3, new_h3)
    print("Replaced!")
else:
    # Try with single spaces or different indentations
    import re
    cleaned_old = re.sub(r'\s+', ' ', old_h3)
    # This is getting complex, I'll just find the lines by number.
    lines = content.split('\n')
    for i in range(len(lines)):
        if 'Business Scenario Simulator' in lines[i] and '</h3>' in lines[i+1 if i+1 < len(lines) else i]:
             # We found it. Now look back for h3
             for j in range(i, i-5, -1):
                 if '<h3' in lines[j]:
                     lines[j] = '          <h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: 14, color: "#1e293b", fontSize: "1.65rem", fontWeight: 800, letterSpacing: "-0.02em" }}>'
                     break
             lines[i] = '            <span style={{ fontSize: "1.85rem" }}>🎯</span> Business Scenario Simulator'
             print(f"Fixed lines {j} and {i}")

    content = '\n'.join(lines)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
