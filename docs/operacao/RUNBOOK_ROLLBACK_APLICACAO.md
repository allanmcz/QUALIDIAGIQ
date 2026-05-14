# Runbook — Rollback de aplicação QDI

> Procedimento operacional mínimo. Migrações SQL são **forward-only** (ADR-019) — não há «down» automático de schema.

## Quando acionar

- Taxa de erro **5xx** > 5% sustentada por > 5 minutos (comparar com `_DEVELOPER/DECISAO_EXTERNA/SLO_OPERACAO_QDI.md`).
- **Vazamento de dados** confirmado ou suspeita forte (seguir também `docs/operacao/RUNBOOK_SEGREDO_VAZADO.md`).
- **Regressão funcional bloqueante** (login, wizard crítico, persistência de diagnóstico).

## Pré-condições

- Imagem Docker ou artefacto da **versão estável anterior** identificável (tag Git / SHA).
- Acesso ao painel de deploy (**Vercel** / **Render** / outro — o que estiver em uso).
- Acesso ao **Supabase** (dashboard) para verificar saúde da BD (sem rollback de DDL).

## Procedimento — backend (FastAPI)

1. Identificar tag ou SHA da última versão boa: `git log --oneline -20`.
2. No serviço de hosting: **promover** deploy da imagem/commit anterior (rollback de aplicação, não de dados).
3. Validar `GET /health/live` → **200** e corpo `status=ok`.
4. Validar `GET /health/ready` → **200** (Postgres acessível para idempotência).
5. Verificar logs estruturados sem erro de bootstrap (`structlog`).

## Procedimento — frontend (Next.js)

1. No painel Vercel (ou equivalente): **Deployments** → selecionar deploy anterior estável → **Promote to Production**.
2. Se CDN/cache externo: invalidar apenas se documentado para o teu hosting.
3. Smoke manual mínimo: página de login + primeira página do wizard (sem regressão visível).

## Procedimento — base de dados

- **Não** executar rollback de DDL. Migrações são apenas **forward** (ADR-019).
- Se o incidente exigir correcção de schema: criar **nova migração** corretiva e redeployar para a frente.

## Critério de sucesso

- `/health/live` verde.
- Taxa 5xx < 1% durante **15 minutos** consecutivos (referência SLO MVP).
- Smoke do fluxo principal (login + início de diagnóstico) verde.

## Pós-rollback

- Abrir registo de incidente em `docs/operacao/INCIDENTES/` (ficheiro `YYYY-MM-DD-assunto.md` — criar pasta se ainda não existir).
- Atualizar **status page** (se ativa) e comunicar stakeholders internos.

## Referências

- `.github/adr/ADR-019-sql-migrations-forward-only.md`
- `docs/operacao/BACKUP_E_DR.md`
- `_DEVELOPER/DECISAO_EXTERNA/SLO_OPERACAO_QDI.md`
