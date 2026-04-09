import requests
import json

N8N_BASE = "https://yash1223456.app.n8n.cloud"
WORKFLOW_ID = "FJogRQZQSNViU8y5"

session = requests.Session()
login_resp = session.post(f"{N8N_BASE}/rest/login", json={
    "emailOrLdapLoginId": "yashdhoble6666@gmail.com",
    "password": "Yash@12345"
})

workflow = session.get(f"{N8N_BASE}/rest/workflows/{WORKFLOW_ID}").json()["data"]

for node in workflow["nodes"]:
    if node["name"] == "Notify Dashboard":
        old_body = node["parameters"].get("jsonBody", "")
        if '.item.json.output' in old_body:
            old_body = old_body.replace('.item.json.output', '.item.json.text')
        
        if "replace(/```/g" not in old_body:
            old_body = old_body.replace(
                'JSON.parse($("Extract Quote Information").item.json.text)',
                'JSON.parse(($("Extract Quote Information").item.json.text || "{ }").replace(/```json/gi, "").replace(/```/g, "").trim())'
            )
        node["parameters"]["jsonBody"] = old_body
        print("Updated Notify Dashboard node with robust JSON parsing!")

save_payload = {
    "nodes": workflow["nodes"],
    "connections": workflow["connections"],
    "settings": workflow.get("settings", {}),
    "name": workflow["name"],
}

resp = session.patch(f"{N8N_BASE}/rest/workflows/{WORKFLOW_ID}", json=save_payload)
print(f"Save status: {resp.status_code}")
if resp.status_code == 200:
    session.patch(f"{N8N_BASE}/rest/workflows/{WORKFLOW_ID}", json={"active": True})
    print("Workflow published securely!")

# anything
