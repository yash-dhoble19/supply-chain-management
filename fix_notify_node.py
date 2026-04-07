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
        # The AI agent node outputs '.text', not '.output'
        # Let's fix the parameter
        old_body = node["parameters"].get("jsonBody", "")
        new_body = old_body.replace('.item.json.output', '.item.json.text')
        node["parameters"]["jsonBody"] = new_body
        print("Updated Notify Dashboard node!")
        
    if node["name"] == "Update Supplier Record":
        # Ensure Groq AI output is also accessed via .text here too if it is used
        old_query = node["parameters"].get("query", "")
        if ".item.json.output" in old_query:
            new_query = old_query.replace('.item.json.output', '.item.json.text')
            node["parameters"]["query"] = new_query
            print("Updated Update Supplier Record node!")

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
    print("Workflow published!")
