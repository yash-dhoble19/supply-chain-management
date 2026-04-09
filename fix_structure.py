import os

path = 'frontend/src/pages/CreateForecast.tsx'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Remove duplicate workspace div at the start
new_lines = []
workspace_count = 0
for line in lines:
    if '<div className="forecast-workspace">' in line:
        workspace_count += 1
        if workspace_count == 2:
            continue # skip the second one
    new_lines.append(line)

# 2. Fix the closing tag sequence
# We look for the area where main and demand-content close.
# Current end of return looks like:
# ...
#           </div>
#         </main>
# 
#         {validationModal && (

final_lines = []
for i, line in enumerate(new_lines):
    if '3561' in str(i): # just a heuristic
        pass
    
    # We will do a targeted replacement of the block at the end of the results
    final_lines.append(line)

full_text = "".join(new_lines)

# Fix the specific closing section
old_end = """          </div>
        </main>

        {validationModal && ("""

new_end = """          </div>
        </div>
      </main>

      {validationModal && ("""

if old_end in full_text:
    full_text = full_text.replace(old_end, new_end)

with open(path, 'w', encoding='utf-8') as f:
    f.write(full_text)
