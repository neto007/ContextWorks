from datetime import datetime
from typing import List, Dict, Optional
import psycopg2.extras
from core.db_base import get_db_connection

def save_workspace(name: str, description: str = "", is_visible: bool = True):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO workspaces (name, description, is_visible, created_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET 
                description = EXCLUDED.description,
                is_visible = EXCLUDED.is_visible
        ''', (name, description, is_visible, datetime.utcnow().isoformat()))
        conn.commit()
    finally:
        conn.close()

def get_workspaces() -> List[Dict]:
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM workspaces ORDER BY name ASC')
        rows = c.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_workspace(name: str) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM workspaces WHERE name = %s', (name,))
        row = c.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def delete_workspace(name: str):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('DELETE FROM workspaces WHERE name = %s', (name,))
        conn.commit()
    finally:
        conn.close()
