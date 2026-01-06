import psycopg2
from config import settings
from core.logger import logger

# Database configuration
DATABASE_URL = settings.DATABASE_URL

def get_db_connection():
    """Wait loop for DB startup (simple retry logic)"""
    import time
    max_retries = 5
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = False 
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise e
