"""
Configurações centralizadas do Security Platform
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database (PostgreSQL nativo no K8s)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/security_platform"
    )
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Kubernetes namespace
    K8S_NAMESPACE: str = os.getenv("K8S_NAMESPACE", "security-platform")
    
    # Kubernetes execution timeouts
    K8S_JOB_TIMEOUT_SECONDS: int = int(os.getenv("K8S_JOB_TIMEOUT", "120"))
    K8S_POD_WAIT_SECONDS: int = int(os.getenv("K8S_POD_WAIT", "30"))
    K8S_LOG_ATTACH_RETRIES: int = int(os.getenv("K8S_LOG_RETRIES", "120"))
    K8S_POD_WAIT_ASYNC_SECONDS: int = int(os.getenv("K8S_POD_WAIT_ASYNC", "60"))
    
    # Tools
    TOOLS_BASE_DIR: str = os.getenv(
        "TOOLS_BASE_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "tools"))
    )
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8001"))
    
    # CORS
    CORS_ORIGINS: list = ["*"]  # In production, specify exact origins

settings = Settings()
