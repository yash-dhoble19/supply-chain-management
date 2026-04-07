import requests, json

session = requests.Session()
session.post('https://yash1223456.app.n8n.cloud/rest/login', json={
    'emailOrLdapLoginId': 'yashdhoble6666@gmail.com',
    'password': 'Yash@12345'
})

resp = session.get('https://yash1223456.app.n8n.cloud/rest/executions?limit=10&workflowId=FJogRQZQSNViU8y5')
raw = resp.json()

# Debug the structure
if 'data' in raw and isinstance(raw['data'], dict):
    executions = raw['data'].get('results', [])
elif 'data' in raw and isinstance(raw['data'], list):
    executions = raw['data']
elif 'results' in raw:
    executions = raw['results']
else:
    print("Response keys:", list(raw.keys()))
    print("Raw response (first 500 chars):", json.dumps(raw)[:500])
    executions = []

for ex in executions:
    ex_id = str(ex.get('id', '?'))
    status = ex.get('status', 'unknown')
    mode = ex.get('mode', 'unknown')
    started = str(ex.get('startedAt', 'N/A'))[:19]
    print(f"ID: {ex_id:6s} | Status: {status:12s} | Mode: {mode:12s} | Started: {started}")

# Get details of the most recent failed execution
for ex in executions:
    if ex.get('status') == 'error':
        ex_id = str(ex.get('id'))
        detail = session.get(f'https://yash1223456.app.n8n.cloud/rest/executions/{ex_id}?includeData=true')
        detail_data = detail.json()
        d = detail_data.get('data', detail_data)
        result_data = d.get('data', {}).get('resultData', {})
        last_node = result_data.get('lastNodeExecuted', 'unknown')
        error = result_data.get('error', {})
        print(f"\n--- FAILED EXECUTION {ex_id} ---")
        print(f"Last Node: {last_node}")
        if isinstance(error, dict):
            print(f"Error Message: {error.get('message', 'N/A')}")
        else:
            print(f"Error: {str(error)[:500]}")
        break
