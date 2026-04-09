"""
Fix the 'Update Supplier Record' node in n8n workflow via REST API.
Changes operation to executeQuery with proper SQL + WHERE clause.
"""
import requests
import json

N8N_BASE = "https://yash1223456.app.n8n.cloud"
WORKFLOW_ID = "FJogRQZQSNViU8y5"

# Step 1: Login to get session cookie
session = requests.Session()
login_resp = session.post(f"{N8N_BASE}/rest/login", json={
    "emailOrLdapLoginId": "yashdhoble6666@gmail.com",
    "password": "Yash@12345"
})
print(f"Login status: {login_resp.status_code}")
if login_resp.status_code != 200:
    print(f"Login failed: {login_resp.text}")
    exit(1)

# Step 2: Get the current workflow
wf_resp = session.get(f"{N8N_BASE}/rest/workflows/{WORKFLOW_ID}")
print(f"Get workflow status: {wf_resp.status_code}")
workflow = wf_resp.json()["data"]

# Step 3: Fix the 'Update Supplier Record' node
fixed = False
for node in workflow["nodes"]:
    if node["name"] == "Update Supplier Record":
        print(f"Found node: {node['name']}")
        print(f"Current operation: {node['parameters'].get('operation', 'insert')}")
        print(f"Current query: {node['parameters'].get('query', 'N/A')}")
        
        # Fix: change to executeQuery with proper SQL
        node["parameters"] = {
            "operation": "executeQuery",
            "query": "UPDATE suppliers SET last_reply_at = NOW(), total_replies_received = COALESCE(total_replies_received, 0) + 1 WHERE id = {{ $('Match Supplier').item.json.id }}",
            "options": {}
        }
        fixed = True
        print(f"\nFixed query: {node['parameters']['query']}")
        break

if not fixed:
    print("ERROR: Could not find 'Update Supplier Record' node!")
    exit(1)

# Step 4: Also fix the 'Notify Dashboard' node URL to remove stale ngrok URL
# and the 'Mark Low Responsiveness' & 'Send Escalation Alert' nodes too
for node in workflow["nodes"]:
    if node["name"] in ["Notify Dashboard", "Send Dashboard Confirmation", 
                         "Notify Dashboard - Follow-up Sent", "Send Escalation Alert"]:
        if "url" in node["parameters"]:
            old_url = node["parameters"]["url"]
            print(f"\nNode '{node['name']}' URL: {old_url}")

# Step 5: Save the updated workflow
# Remove fields that shouldn't be in the update payload
save_payload = {
    "nodes": workflow["nodes"],
    "connections": workflow["connections"],
    "settings": workflow.get("settings", {}),
    "name": workflow["name"],
}

save_resp = session.patch(
    f"{N8N_BASE}/rest/workflows/{WORKFLOW_ID}",
    json=save_payload,
    headers={"Content-Type": "application/json"}
)
print(f"\nSave status: {save_resp.status_code}")
if save_resp.status_code == 200:
    print("Workflow saved successfully!")
    
    # Step 6: Publish/activate the workflow
    activate_resp = session.patch(
        f"{N8N_BASE}/rest/workflows/{WORKFLOW_ID}",
        json={"active": True},
        headers={"Content-Type": "application/json"}
    )
    print(f"Activate status: {activate_resp.status_code}")
    if activate_resp.status_code == 200:
        print("Workflow published and active!")
    else:
        print(f"Activation response: {activate_resp.text[:500]}")
else:
    print(f"Save error: {save_resp.text[:500]}")

# anything
