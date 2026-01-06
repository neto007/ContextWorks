"""
Dependências compartilhadas da API
"""
from fastapi import Header, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from core import security, database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency para obter usuário autenticado do token JWT"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Remove "Bearer " prefix if present
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        
        email = security.verify_token(token)
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = database.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
