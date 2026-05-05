# Template — evidência RLS dois tenants (OPS)

**Data:** ____/____/______  
**Ambiente:** (ex.: Supabase projeto `___` / pooler URL mascarada)  
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

Referência técnica: `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`.
