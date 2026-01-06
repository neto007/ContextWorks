import json
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2.extras
from core.db_base import get_db_connection

def save_tool(tool_id: str, name: str, category: str, script_code: str, arguments: List[Dict] = None, description: str = "", configuration: str = ""):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute('''
            INSERT INTO tools (id, name, category, script_code, arguments, description, configuration, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET 
                name = EXCLUDED.name,
                script_code = EXCLUDED.script_code,
                arguments = EXCLUDED.arguments,
                description = EXCLUDED.description,
                configuration = EXCLUDED.configuration,
                updated_at = EXCLUDED.updated_at
        ''', (tool_id, name, category, script_code, json.dumps(arguments) if arguments else "[]", description, configuration, now, now))
        conn.commit()
    finally:
        conn.close()

def get_all_tools() -> List[Dict]:
    from pathlib import Path
    from config import settings
    
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # Efficiently check for logo existence via LEFT JOIN
        query = '''
            SELECT t.*, 
                   CASE WHEN l.entity_id IS NOT NULL THEN true ELSE false END as has_logo 
            FROM tools t 
            LEFT JOIN logos l ON l.entity_type = 'tool' AND l.entity_id = t.id 
            ORDER BY t.category ASC, t.name ASC
        '''
        c.execute(query)
        rows = c.fetchall()
        tools = []
        for row in rows:
            res = dict(row)
            if res.get('arguments') and isinstance(res['arguments'], str):
                try:
                    res['arguments'] = json.loads(res['arguments'])
                except:
                    res['arguments'] = []
            
            # has_logo is now returned by the query
            
            tools.append(res)
        return tools
    finally:
        conn.close()

def get_tool(tool_id: str) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM tools WHERE id = %s', (tool_id,))
        row = c.fetchone()
        if row:
            res = dict(row)
            if res.get('arguments'):
                res['arguments'] = json.loads(res['arguments'])
            return res
        return None
    finally:
        conn.close()

def delete_tool(tool_id: str):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('DELETE FROM tools WHERE id = %s', (tool_id,))
        conn.commit()
    finally:
        conn.close()

def get_tools_count_by_category(category: str) -> int:
    """Get count of tools in a category efficiently."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM tools WHERE category = %s",
            (category,)
        )
        count = cursor.fetchone()[0]
        return count
    finally:
        cursor.close()
        conn.close()
