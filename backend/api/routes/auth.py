"""
Rotas de Autenticação
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import timedelta
import uuid

from config import settings
from core import database, security
from models.auth import UserCreate, RecoverRequest, PasswordUpdate
from api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(user: UserCreate):
    """Registra um novo usuário"""
    # Check if user exists
    db_user = database.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = security.get_password_hash(user.password)
    
    database.create_user(user_id, user.email, hashed_password, user.full_name)
    return {"status": "success", "user_id": user_id}

@router.post("/login")
def login(login_data: LoginRequest):
    """Autentica usuário e retorna token JWT"""
    user = database.get_user_by_email(login_data.username)
    if not user or not security.verify_password(login_data.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/recover")
def recover_password(request: RecoverRequest):
    """Inicia processo de recuperação de senha"""
    user = database.get_user_by_email(request.email)
    if not user:
        # Por segurança, não revelamos se o email existe
        return {"status": "success", "message": "If the email exists, a recovery link has been sent"}
    
    # TODO: Implementar envio de email com token de recuperação
    # Por enquanto, apenas retorna sucesso
    return {
        "status": "success",
        "message": "Recovery email sent",
        "todo": "Email sending not implemented yet"
    }

@router.get("/me")
def get_current_user_info(user: dict = Depends(get_current_user)):
    """Retorna informações do usuário autenticado"""
    return {
        "id": user['id'],
        "email": user['email'],
        "full_name": user.get('full_name'),
        "created_at": user.get('created_at')
    }

@router.put("/password")
def update_password(
    password_update: PasswordUpdate,
    user: dict = Depends(get_current_user)
):
    """Atualiza senha do usuário autenticado"""
    # Verify current password
    if not security.verify_password(password_update.current_password, user['hashed_password']):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    new_hashed_password = security.get_password_hash(password_update.new_password)
    success = database.update_user_password(user['email'], new_hashed_password)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    
    return {"status": "success", "message": "Password updated"}
