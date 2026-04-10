import sys

def count_tags(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    opens = content.count('<div')
    closes = content.count('</div>')
    m_opens = content.count('<main')
    m_closes = content.count('</main>')
    f_opens = content.count('<>')
    f_closes = content.count('</>')
    
    print(f"DIVs: {opens} opens, {closes} closes (diff: {opens - closes})")
    print(f"MAINs: {m_opens} opens, {m_closes} closes (diff: {m_opens - m_closes})")
    print(f"Fragments: {f_opens} opens, {f_closes} closes (diff: {f_opens - f_closes})")

count_tags('frontend/src/pages/CreateForecast.tsx')
