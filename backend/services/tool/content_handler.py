import json
import yaml
from typing import Dict, Optional
from core import database
from core.logger import logger

def is_docker_config_changed(new_config: Dict, existing_config: Optional[Dict]) -> bool:
    """Compara se as mudanças na configuração Docker justificam um novo build."""
    if not existing_config:
        return True
        
    # Extrair campos relevantes que afetam a construção da imagem Docker
    # IGNORAR: resources (CPU/memory não afetam a imagem!)
    new_mode = new_config.get('docker_mode')
    old_mode = existing_config.get('docker_mode')
    
    # Apenas comparar image se for PRÉ-EXISTENTE (não auto-gerado)
    new_image = new_config.get('image', '')
    old_image = existing_config.get('image', '')
    
    # Ignorar images auto-geradas que começam com 'security-platform-tool-'
    if (new_image and new_image.startswith('security-platform-tool-')) or \
       (old_image and old_image.startswith('security-platform-tool-')):
        new_image = None
        old_image = None
    
    new_base = new_config.get('base_image')
    old_base = existing_config.get('base_image')
    
    new_apt = sorted(new_config.get('apt_packages', []))
    old_apt = sorted(existing_config.get('apt_packages', []))
    
    new_pip = sorted(new_config.get('pip_packages', []))
    old_pip = sorted(existing_config.get('pip_packages', []))
    
    changed = (
        new_mode != old_mode or
        new_image != old_image or
        new_base != old_base or
        new_apt != old_apt or
        new_pip != old_pip
    )
    
    if changed:
        logger.debug("Docker config changed", extra={"extra_fields": {
            "mode": f"{old_mode} -> {new_mode}",
            "base": f"{old_base} -> {new_base}",
            "apt": f"{old_apt} -> {new_apt}",
            "pip": f"{old_pip} -> {new_pip}"
        }})
        
    return changed

def get_default_script_template(tool_name: str) -> str:
    """Generate a default Python script template."""
    return f'''#!/usr/bin/env python3
"""
{tool_name}
Auto-generated security tool
"""
import sys
import json

def main(args):
    """Main execution function."""
    # TODO: Implement tool logic here
    
    result = {{
        "status": "success",
        "message": "Tool executed successfully",
        "data": {{}}
    }}
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {{}}
    
    try:
        main(args)
    except Exception as e:
        error_result = {{
            "status": "error",
            "message": str(e)
        }}
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
'''

def resolve_tool_id_from_path(path: str) -> Optional[str]:
    """Infers tool ID from a virtual filesystem path."""
    if not path or '/' not in path:
        return None
    
    parts = path.split('/')
    if len(parts) >= 2:
        raw_id = f"{parts[-2]}/{parts[-1]}"
        return raw_id.replace('.py', '').replace('.yaml', '').replace('.yml', '')
    return None

def get_tool_content(target_id: str, file_type: str = "py", path: str = None) -> str:
    """Reads script or configuration content from DB."""
    tool = database.get_tool(target_id)
    if not tool:
        raise ValueError(f"Tool '{target_id}' not found")

    if file_type == "py" or (path and path.endswith('.py')):
        return tool['script_code']
    
    elif file_type == "yaml" or (path and (path.endswith('.yaml') or path.endswith('.yml'))):
        if tool.get('configuration'):
            return tool['configuration']
        return generate_yaml_metadata(tool)
    
    raise ValueError(f"Invalid file type: {file_type}")

def save_tool_content(target_id: str, content: str, path: str) -> bool:
    """Saves script or configuration content to DB. Returns True if content actually changed."""
    tool = database.get_tool(target_id)
    if not tool:
        # UPSERT LOGIC: Create tool if it doesn't exist
        # We need path to extract category and name
        if not path:
             raise ValueError(f"Tool '{target_id}' not found and no path provided to create it.")
             
        parts = path.split('/')
        if len(parts) < 2:
             raise ValueError(f"Cannot infer category/name from path '{path}'")
             
        # Normalize category/id
        category = parts[0]
        # ID is usually parts[-1] without extension
        raw_id = parts[-1].replace('.py', '').replace('.yaml', '').replace('.yml', '')
        
        # Make sure target_id matches what we inferred, or use target_id as source of truth if path is partial
        # But we trust target_id (e.g. "Network/nmap_scan")
        
        # Determine tool name - Default to ID formatted nicely
        tool_name = raw_id.replace('_', ' ').title()
        full_id = target_id
        
        # Create stub tool
        database.save_tool(
            full_id, tool_name, category, 
            get_default_script_template(tool_name), [], "Auto-created via sync", ""
        )
        tool = database.get_tool(target_id)
        
    category = tool['category']
    full_id = tool['id']
    
    if path and path.endswith('.py'):
        changed = content != tool['script_code']
        if changed:
            database.save_tool(
                full_id, tool['name'], category, 
                content, tool['arguments'], tool.get('description', ""),
                tool.get('configuration', "")
            )
        return changed
        
    elif path and (path.endswith('.yaml') or path.endswith('.yml')):
        try:
            metadata = yaml.safe_load(content) or {}
            
            # Detecção de mudanças granulares para YAML
            existing_config = {}
            if tool.get('configuration'):
                try:
                    existing_config = yaml.safe_load(tool['configuration']) or {}
                except: pass
            
            # 1. Verificar se a configuração Docker mudou
            docker_changed = is_docker_config_changed(
                metadata.get('docker', {}), 
                existing_config.get('docker', {})
            )
            
            # 2. Verificar metadados gerais (apenas para persistência, mas docker_changed é o que manda pro build)
            # No entanto, a CLI quer saber se "algo mudou que justifique build"
            # Na verdade, a CLI quer saber se o arquivo mudou.
            # Se mudou apenas a descrição, changed=True mas talvez não disparemos build?
            # Melhor: changed=True se o conteúdo for diferente. 
            # A CLI decidirá se builda baseado nisso por enquanto.
            
            content_changed = content != tool.get('configuration', "")
            
            if content_changed:
                args = []
                if 'schema' in metadata and 'properties' in metadata['schema']:
                    for arg_name, arg_def in metadata['schema']['properties'].items():
                        args.append({
                            'name': arg_name,
                            'type': arg_def.get('type', 'string'),
                            'description': arg_def.get('description', ''),
                            'required': arg_name in metadata['schema'].get('required', []),
                            'default': arg_def.get('default', '')
                        })
                
                # Fallback para arguments (legacy)
                if not args and 'arguments' in metadata:
                    args = metadata['arguments']

                # Ensure workspace exists before saving tool (Upsert Category)
                existing_ws = database.get_workspace(category)
                if not existing_ws:
                    database.save_workspace(category, "")
                    
                database.save_tool(
                    full_id, metadata.get('name', tool['name']), category,
                    tool['script_code'], args, metadata.get('description', tool.get('description', "")),
                    content
                )
            
            # Retornamos True se houver mudança no conteúdo. 
            # Mas podemos ser mais espertos e diferenciar mudança de build vs mudança de metadados.
            # Por simplicidade da CLI hoje: retornamos True se mudou.
            return content_changed
        except Exception as e:
            raise ValueError(f"Invalid YAML format or DB error: {str(e)}")
    else:
        raise ValueError("Could not determine file type from path")

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
    
    if 'docker' in tool_data and tool_data.get('docker') is not None:
        data['docker'] = {**data.get('docker', {}), **tool_data['docker']}
    
    if 'resources' in tool_data and tool_data.get('resources') is not None:
        data['resources'] = {**data.get('resources', {}), **tool_data['resources']}
    
    return yaml.dump(data, sort_keys=False, allow_unicode=True)
