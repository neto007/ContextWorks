#!/usr/bin/env python3
"""
Full Migration Script: Move workspaces, tools, scripts, and logos from filesystem to PostgreSQL.
"""
import os
import sys
import yaml
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import database
from services import tool_service as tool_manager

def migrate_everything():
    print("🚀 Starting FULL platform migration to database...")
    
    # 1. Reset cache
    tool_manager.list_categories.cache_clear()
    
    # Get all categories from FS (since DB might be empty)
    fs_categories = []
    base_dir = Path(tool_manager.TOOLS_BASE_DIR)
    
    if not base_dir.exists():
        print(f"❌ Base directory not found: {base_dir}")
        return

    print(f"\n📁 Scanning Workspaces in {base_dir}...")
    for entry in os.listdir(base_dir):
        cat_path = base_dir / entry
        if cat_path.is_dir() and not entry.startswith('.') and not entry.startswith('_'):
            print(f"  ✨ Found workspace: {entry}")
            
            # Read description from workspace.yaml
            description = ""
            meta_path = cat_path / "workspace.yaml"
            if meta_path.exists():
                try:
                    with open(meta_path, 'r') as f:
                        data = yaml.safe_load(f)
                        description = data.get('description', '')
                except: pass
            
            # 1. Save Workspace to DB
            database.save_workspace(entry, description)
            print(f"    ✅ Workspace '{entry}' saved to DB.")

            # 2. Check for Workspace Logo
            logo_path = cat_path / "logo.svg"
            if logo_path.exists():
                try:
                    with open(logo_path, 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                    database.save_logo('workspace', entry, svg_content)
                    print(f"    ✅ Workspace logo migrated: {entry}")
                except Exception as e:
                    print(f"    ❌ Failed to migrate workspace logo {entry}: {e}")

            # 3. Scan Tools in this Workspace
            print(f"    🔍 Scanning tools in {entry}...")
            for tool_file in os.listdir(cat_path):
                if tool_file.endswith('.py') and not tool_file.startswith('__'):
                    tool_id = tool_file.replace('.py', '')
                    full_tool_id = f"{entry}/{tool_id}"
                    script_path = cat_path / tool_file
                    yaml_path = cat_path / f"{tool_id}.script.yaml"
                    
                    print(f"      🔹 Found tool: {full_tool_id}")
                    
                    try:
                        # Read script code
                        with open(script_path, 'r', encoding='utf-8') as f:
                            script_code = f.read()
                        
                        # Read metadata
                        name = tool_id.replace('_', ' ').title()
                        description = ""
                        arguments = []
                        
                        if yaml_path.exists():
                            try:
                                with open(yaml_path, 'r', encoding='utf-8') as f:
                                    meta_data = yaml.safe_load(f)
                                    name = meta_data.get('name', name)
                                    description = meta_data.get('description', '')
                                    arguments = meta_data.get('arguments', [])
                            except: pass
                        
                        # Save Tool to DB
                        database.save_tool(full_tool_id, name, entry, script_code, arguments, description)
                        print(f"      ✅ Tool '{full_tool_id}' saved to DB.")
                        
                        # Check for Tool Logo
                        tool_logo_path = cat_path / f"{tool_id}.logo.svg"
                        if tool_logo_path.exists():
                            try:
                                with open(tool_logo_path, 'r', encoding='utf-8') as f:
                                    tool_svg = f.read()
                                database.save_logo('tool', full_tool_id, tool_svg)
                                print(f"      ✅ Tool logo migrated: {full_tool_id}")
                            except: pass
                            
                    except Exception as e:
                        print(f"      ❌ Failed to migrate tool {full_tool_id}: {e}")

    print("\n✅ FULL Migration complete!")

if __name__ == "__main__":
    try:
        migrate_everything()
    except Exception as e:
        print(f"💥 Migration failed: {e}")
        sys.exit(1)
