from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from typing import Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

# Mock das configurações de JWT (em dev/MVP, manteremos simplificado)
SECRET_KEY = "qualidiagiq-super-secret-key-dev"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 dia

router = APIRouter(prefix="/auth", tags=["Autenticação B2B"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    nome: Optional[str]

class AdminCreate(BaseModel):
    email: str
    password: str
    nome: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # Por simplicidade no MVP, vamos buscar via banco direto ou validar o admin mockado
    from src.presentation.api.dependencies import get_supabase_client
    client = get_supabase_client()
    
    # Busca usuário no banco. Como usamos o supabase-py sem RLS pro Auth customizado:
    try:
        # IMPORTANTE: No supabase-py, table.select não suporta text() raw do sqlalchemy, 
        # então fazemos uma consulta na tabela `admins`
        response = client.table("admins").select("*").eq("email", request.email).execute()
        users = response.data
        if not users:
            raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")
        
        user = users[0]
        if not pwd_context.verify(request.password, user["hashed_password"]):
            raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")
        
        access_token = create_access_token(
            data={"sub": user["email"], "id": user["id"]},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return LoginResponse(access_token=access_token, token_type="bearer", nome=user["nome"])
    except Exception as e:
        # Fallback de segurança se a tabela não tiver rodado no init.sql ainda (mocking mode)
        if request.email == "allan@tributolab.com.br" and request.password == "admin123":
            access_token = create_access_token(data={"sub": request.email}, expires_delta=timedelta(minutes=60))
            return LoginResponse(access_token=access_token, token_type="bearer", nome="Admin Tributiq")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create_admin")
async def create_admin(request: AdminCreate):
    """Rota para criar usuário admin. Em prod deveria ser protegida!"""
    from src.presentation.api.dependencies import get_supabase_client
    client = get_supabase_client()
    hashed_password = pwd_context.hash(request.password)
    
    try:
        client.table("admins").insert({
            "email": request.email,
            "hashed_password": hashed_password,
            "nome": request.nome
        }).execute()
        return {"msg": "Usuário admin criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao criar usuário (já existe?): {e}")
