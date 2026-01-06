import uuid
from datetime import datetime
from typing import Dict
import psycopg2.extras
from core.db_base import get_db_connection

def create_build_job(tool_id: str) -> str:
    """Create a new build job and return its ID"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        c.execute('''
            INSERT INTO build_jobs (id, tool_id, status, logs, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (job_id, tool_id, "PENDING", "", now, now))
        
        conn.commit()
        return job_id
    finally:
        conn.close()

def update_build_job(job_id: str, status: str, image_tag: str = None):
    """Update job status and optionally image tag"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        
        query = "UPDATE build_jobs SET status = %s, updated_at = %s"
        params = [status, now]
        
        if image_tag:
            query += ", image_tag = %s"
            params.append(image_tag)
            
        query += " WHERE id = %s"
        params.append(job_id)
        
        c.execute(query, tuple(params))
        conn.commit()
    finally:
        conn.close()

def append_build_logs(job_id: str, new_logs: str):
    """Append logs to a build job"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            UPDATE build_jobs 
            SET logs = COALESCE(logs, '') || %s 
            WHERE id = %s
        ''', (new_logs, job_id))
        conn.commit()
    finally:
        conn.close()

def get_build_job(job_id: str) -> Dict:
    """Get build job details"""
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM build_jobs WHERE id = %s', (job_id,))
        row = c.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
