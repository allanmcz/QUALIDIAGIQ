# ADR-014 — `FORCE ROW LEVEL SECURITY` em tabelas críticas tenant-scoped

| Campo | Valor |
|-------|--------|
| **Status** | Aceita |
| **Data** | 2026-05-10 |
| **Contexto** | Com `ENABLE ROW LEVEL SECURITY`, o **owner** da tabela pode contornar políticas em alguns cenários de configuração; dados sensíveis (`diagnosticos`, LGPD, auditoria WORM) exigem defesa em profundidade. |
| **Decisão** | Aplicar `ALTER TABLE … FORCE ROW LEVEL SECURITY` em `diagnosticos`, `lgpd_titular_solicitacao`, `lgpd_anonimizacao_log`, `diagnostico_mutacao_audit`. **Não** aplicar em caches globais (`cnpj_consulta_cache`), nem em `idempotency_responses` (dados efémeros + custo). Superutilizadores PostgreSQL continuam a poder contornar RLS por natureza do motor — operações de emergência devem usar processos auditados. |
| **Consequências** | Consistência alinhada a políticas mesmo para roles não superutilizadores que sejam owners; manutenção documentada no runbook pg_cron / admin. |
