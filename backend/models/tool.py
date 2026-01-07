"""
Modelos Pydantic para Ferramentas (Tools)
"""
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class ToolExecutionRequest(BaseModel):
    path: Optional[str] = None # Deprecated, use tool_id
    tool_id: Optional[str] = None
    job_id: Optional[str] = None # Optional for re-attaching to existing jobs
    arguments: Dict[str, Any]
    env: Optional[Dict[str, str]] = None # Environment variables to inject

class ToolContentRequest(BaseModel):
    path: Optional[str] = None # Deprecated, use tool_id
    tool_id: Optional[str] = None
    content: str

class CreateToolRequest(BaseModel):
    category: str
    name: str
    description: str
    script_code: Optional[str] = None
    arguments: Optional[List[Dict]] = None
    docker: Optional[Dict] = None  # Docker configuration (image, apt_packages, pip_packages, etc)
    resources: Optional[Dict] = None  # Kubernetes resources (requests, limits)

class UpdateToolRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    script_code: Optional[str] = None
    arguments: Optional[List[Dict]] = None
    docker: Optional[Dict] = None  # Docker configuration updates
    resources: Optional[Dict] = None  # Kubernetes resources updates

class LogoUploadRequest(BaseModel):
    svg_code: str

class TestToolRequest(BaseModel):
    script_code: str
    arguments: Optional[Dict[str, Any]] = None
    tool_name: Optional[str] = "test-tool"
    tool_id: Optional[str] = None
    image: Optional[str] = None
    configuration: Optional[str] = None
