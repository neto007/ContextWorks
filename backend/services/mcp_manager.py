"""
MCP (Model Context Protocol) Manager
Handles high-level logic for MCP servers and API key management.
Triple Check: Modularized - SQL logic moved to core/repositories/mcp_repo.py.
"""
import secrets
import hashlib
from typing import List, Dict, Any, Optional

from core import database
from core.repositories import mcp_repo

def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"mcp_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """Verify an API key against its hash."""
    return hash_api_key(api_key) == api_key_hash

# MCP Server Operations

def create_mcp_server(name: str, description: str, tool_ids: List[str], env_vars: List[Dict[str, Any]] = []) -> Dict[str, Any]:
    mcp_id = f"mcp_{secrets.token_hex(8)}"
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    result = mcp_repo.create_mcp_server(mcp_id, name, description, api_key_hash, tool_ids, env_vars)
    result['api_key'] = api_key # Only shown once
    return result

def get_mcp_server(mcp_id: str) -> Optional[Dict[str, Any]]:
    mcp = mcp_repo.get_mcp_server(mcp_id)
    if mcp:
        mcp['has_logo'] = database.get_logo('mcp', mcp_id) is not None
    return mcp

def list_mcp_servers() -> List[Dict[str, Any]]:
    servers = mcp_repo.list_mcp_servers()
    for s in servers:
        s['has_logo'] = database.get_logo('mcp', s['id']) is not None
    return servers

def update_mcp_server(mcp_id: str, **kwargs) -> bool:
    return mcp_repo.update_mcp_server(mcp_id, kwargs)

def delete_mcp_server(mcp_id: str) -> bool:
    database.delete_logo('mcp', mcp_id)
    return mcp_repo.delete_mcp_server(mcp_id)

def regenerate_api_key(mcp_id: str) -> Optional[str]:
    new_api_key = generate_api_key()
    success = mcp_repo.update_mcp_server(mcp_id, {'api_key_hash': hash_api_key(new_api_key)})
    return new_api_key if success else None

def authenticate_mcp(mcp_id: str, api_key: str) -> bool:
    mcp = mcp_repo.get_mcp_server(mcp_id)
    if not mcp or mcp['status'] != 'active':
        return False
    # We need the hash which is not returned by get_mcp_server by default? 
    # Wait, I should check my mcp_repo.get_mcp_server. It returns * (all columns).
    return verify_api_key(api_key, mcp['api_key_hash'])

# MCP Connection Tracking

def record_connection(mcp_id: str, client_info: str) -> str:
    conn_id = f"conn_{secrets.token_hex(8)}"
    mcp_repo.record_connection(conn_id, mcp_id, client_info)
    return conn_id

def update_connection_ping(connection_id: str):
    mcp_repo.update_connection_ping(connection_id)

def remove_connection(connection_id: str):
    mcp_repo.remove_connection(connection_id)

def get_active_connections(mcp_id: str) -> List[Dict[str, Any]]:
    return mcp_repo.get_active_connections(mcp_id)

# Logo Management (Now unified in DB)

def save_mcp_logo(mcp_id: str, svg_content: str):
    database.save_logo('mcp', mcp_id, svg_content)

def get_mcp_logo(mcp_id: str) -> Optional[str]:
    return database.get_logo('mcp', mcp_id)
