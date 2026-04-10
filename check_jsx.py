import sys

def count_tags(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    open_brackets = 0
    open_fragments = 0
    
    for i, line in enumerate(lines):
        ln = i + 1
        # Simple counts
        if '{' in line and '(' in line and '&& (' in line:
            open_brackets += line.count('{')
            # print(f"L{ln}: Open JS {open_brackets}")
        if '<>' in line:
            open_fragments += line.count('<>')
            # print(f"L{ln}: Open FG {open_fragments}")
        if ')}' in line:
            open_brackets -= line.count(')}')
            # print(f"L{ln}: Close JS {open_brackets}")
        if '</>' in line:
            open_fragments -= line.count('</>')
            # print(f"L{ln}: Close FG {open_fragments}")
            
    print(f"Final Count: Brackets {open_brackets}, Fragments {open_fragments}")

count_tags('frontend/src/pages/CreateForecast.tsx')
