import requests
import json
import sys

URL = "https://yash1223456.app.n8n.cloud"
EMAIL = "yashdhoble6666@gmail.com"
PASSWORD = "Yash@12345"

session = requests.Session()

# 1. Login
login_payload = {
    "email": EMAIL,
    "password": PASSWORD
}
res = session.post(f"{URL}/rest/login", json=login_payload)
if res.status_code != 200:
    print(f"Login failed: {res.status_code} {res.text}")
    sys.exit(1)

auth_data = res.json()
print("Logged in successfully.")

# Add auth headers
session.headers.update({
    "cookie": f"n8n-auth={auth_data.get('data', {}).get('token', '')}"
})

# Or maybe it uses the token directly in the auth header if cookie isn't primary
if 'data' in auth_data and 'token' in auth_data['data']:
    token = auth_data['data']['token']
    session.headers.update({"cookie": f"n8n-auth={token}"})

# 2. Fetch Workflow
workflow_id = "FJogRQZQSNViU8y5" # From previous search
res = session.get(f"{URL}/rest/workflows/{workflow_id}")
if res.status_code != 200:
    print(f"Failed to fetch workflow: {res.status_code} {res.text}")
    sys.exit(1)

workflow_data = res.json()
if 'data' in workflow_data:
    workflow_data = workflow_data['data']

print(f"Fetched workflow '{workflow_data.get('name')}'")

# 3. Modify Gmail nodes
updated_nodes = []
changes_made = 0
for node in workflow_data.get('nodes', []):
    if node.get('type') == 'n8n-nodes-base.gmail':
        if 'parameters' not in node:
            node['parameters'] = {}
        node['parameters']['resource'] = 'message'
        node['parameters']['operation'] = 'send'
        print(f"Fixed parameters for node: {node.get('name')}")
        changes_made += 1
    updated_nodes.append(node)

workflow_data['nodes'] = updated_nodes

if changes_made == 0:
    print("No Gmail nodes needed fixing (or not found).")
    sys.exit(0)

# 4. Upload modified workflow
res = session.put(f"{URL}/rest/workflows/{workflow_id}", json=workflow_data)
if res.status_code != 200:
    print(f"Failed to update workflow: {res.status_code} {res.text}")
    sys.exit(1)

print("Workflow successfully updated via raw JSON update!")

# anything
