import os

path = 'frontend/src/pages/ForecastOutput.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Box style
box_style = 'padding: "16px", background: "#f8fafc", border: "1px solid #cbd5e1", borderRadius: "12px", boxShadow: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)"'

# Replace the labels in simulation-controls
# Note: we need to handle the className="config-field" existing style
content = content.replace('className="config-field"', f'className="config-field" style={{{box_style}}}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
