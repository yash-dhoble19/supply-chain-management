import json
import ast
import re

def json_to_ts_string(obj, indent=2):
    """Convert JSON block into TS exact code string"""
    if isinstance(obj, dict):
        lines = ["{"]
        for k, v in obj.items():
            key = f"'{k}'" if '-' in k or ' ' in k or ':' in k else k
            lines.append(f"{' '*(indent)}{key}: {json_to_ts_string(v, indent+2)},")
        lines.append(f"{' '*(indent-2)}}}")
        return "\n".join(lines)
    elif isinstance(obj, list):
        lines = ["["]
        for v in obj:
            lines.append(f"{' '*indent}{json_to_ts_string(v, indent+2)},")
        lines.append(f"{' '*(indent-2)}]")
        return "\n".join(lines)
    elif isinstance(obj, bool):
        return "true" if obj else "false"
    elif obj is None:
        return "null"
    elif isinstance(obj, (int, float)):
        return str(obj)
    else:
        return json.dumps(str(obj))

def convert_workflow():
    with open('output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("Read workflow JSON")
    workflow = data.get('workflow', {})
    nodes = workflow.get('nodes', [])
    connections = workflow.get('connections', {})
    
    ts_code = [
        "import { workflow, node, trigger } from '@n8n/workflow-sdk';",
        ""
    ]
    node_vars = {}
    for i, n in enumerate(nodes):
        node_varName = re.sub(r'[^a-zA-Z0-9]', '', n['name'])
        node_varName = node_varName[0].lower() + node_varName[1:]
        node_vars[n['name']] = node_varName
        
        # FIX THE GMAIL NODES HERE
        if n['type'] == 'n8n-nodes-base.gmail':
            if 'parameters' not in n:
                n['parameters'] = {}
            n['parameters']['resource'] = 'message'
            n['parameters']['operation'] = 'send'
            
        is_trigger = "trigger" in n['type'].lower() or n['type'] == 'n8n-nodes-base.webhook'
        creator = "trigger" if is_trigger else "node"
        
        cfg = {"name": n['name']}
        if 'parameters' in n: cfg['parameters'] = n['parameters']
        if 'position' in n: cfg['position'] = n['position']
        
        ts_code.append(f"const {node_varName} = {creator}({{")
        ts_code.append(f"  id: '{n['id']}',")
        ts_code.append(f"  type: '{n['type']}',")
        ts_code.append(f"  version: {n['typeVersion']},")
        ts_code.append(f"  config: {json_to_ts_string(cfg, 4)}")
        ts_code.append(f"}});")
        ts_code.append("")
    
    ts_code.append(f"export default workflow('{workflow['id']}', '{workflow['name']}')")
    
    # Process connections
    # connections is { "NodeA": { "main": [ [ {"node": "NodeB", "type": "main", "index": 0} ] ] } }
    # Let's just track the roots and use .to()
    visited_connections = set()
    for source_name, output_types in connections.items():
        for output_type, links in output_types.items():
            for target_list in links:
                for target in target_list:
                    target_name = target['node']
                    # naive sequential connection
                    if source_name in node_vars and target_name in node_vars:
                        ts_code.append(f"  .add({node_vars[source_name]}).to({node_vars[target_name]})")

    ts_code.append(";")
    with open('workflow_script.ts', 'w', encoding='utf-8') as f:
        f.write("\n".join(ts_code))
    print("Generated workflow_script.ts")

if __name__ == '__main__':
    convert_workflow()

# anything
