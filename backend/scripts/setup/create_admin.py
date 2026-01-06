import sys
import os
import uuid

# Add the backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core import database
from core import security
from core.logger import logger

def create_admin_user():
    email = "admin@platform.com"
    password = "admin123"
    
    logger.info(f"Creating admin user: {email}")
    
    # Check if user already exists
    existing = database.get_user_by_email(email)
    if existing:
        logger.info(f"User {email} already exists.")
        return

    hashed_password = security.get_password_hash(password)
    user_id = str(uuid.uuid4())
    
    try:
        database.create_user(
            user_id=user_id,
            email=email,
            hashed_password=hashed_password,
            full_name="Administrator"
        )
        logger.info(f"Successfully created user {email}")
    except Exception as e:
        logger.error(f"Error creating user: {e}")

if __name__ == "__main__":
    create_admin_user()
