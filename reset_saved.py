import sys

def modifyFile():
    with open('frontend/src/pages/CreateForecast.tsx', 'r', encoding='utf-8') as f:
        content = f.read()

    # Reset hasSavedForecast when starting a new generation
    target = 'setIsGenerating(true);'
    replacement = 'setIsGenerating(true);\n    setHasSavedForecast(false);'
    content = content.replace(target, replacement)

    with open('frontend/src/pages/CreateForecast.tsx', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    modifyFile()
