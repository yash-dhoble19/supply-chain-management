import os

path = 'frontend/src/pages/ForecastOutput.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the double braces first
content = content.replace('style={padding:', 'style={{ padding:')
content = content.replace('0.05)"}', '0.05)" }}')

# Now specifically remove boxes from non-simulation area if they exist
# We will do this by line range or by finding the specific context.
# Actually, I'll just check if the user likes it. 
# But let's fix the syntax error first.

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
