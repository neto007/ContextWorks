import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import psycopg2.extras
from core.db_base import get_db_connection

def create_mcp_server(mcp_id: str, name: str, description: str, api_key_hash: str, tool_ids: List[str], env_vars: List[Dict[str, Any]] = []) -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute('''
            INSERT INTO mcp_servers (id, name, description, api_key_hash, tool_ids, env_vars, created_at, updated_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (mcp_id, name, description, api_key_hash, json.dumps(tool_ids), json.dumps(env_vars), now, now, 'active'))
        conn.commit()
        return {
            'id': mcp_id, 'name': name, 'description': description,
            'tool_ids': tool_ids, 'env_vars': env_vars, 'created_at': now, 'status': 'active'
        }
    finally:
        conn.close()

def get_mcp_server(mcp_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM mcp_servers WHERE id = %s', (mcp_id,))
        row = cursor.fetchone()
        if not row: return None
        res = dict(row)
        res['tool_ids'] = json.loads(res['tool_ids']) if res['tool_ids'] else []
        res['env_vars'] = json.loads(res.get('env_vars') or '[]')
        return res
    finally:
        conn.close()

def list_mcp_servers() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM mcp_servers ORDER BY created_at DESC')
        rows = cursor.fetchall()
        servers = []
        for row in rows:
            res = dict(row)
            res['tool_ids'] = json.loads(res['tool_ids']) if res['tool_ids'] else []
            res['env_vars'] = json.loads(res.get('env_vars') or '[]')
            servers.append(res)
        return servers
    finally:
        conn.close()

def update_mcp_server(mcp_id: str, update_data: Dict[str, Any]) -> bool:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        updates = []
        params = []
        for key, value in update_data.items():
            if key in ['name', 'description', 'status']:
                updates.append(f"{key} = %s")
                params.append(value)
            elif key == 'tool_ids':
                updates.append("tool_ids = %s")
                params.append(json.dumps(value))
            elif key == 'env_vars':
                updates.append("env_vars = %s")
                params.append(json.dumps(value))
            elif key == 'api_key_hash':
                updates.append("api_key_hash = %s")
                params.append(value)
        
        if not updates: return False
        updates.append("updated_at = %s")
        params.append(datetime.utcnow().isoformat())
        params.append(mcp_id)
        
        query = f"UPDATE mcp_servers SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)
        success = cursor.rowcount > 0
        conn.commit()
        return success
    finally:
        conn.close()

def delete_mcp_server(mcp_id: str) -> bool:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM mcp_servers WHERE id = %s', (mcp_id,))
        success = cursor.rowcount > 0
        conn.commit()
        return success
    finally:
        conn.close()

def record_connection(connection_id: str, mcp_id: str, client_info: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute('''
            INSERT INTO mcp_connections (id, mcp_id, client_info, connected_at, last_ping)
            VALUES (%s, %s, %s, %s, %s)
        ''', (connection_id, mcp_id, client_info, now, now))
        conn.commit()
    finally:
        conn.close()

def update_connection_ping(connection_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE mcp_connections SET last_ping = %s WHERE id = %s', 
                     (datetime.utcnow().isoformat(), connection_id))
        conn.commit()
    finally:
        conn.close()

def remove_connection(connection_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM mcp_connections WHERE id = %s', (connection_id,))
        conn.commit()
    finally:
        conn.close()

def get_active_connections(mcp_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM mcp_connections WHERE mcp_id = %s ORDER BY connected_at DESC', (mcp_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
