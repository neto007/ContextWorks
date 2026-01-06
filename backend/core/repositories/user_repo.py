from datetime import datetime
from typing import Dict, Optional
import psycopg2
import psycopg2.extras
from core.db_base import get_db_connection

def create_user(user_id: str, email: str, hashed_password: str, full_name: str = None):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (id, email, hashed_password, full_name, created_at)
            VALUES (%s, %s, %s, %s, %s)
        ''', (
            user_id,
            email,
            hashed_password,
            full_name,
            datetime.utcnow().isoformat()
        ))
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        raise ValueError("User with this email already exists")
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM users WHERE email = %s', (email,))
        row = c.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def update_user_password(email: str, hashed_password: str):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('UPDATE users SET hashed_password = %s WHERE email = %s', (hashed_password, email))
        conn.commit()
        return c.rowcount > 0
    finally:
        conn.close()
