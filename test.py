import sys

def modifyFile():
    with open('frontend/src/pages/CreateForecast.tsx', 'r', encoding='utf-8') as f:
        content = f.read()

    target_timeout = 'setTimeout(() => onNavigate(\"demandForecasting\"), 300);'
    replacement_timeout = '// ' + target_timeout
    content = content.replace(target_timeout, replacement_timeout)

    target_render = '''                    </div>\n                  </section>\n                )}\n\n              </>\n            )}\n          </>\n        )}'''
    replacement_render = '''                    </div>\n                  </section>\n                )}\n\n                {forecastRequested && overallForecastSection && (\n                  <ForecastOutput\n                    section={overallForecastSection}\n                    forecastLevel={forecastLevel}\n                    productCategoryOptions={productCategoryOptions}\n                    productOptions={productOptions}\n                    selectedCategory={selectedCategory}\n                    selectedProductKey={selectedProductKey}\n                    onCategoryChange={(v) => { setSelectedCategory(v); setSelectedProductKey(\"\"); }}\n                    onProductChange={setSelectedProductKey}\n                    locationFieldConfig={locationFieldConfig}\n                    locationOptionsByField={locationOptionsByField}\n                    locationSelections={locationSelections}\n                    onLocationChange={updateLocationSelection}\n                  />\n                )}\n\n              </>\n            )}\n          </>\n        )}'''
    content = content.replace(target_render, replacement_render)

    with open('frontend/src/pages/CreateForecast.tsx', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    modifyFile()
