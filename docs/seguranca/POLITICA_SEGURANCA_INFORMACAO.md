# Política de segurança da informação — QualiDiagIQ (rascunho técnico)

> **Atenção:** documento de apoio à ISO 27001 / operação; revisão formal pelo responsável de segurança.

## Princípios

1. **Confidencialidade:** segredos apenas em variáveis de ambiente (`pydantic-settings`); sem chaves no repositório.
2. **Integridade:** migrações append-only para evidências; hash de diagnóstico (ADR-012, migrações `qdi.*`).
3. **Disponibilidade:** health checks `/health/live` e `/health/ready`; plano de backup em `docs/operacao/BACKUP_RECUPERACAO.md`.

## Controlo de acesso

- Autenticação JWT com `tenant_id` em claim (anti-padrão S-04).
- Endpoints administrativos protegidos por dependências de admin.

## Gestão de vulnerabilidades

- CI: `npm audit --omit=dev --audit-level=high` (ADR-016).
- Pre-commit: gitleaks (ADR-016).

## Divulgação responsável

- `frontend/public/.well-known/security.txt` (RFC 9116) — atualizar contacto em produção.
