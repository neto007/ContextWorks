"""
Modelos Pydantic para Autenticação
"""
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class RecoverRequest(BaseModel):
    email: str

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str
