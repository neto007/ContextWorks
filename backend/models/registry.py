"""
Registry Configuration Models
Defines data models for Docker registry configuration
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal

class RegistryConfig(BaseModel):
    """Configuration for Docker registry integration"""
    
    type: Literal["dockerhub", "ecr", "gcr", "local"] = Field(
        default="local",
        description="Type of registry to use"
    )
    
    url: Optional[str] = Field(
        default=None,
        description="Registry URL (e.g., registry.example.com)"
    )
    
    username: Optional[str] = Field(
        default=None,
        description="Registry username"
    )
    
    password: Optional[str] = Field(
        default=None,
        description="Registry password or token (will be encrypted)"
    )
    
    namespace: Optional[str] = Field(
        default=None,
        description="Registry namespace/organization (e.g., myorg/myuser)"
    )
    
    use_local_fallback: bool = Field(
        default=True,
        description="Fallback to local cluster registry if push fails"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "dockerhub",
                "url": "docker.io",
                "username": "myuser",
                "password": "mytoken",
                "namespace": "myorg",
                "use_local_fallback": True
            }
        }


class RegistryTestRequest(BaseModel):
    """Request to test registry connection"""
    config: RegistryConfig


class RegistryTestResponse(BaseModel):
    """Response from registry connection test"""
    status: Literal["success", "failed"]
    message: str
