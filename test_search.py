import requests
import json

print("Testing supplier search API (ZenRows external only)...")
r = requests.post(
    "http://localhost:8000/api/ai-tools/supplier-search",
    json={"product_name": "Steel Pipes", "sources": ["external"]},
    timeout=30,
)
print(f"STATUS: {r.status_code}")
d = r.json()
print(f"Found: {d.get('total_found')} suppliers")
print(f"Session: {d.get('session_code')}")
print()
for i, s in enumerate(d.get("suppliers", [])):
    print(f"{i+1}. {s['company_name']}")
    print(f"   Location: {s['location']}")
    print(f"   AI Score: {s['ai_score']}")
    print(f"   Source: {s['source']}")
    print(f"   Email: {s['contact_email']}")
    print(f"   Delivery: {s['average_delivery_days']} days")
    print()

# Save full JSON for inspection
with open("test_output.json", "w") as f:
    json.dump(d, f, indent=2)
print("Full JSON saved to test_output.json")

# anything
