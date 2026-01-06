
import yaml
from typing import Dict

def generate_yaml_metadata(tool_data: Dict, existing_content: str = None) -> str:
    """Generate or update YAML metadata from tool data, preserving extra fields."""
    data = {}
    if existing_content:
        try:
            data = yaml.safe_load(existing_content) or {}
        except Exception:
            data = {}
            
    data['name'] = tool_data.get('name', data.get('name', 'Unnamed Tool'))
    data['description'] = tool_data.get('description', data.get('description', ''))
    
    args_list = []
    tool_args = tool_data.get('arguments', [])
    if tool_args:
        for arg in tool_args:
            args_list.append({
                'name': arg.get('name', 'arg'),
                'type': arg.get('type', 'string'),
                'description': arg.get('description', ''),
                'required': arg.get('required', False)
            })
    data['arguments'] = args_list
    
    if 'docker' in tool_data and tool_data['docker']:
        data['docker'] = {**data.get('docker', {}), **tool_data['docker']}
    
    if 'resources' in tool_data and tool_data['resources']:
        data['resources'] = {**data.get('resources', {}), **tool_data['resources']}
    
    return yaml.dump(data, sort_keys=False, allow_unicode=True)

# Test case: Existing YAML has something, tool_data has new docker config
existing_yaml = """
name: Tool
docker:
  base_image: python:3.9
"""

tool_updates = {
    'docker': {
        'apt_packages': 'nmap'
    }
}

result = generate_yaml_metadata(tool_updates, existing_yaml)
print("Result YAML:")
print(result)

# Test case 2: tool_data has docker AND existing content is empty
result2 = generate_yaml_metadata(tool_updates, "")
print("\nResult 2 YAML:")
print(result2)
