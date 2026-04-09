import re

with open('frontend/src/App.tsx', 'r') as f:
    text = f.read()

# Update pathByPage
if 'aiTools: "/ai-tools"' not in text:
    text = text.replace(
        '  purchaseOrders: "/purchase-orders",\n};',
        '  purchaseOrders: "/purchase-orders",\n  aiTools: "/ai-tools",\n};'
    )

# Update getPageFromPath
if 'case "/ai-tools":' not in text:
    text = text.replace(
        '    case "/purchase-orders":\n      return "purchaseOrders";\n    case "/":',
        '    case "/purchase-orders":\n      return "purchaseOrders";\n    case "/ai-tools":\n      return "aiTools";\n    case "/":'
    )

with open('frontend/src/App.tsx', 'w') as f:
    f.write(text)

# anything
