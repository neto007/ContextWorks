from typing import Dict
import psycopg2.extras
from core.db_base import get_db_connection

def get_platform_stats() -> Dict:
    """Retorna estatísticas gerais da plataforma"""
    conn = get_db_connection()
    try:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # MCP Servers
        c.execute('SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE status = %s) as active FROM mcp_servers', ('active',))
        mcp_row = c.fetchone()
        mcp_total = mcp_row['total'] if mcp_row else 0
        mcp_active = mcp_row['active'] if mcp_row else 0
        
        # MCP Connections
        c.execute('SELECT COUNT(*) as total FROM mcp_connections')
        conn_row = c.fetchone()
        mcp_connections = conn_row['total'] if conn_row else 0
        
        # Builds
        c.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'COMPLETED') as success,
                COUNT(*) FILTER (WHERE status = 'FAILED') as failed,
                COUNT(*) FILTER (WHERE status = 'PENDING' OR status = 'BUILDING') as pending
            FROM build_jobs
        ''')
        build_row = c.fetchone()
        builds = {
            'total': build_row['total'] if build_row else 0,
            'success': build_row['success'] if build_row else 0,
            'failed': build_row['failed'] if build_row else 0,
            'pending': build_row['pending'] if build_row else 0,
        }
        
        # Workspaces
        c.execute('SELECT COUNT(*) as total FROM workspaces')
        ws_row = c.fetchone()
        workspaces = ws_row['total'] if ws_row else 0
        
        # Tools
        c.execute('SELECT COUNT(*) as total FROM tools')
        tools_row = c.fetchone()
        tools = tools_row['total'] if tools_row else 0
        
        return {
            'mcp_servers': {
                'total': mcp_total,
                'active': mcp_active,
                'connections': mcp_connections,
            },
            'builds': builds,
            'workspaces': workspaces,
            'tools': tools,
        }
    finally:
        conn.close()
