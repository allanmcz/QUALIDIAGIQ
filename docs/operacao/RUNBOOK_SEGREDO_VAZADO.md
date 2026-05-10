# Runbook — segredo vazado (repos Git ou logs)

## Primeiros 5 minutos

1. Identificar **qual segredo** (JWT, API key, URL com senha, etc.).
2. Determinar se houve **push remoto** ou apenas commit local.
3. Assumir comprometimento total da credencial — **rotacionar**, não apenas apagar do ficheiro.

## Rotação por tipo

| Segredo | Ação |
|---------|------|
| **JWT_SECRET_KEY** | Gerar novo (`python -c "import secrets; print(secrets.token_urlsafe(48))"`), atualizar env em produção, aceitar logout de sessões antigas. |
| **ANTHROPIC_API_KEY / OPENAI_API_KEY** | Nova chave no painel do fornecedor; revogar a antiga. |
| **SUPABASE_SERVICE_ROLE_KEY** | Rotacionar no projeto Supabase; monitorizar logs por uso da chave antiga. |
| **DATABASE_URL / senha Postgres** | `ALTER USER ... PASSWORD '...'` ou fluxo equivalente na hospedagem; atualizar secrets da API e reiniciar. |

## Histórico Git

Se o segredo entrou num commit já enviado ao remoto:

1. Rotacionar o segredo na origem (prioridade absoluta).
2. Opcionalmente limpar histórico com **git filter-repo** / BFG e `git push --force-with-lease` — coordenar com todos os clones.
3. Registar postmortem em `docs/operacao/` se impacto relevante.

## Ferramentas locais

- **`scripts/audit_secrets.sh`** — CI e hook pré-commit.
- **gitleaks** — `.gitleaks.toml`; falsos positivos em `.gitleaksignore`.
