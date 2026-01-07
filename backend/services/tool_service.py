import os
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from functools import lru_cache

from core import database
from core.logger import logger
from config import settings

# Modular imports
from .tool.content_handler import (
    get_default_script_template, 
    resolve_tool_id_from_path,
    get_tool_content,
    save_tool_content as _save_tool_content_impl,
    generate_yaml_metadata
)

def save_tool_content(target_id: str, content: str, path: str) -> bool:
    """Wrapper to save content and clear cache. Returns True if changed."""
    changed = _save_tool_content_impl(target_id, content, path)
    if changed:
        scan_tools.cache_clear()
    return changed

TOOLS_BASE_DIR = settings.TOOLS_BASE_DIR

# ============================================================================
# SCANNER FUNCTIONALITY
# ============================================================================

@lru_cache(maxsize=1)
def scan_tools() -> Dict[str, List[Dict]]:
    """Scans tools from database ONLY."""
    tools = database.get_all_tools()
    result = {}
    for tool in tools:
        cat = tool['category']
        if cat not in result:
            result[cat] = []
        result[cat].append(tool)
    return result

# ============================================================================
# CATEGORY MANAGEMENT
# ============================================================================

def list_categories() -> List[Dict]:
    """List all available categories (workspaces) from database ONLY."""
    categories = database.get_workspaces()
    result = []
    for cat in categories:
        cat_name = cat['name']
        tool_count = database.get_tools_count_by_category(cat_name)
        result.append({
            "name": cat_name,
            "path": os.path.join(TOOLS_BASE_DIR, cat_name),
            "tool_count": tool_count,
            "description": cat.get('description', ''),
            "is_visible": cat.get('is_visible', True),
            "has_logo": database.get_logo('category', cat_name) is not None
        })
    return result

def create_category(category_name: str, description: str = ""):
    database.save_workspace(category_name, description)
    scan_tools.cache_clear()
    return True

def update_category(old_name: str, new_name: str = None, description: str = None, is_visible: bool = None):
    # Rename is slightly complex as it affects all tools
    # Currently we only support description update or simple name update if no tools exist
    
    # Get existing to preserve values if not provided
    existing = database.get_workspace(old_name)
    if not existing:
        return False
        
    final_is_visible = is_visible if is_visible is not None else existing.get('is_visible', True)
    final_description = description if description is not None else existing.get('description', '')
    final_name = new_name if new_name else old_name

    database.save_workspace(final_name, final_description, final_is_visible)
    scan_tools.cache_clear()
    return True

def delete_category(name: str):
    database.delete_workspace(name)
    database.delete_logo('category', name)
    scan_tools.cache_clear()
    return True

# ============================================================================
# LOGO MANAGEMENT
# ============================================================================

def save_category_logo(category_name: str, svg_content: str):
    database.save_logo('category', category_name, svg_content)

def get_category_logo(category_name: str):
    return database.get_logo('category', category_name)

def save_tool_logo(category_name: str, tool_name: str, svg_content: str):
    database.save_logo('tool', f"{category_name}/{tool_name}", svg_content)

def get_tool_logo(category_name: str, tool_name: str):
    return database.get_logo('tool', f"{category_name}/{tool_name}")

# ============================================================================
# TOOL CRUD
# ============================================================================

def create_tool(category: str, tool_data: Dict) -> Dict:
    tool_id = tool_data['name'].replace(' ', '_').lower()
    full_id = f"{category}/{tool_id}"
    
    script_code = tool_data.get('script_code') or get_default_script_template(tool_data['name'])
    arguments = tool_data.get('arguments', [])
    description = tool_data.get('description', '')
    yaml_content = generate_yaml_metadata(tool_data)
    logger.debug("Generating tool metadata", extra={"extra_fields": {"tool_name": tool_data['name'], "category": category}})

    database.save_tool(full_id, tool_data['name'], category, script_code, arguments, description, yaml_content)
    
    # Trigger Async Build
    build_result = None
    docker_config = tool_data.get('docker')
    logger.debug("Initiating tool build check", extra={"extra_fields": {"tool_id": tool_id, "has_docker": bool(docker_config)}})
    if docker_config:
        try:
            from services.docker_build_service import should_build_image, trigger_build_async
            if should_build_image(docker_config):
                logger.info("Triggering async Docker build", extra={"extra_fields": {"tool_id": tool_id, "category": category}})
                job_id = trigger_build_async(category, tool_id, docker_config)
                build_result = {"status": "pending", "job_id": job_id, "message": "Build started in background"}
            else:
                logger.info("should_build_image returned False", extra={"extra_fields": {"tool_id": tool_id}})
        except Exception as e:
            logger.error("Error during Docker build", exc_info=True, extra={"extra_fields": {"tool_id": tool_id}})
    
    scan_tools.cache_clear()
    
    return expand_tool_config({
        "id": tool_id,
        "name": tool_data['name'],
        "category": category,
        "script_code": script_code,
        "arguments": arguments,
        "description": description,
        "configuration": yaml_content,
        "build_result": build_result,
        "created_at": datetime.now().isoformat()
    })

def expand_tool_config(tool: Dict) -> Dict:
    """Helper to parse configuration YAML and add structured fields to tool dict."""
    if not tool or not tool.get('configuration'):
        return tool
        
    try:
        config = yaml.safe_load(tool['configuration']) or {}
        if 'docker' in config:
            tool['docker'] = config['docker']
        if 'resources' in config:
            tool['resources'] = config['resources']
            
        # Ensure docker_mode is available for frontend
        if 'docker' in tool:
            if 'docker_mode' not in tool['docker']:
                # Infer mode if missing
                if tool['docker'].get('image') and not tool['docker']['image'].startswith("security-platform-tool-"):
                    tool['docker']['docker_mode'] = 'preexisting'
                elif any(k in tool['docker'] for k in ['apt_packages', 'pip_packages']):
                    tool['docker']['docker_mode'] = 'custom'
                else:
                    tool['docker']['docker_mode'] = 'auto'
    except Exception as e:
        logger.error("Error expanding tool config", exc_info=True, extra={"extra_fields": {"tool_id": tool.get('id')}})
        
    return tool

def update_tool(category: str, tool_id: str, tool_data: Dict) -> Dict:
    full_id = f"{category}/{tool_id}"
    existing = database.get_tool(full_id)
    if not existing:
        raise ValueError(f"Tool '{tool_id}' not found in DB")
    
    name = tool_data.get('name', existing['name'])
    script_code = tool_data.get('script_code', existing.get('script_code', ''))
    arguments = tool_data.get('arguments', existing.get('arguments', []))
    description = tool_data.get('description', existing.get('description', ''))
    
    # DETECÇÃO INTELIGENTE: Verificar se houve mudanças relevantes que justificam build
    script_changed = script_code != existing.get('script_code', '')
    docker_changed = False
    
    docker_config = tool_data.get('docker')
    if docker_config:
        # Carregar configuração Docker existente do YAML
        existing_docker = {}
        try:
            if existing.get('configuration'):
                config = yaml.safe_load(existing['configuration']) or {}
                existing_docker = config.get('docker', {})
        except: pass
        
        from .tool.content_handler import is_docker_config_changed
        docker_changed = is_docker_config_changed(docker_config, existing_docker)
    
    logger.debug("Analyzing tool changes", extra={"extra_fields": {
        "tool_id": tool_id,
        "category": category,
        "script_changed": script_changed,
        "docker_changed": docker_changed
    }})
    
    yaml_content = generate_yaml_metadata({**existing, **tool_data}, existing.get('configuration') or "")
    database.save_tool(full_id, name, category, script_code, arguments, description, yaml_content)
    
    build_result = None
    
    # APENAS disparar build se código OU configuração Docker mudaram
    if docker_config and (script_changed or docker_changed):
        try:
            from services.docker_build_service import should_build_image, trigger_build_async
            if should_build_image(docker_config):
                logger.info("Triggering async Docker build on update", extra={"extra_fields": {
                    "tool_id": tool_id,
                    "reason": "script_changed" if script_changed else "docker_config_changed"
                }})
                job_id = trigger_build_async(category, tool_id, docker_config)
                build_result = {"status": "pending", "job_id": job_id, "message": "Build started in background"}
            else:
                logger.debug("Skipping docker build", extra={"extra_fields": {
                    "tool_id": tool_id,
                    "reason": "should_build_image returned False"
                }})
        except Exception as e:
            logger.error("Error triggering docker build on update", exc_info=True, extra={"extra_fields": {"tool_id": tool_id}})
    else:
        logger.info("Skipping build: only metadata changed", extra={"extra_fields": {
            "tool_id": tool_id,
            "script_changed": script_changed,
            "docker_changed": docker_changed,
            "has_docker_config": bool(docker_config)
        }})
            
    scan_tools.cache_clear()
    result = database.get_tool(full_id)
    if build_result:
        result['build_result'] = build_result
    return expand_tool_config(result)

def delete_tool(category: str, tool_id: str) -> bool:
    full_id = f"{category}/{tool_id}"
    database.delete_tool(full_id)
    database.delete_logo('tool', full_id)
    scan_tools.cache_clear()
    return True
