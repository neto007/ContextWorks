import psycopg2
import psycopg2.extras
from core.db_base import get_db_connection, DATABASE_URL
from core.logger import logger

def init_db():
    """Initialize database and create tables if they don't exist."""
    logger.info("Initializing database...")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Executions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY, tool_name TEXT, tool_path TEXT, target TEXT,
                status TEXT, start_time TEXT, end_time TEXT, result TEXT, logs TEXT, arguments TEXT
            )
        ''')
        
        # MCP Servers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mcp_servers (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT,
                api_key_hash TEXT NOT NULL, tool_ids TEXT, created_at TEXT,
                updated_at TEXT, status TEXT DEFAULT 'active',
                env_vars TEXT DEFAULT '{}'
            )
        ''')
        
        # Migration: Ensure env_vars column exists (idempotent)
        try:
            cursor.execute('ALTER TABLE mcp_servers ADD COLUMN IF NOT EXISTS env_vars TEXT DEFAULT \'{}\'')
        except Exception:
            conn.rollback()
        else:
            conn.commit()
        
        # MCP Connections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mcp_connections (
                id TEXT PRIMARY KEY, mcp_id TEXT, client_info TEXT,
                connected_at TEXT, last_ping TEXT,
                FOREIGN KEY (mcp_id) REFERENCES mcp_servers(id) ON DELETE CASCADE
            )
        ''')
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL, full_name TEXT, created_at TEXT
            )
        ''')
        
        # Logos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logos (
                entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
                svg_content TEXT NOT NULL, updated_at TEXT NOT NULL,
                PRIMARY KEY (entity_type, entity_id)
            )
        ''')
        
        # Workspaces table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workspaces (
                name TEXT PRIMARY KEY, description TEXT, created_at TEXT NOT NULL
            )
        ''')

        # Tools table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
                script_code TEXT NOT NULL, arguments TEXT, description TEXT,
                configuration TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                FOREIGN KEY (category) REFERENCES workspaces(name) ON DELETE CASCADE
            )
        ''')
        
        # Registry Config table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registry_config (
                id SERIAL PRIMARY KEY, type VARCHAR(20) NOT NULL DEFAULT 'local',
                url VARCHAR(255), username VARCHAR(255), password TEXT,
                namespace VARCHAR(255), use_local_fallback BOOLEAN DEFAULT TRUE,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )
        ''')

        # Build Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS build_jobs (
                id TEXT PRIMARY KEY, tool_id TEXT NOT NULL, status TEXT NOT NULL,
                logs TEXT, image_tag TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
    except Exception as e:
        logger.error("Error initializing database", exc_info=True)
        raise e
    finally:
        conn.close()

# Re-exporting common functions for backward compatibility
from core.repositories.build_repo import *
from core.repositories.execution_repo import *
from core.repositories.user_repo import *
from core.repositories.logo_repo import *
from core.repositories.workspace_repo import *
from core.repositories.tool_repo import *
from core.repositories.registry_repo import *
from core.repositories.mcp_repo import *
from core.repositories.platform_stats_repo import *

# Initialize DB on import if possible
try:
    init_db()
except:
    pass
