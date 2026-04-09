import subprocess
import os

def add_comment():
    # Get all tracked files
    result = subprocess.run(['git', 'ls-files'], stdout=subprocess.PIPE, text=True)
    files = result.stdout.strip().split('\n')
    
    for file in files:
        if not file.strip(): continue
        # don't touch node_modules or venv just in case they are tracked
        if 'node_modules' in file or 'venv' in file:
            continue
            
        # check if file exists and is a file
        if not os.path.isfile(file):
            continue
            
        ext = os.path.splitext(file)[1].lower()
        comment = ""
        if ext in ['.py', '.sh', '.yaml', '.yml']:
            comment = "\n# anything\n"
        elif ext in ['.js', '.ts', '.tsx', '.jsx', '.c', '.cpp', '.java']:
            comment = "\n// anything\n"
        elif ext in ['.html', '.md', '.xml']:
            comment = "\n<!-- anything -->\n"
        elif ext in ['.css']:
            comment = "\n/* anything */\n"
        elif ext in ['.sql']:
            comment = "\n-- anything\n"
        else:
            # We'll just leave json and others alone, or add a newline 
            # so they get modified
            comment = "\n"

        try:
            with open(file, 'a', encoding='utf-8') as f:
                f.write(comment)
            print(f"Modified {file}")
        except Exception as e:
            print(f"Skipping {file}: {e}")

if __name__ == '__main__':
    add_comment()
