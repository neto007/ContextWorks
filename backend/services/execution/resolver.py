import yaml
from typing import Dict, Any, Union
from core import database, utils
from core.logger import logger

def resolve_tool(tool_identifier: str) -> Dict[str, Any]:
    """
    Resolves a tool identifier (ID or Path) to a Database Tool Object.
    """
    tool_id = tool_identifier
    
    if '/' in tool_identifier:
        parts = tool_identifier.split('/')
        if len(parts) >= 2:
            potential_id = f"{parts[-2]}/{parts[-1]}".replace('.py', '')
            tool = database.get_tool(potential_id)
            if tool:
                return tool
    
    tool = database.get_tool(tool_id)
    if tool:
        return tool

    if tool_id.endswith('.py'):
        tool = database.get_tool(tool_id[:-3])
        if tool:
            return tool
            
    raise FileNotFoundError(f"Tool not found in database: {tool_identifier}")

def get_tool_config_from_data(tool_data: Dict[str, Any]) -> dict:
    """
    Determines Docker image and K8s resources from Tool DB Data.
    """
    # Use id as priority for tags as it is the unique file/folder identifier
    # Use id as priority for tags as it is the unique file/folder identifier
    tool_id = tool_data.get('id', tool_data.get('name', 'tool'))
    tool_name = tool_data.get('name', 'tool')
    
    is_adhoc_test = tool_name in ['test-tool', 'adhoc-tool'] and not tool_data.get('configuration')
    safe_name = utils.sanitize_k8s_name(tool_id)
    
    # Authoritative tag generation
    authoritative_tag = utils.generate_image_tag(tool_id)
    
    default_config = {
        "image": "python:3.11-slim" if is_adhoc_test else authoritative_tag,
        "resources": {
            "requests": {"cpu": "100m", "memory": "256Mi"},
            "limits": {"cpu": "1000m", "memory": "1024Mi"}
        }
    }
    
    config_yaml = tool_data.get('configuration', '')
    metadata = {}
    if config_yaml:
        try:
            metadata = yaml.safe_load(config_yaml) or {}
        except Exception as e:
            logger.warning("Error parsing tool configuration YAML", exc_info=True, extra={"extra_fields": {"tool_id": tool_id}})

    docker_config = metadata.get('docker', {})
    resource_config = metadata.get('resources', {})
    config = default_config.copy()
    
    custom_tag = authoritative_tag
    
    if 'image' in docker_config and docker_config['image']:
        # Only allow explicit image override (e.g. for external tools)
        config["image"] = docker_config['image']
    else:
        # ALWAYS use authoritative tag for our internal tools
        # base_image is for BUILD time (FROM python...) not execution time
        config["image"] = "python:3.11-slim" if is_adhoc_test else authoritative_tag

    if resource_config:
        if 'requests' in resource_config:
            config["resources"]["requests"].update(resource_config['requests'])
        if 'limits' in resource_config:
            config["resources"]["limits"].update(resource_config['limits'])
            
    logger.info("Resolved tool configuration", extra={"extra_fields": {"tool_name": tool_name, "image": config["image"]}})
    return config
