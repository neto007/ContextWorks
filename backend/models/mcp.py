"""
Modelos Pydantic para MCP Servers
"""
from pydantic import BaseModel
from typing import List, Optional, Dict

class MCPEnvVar(BaseModel):
    name: str
    description: Optional[str] = ""
    default_value: Optional[str] = None
    required: bool = False
    tool_ids: Optional[List[str]] = []

class MCPCreateRequest(BaseModel):
    name: str
    description: str
    tool_ids: List[str]
    env_vars: Optional[List[MCPEnvVar]] = []

class MCPUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tool_ids: Optional[List[str]] = None
    status: Optional[str] = None
    env_vars: Optional[List[MCPEnvVar]] = None
