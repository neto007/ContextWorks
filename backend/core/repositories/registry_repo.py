from datetime import datetime
from typing import Dict, Optional
import psycopg2.extras
from core.db_base import get_db_connection

def save_registry_config(config: Dict) -> Dict:
    """Save or update registry configuration"""
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        now = datetime.utcnow().isoformat()
        
        # Check if config exists
        c.execute('SELECT id FROM registry_config LIMIT 1')
        existing = c.fetchone()
        
        if existing:
            # Update existing
            c.execute('''
                UPDATE registry_config SET
                    type = %s,
                    url = %s,
                    username = %s,
                    password = %s,
                    namespace = %s,
                    use_local_fallback = %s,
                    updated_at = %s
                WHERE id = %s
            ''', (
                config.get('type', 'local'),
                config.get('url'),
                config.get('username'),
                config.get('password'),
                config.get('namespace'),
                config.get('use_local_fallback', True),
                now,
                existing['id']
            ))
        else:
            # Insert new
            c.execute('''
                INSERT INTO registry_config (type, url, username, password, namespace, use_local_fallback, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                config.get('type', 'local'),
                config.get('url'),
                config.get('username'),
                config.get('password'),
                config.get('namespace'),
                config.get('use_local_fallback', True),
                now,
                now
            ))
        
        conn.commit()
        
        # Return saved config
        c.execute('SELECT * FROM registry_config LIMIT 1')
        row = c.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def get_registry_config() -> Optional[Dict]:
    """Get current registry configuration"""
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM registry_config LIMIT 1')
        row = c.fetchone()
        if row:
            return dict(row)
        # Return default local config if none exists
        return {
            'type': 'local',
            'use_local_fallback': True
        }
    finally:
        conn.close()
