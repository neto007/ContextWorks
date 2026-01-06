"""
Modelos Pydantic para Workspaces
"""
from pydantic import BaseModel
from typing import Optional

class CreateWorkspaceRequest(BaseModel):
    name: str
    description: Optional[str] = None

class UpdateWorkspaceRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_visible: Optional[bool] = None
