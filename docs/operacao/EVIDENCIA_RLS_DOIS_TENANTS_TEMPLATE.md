# Template — evidência RLS dois tenants (OPS)

**Data:** ____/____/______  
**Ambiente (caminho primário dev/MVP):** Postgres **Docker Compose** — `127.0.0.1:60322` após `make dev` (`docker-compose.yml`); API típica `http://127.0.0.1:60000`; variável de testes `QDI_POSTGRES_TEST_URL` / `DATABASE_URL` alinhadas ao mesmo host.  
**Opcional (segunda evidência pré-go-live):** projeto Supabase gerido — nome/ref mascarada (sem secrets no Git).  
**Executor:** _______________

## Passos

1. Aplicar migrações até à mesma revisão que produção (`init.sql` / pipeline).
2. Criar dois utilizadores/tenants de teste (JWT distintos).
3. Inserir ou gerar diagnóstico no **tenant A**.
4. Com JWT do **tenant B**, executar `GET /diagnosticos/{id_A}` — **deve** retornar 404 ou lista vazia conforme contrato.
5. Opcional: SQL com `SET qdi.jwt_tenant_id` / role de serviço conforme runbook.

## Resultado

- [ ] Isolamento confirmado  
- [ ] Captura anexada (log pytest, screenshot SQL, ou nota em `CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`)

Referências: smoke automatizado `make mvp-gate` / `tests/integration/test_mvp_gate_postgres.py`; runbook políticas em projeto gerido: `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`.
