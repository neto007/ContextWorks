import json
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2.extras
from core.db_base import get_db_connection

def create_execution(id: str, tool_name: str, tool_path: str, arguments: Dict, status: str = "running"):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Try to extract target from arguments
        target = arguments.get("target") or arguments.get("url") or arguments.get("ip") or arguments.get("domain") or ""
        
        c.execute('''
            INSERT INTO executions (id, tool_name, tool_path, arguments, target, status, start_time, logs, result)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            id, 
            tool_name, 
            tool_path, 
            json.dumps(arguments), 
            target, 
            status, 
            datetime.utcnow().isoformat(), 
            "", 
            ""
        ))
        conn.commit()
    finally:
        conn.close()

def update_execution(id: str, status: str = None, logs: str = None, result: str = None):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        updates = []
        params = []
        
        if status:
            updates.append("status = %s")
            params.append(status)
            if status in ["success", "failed"]:
                updates.append("end_time = %s")
                params.append(datetime.utcnow().isoformat())
                
        if logs is not None:
            updates.append("logs = %s")
            params.append(logs)
            
        if result is not None:
            updates.append("result = %s")
            params.append(result)
            
        params.append(id)
        
        if updates:
            sql = f"UPDATE executions SET {', '.join(updates)} WHERE id = %s"
            c.execute(sql, params)
            conn.commit()
    finally:
        conn.close()
    
def get_executions(limit: int = 50) -> List[Dict]:
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM executions ORDER BY start_time DESC LIMIT %s', (limit,))
        rows = c.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_execution(id: str) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM executions WHERE id = %s', (id,))
        row = c.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def get_execution_stats() -> Dict:
    """Retorna estatísticas agregadas de execuções"""
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Total de execuções por status
        c.execute('''
            SELECT status, COUNT(*) as count 
            FROM executions 
            GROUP BY status
        ''')
        status_counts = {row['status']: row['count'] for row in c.fetchall()}
        
        # Total geral
        total = sum(status_counts.values())
        
        # Top 10 ferramentas mais usadas
        c.execute('''
            SELECT tool_name, COUNT(*) as count 
            FROM executions 
            GROUP BY tool_name 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_tools = [dict(row) for row in c.fetchall()]
        
        # Tempo médio de execução por ferramenta (apenas execuções finalizadas)
        c.execute('''
            SELECT 
                tool_name,
                COUNT(*) as execution_count,
                AVG(
                    EXTRACT(EPOCH FROM (
                        TO_TIMESTAMP(end_time, 'YYYY-MM-DD"T"HH24:MI:SS.US') - 
                        TO_TIMESTAMP(start_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                    ))
                ) as avg_duration_seconds
            FROM executions 
            WHERE end_time IS NOT NULL AND end_time != '' 
                AND start_time IS NOT NULL AND start_time != ''
                AND status IN ('success', 'failed')
            GROUP BY tool_name 
            ORDER BY avg_duration_seconds DESC
        ''')
        avg_durations = [dict(row) for row in c.fetchall()]
        
        return {
            'total': total,
            'by_status': {
                'success': status_counts.get('success', 0),
                'failed': status_counts.get('failed', 0),
                'running': status_counts.get('running', 0),
                'stopped': status_counts.get('stopped', 0),
            },
            'top_tools': top_tools,
            'avg_durations': avg_durations,
        }
    finally:
        conn.close()
