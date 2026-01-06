"""
Modelos Pydantic para MCP Servers
"""
from pydantic import BaseModel
from typing import List, Optional

class MCPCreateRequest(BaseModel):
    name: str
    description: str
    tool_ids: List[str]

class MCPUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tool_ids: Optional[List[str]] = None
    status: Optional[str] = None
