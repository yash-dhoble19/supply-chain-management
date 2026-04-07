import requests

try:
    resp = requests.get('http://localhost:8000/api/ai-tools/communication/interactions')
    data = resp.json()
    for item in data.get('items', []):
        print(f"ID: {item.get('interaction_id')} - Status: {item.get('status')} - Supplier: {item.get('company_name')}")
except Exception as e:
    print("Error:", e)
