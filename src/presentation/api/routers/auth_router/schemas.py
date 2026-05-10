"""Schemas Pydantic dos endpoints `/auth/*`."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class CadastroConsultorB2BRequest(BaseModel):
    """Cadastro mínimo para acesso ao painel (conta na plataforma)."""

    nome: str = Field(min_length=1, max_length=255, description="Nome exibido no painel.")
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=256,
        description="Senha com pelo menos 8 caracteres (bcrypt no servidor).",
    )

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    nome: str | None
    perfil_conta: str = "gratuito"


class SolicitarVerificacaoEmailRequest(BaseModel):
    """Wizard passo 1 — confirmação de posse do inbox (LGPD)."""

    email: EmailStr


class SolicitarVerificacaoEmailResponse(BaseModel):
    mensagem: str


class ConfirmarVerificacaoEmailRequest(BaseModel):
    email: EmailStr
    codigo: str = Field(min_length=4, max_length=8, description="Código recebido por e-mail")


class ConfirmarVerificacaoEmailResponse(BaseModel):
    verificado: bool


class SelfServiceTokenRequest(BaseModel):
    """Troca OTP por JWT para POST /diagnosticos/self-service."""

    email: EmailStr
    codigo: str = Field(
        min_length=4, max_length=8, description="Código numérico recebido por e-mail"
    )


class SelfServiceTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
