from datetime import datetime
from typing import Optional
from core.db_base import get_db_connection

def save_logo(entity_type: str, entity_id: str, svg_content: str):
    """Save or update a logo in the database."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO logos (entity_type, entity_id, svg_content, updated_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (entity_type, entity_id) 
            DO UPDATE SET svg_content = EXCLUDED.svg_content, updated_at = EXCLUDED.updated_at
        ''', (entity_type, entity_id, svg_content, datetime.utcnow().isoformat()))
        conn.commit()
    finally:
        conn.close()

def get_logo(entity_type: str, entity_id: str) -> Optional[str]:
    """Get a logo from the database."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT svg_content FROM logos WHERE entity_type = %s AND entity_id = %s', 
                 (entity_type, entity_id))
        row = c.fetchone()
        if row:
            return row[0]
        return None
    finally:
        conn.close()

def delete_logo(entity_type: str, entity_id: str):
    """Delete a logo from the database."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('DELETE FROM logos WHERE entity_type = %s AND entity_id = %s', 
                 (entity_type, entity_id))
        conn.commit()
    finally:
        conn.close()
