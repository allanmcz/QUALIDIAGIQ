# Status remediação QDI-H — 2026-05-11

> Modelo do plano `_DEVELOPER/ANALISE_10052026/PLANO_IMPLEMENTACAO_HANDOFF_CODEX_CLAUDE.md` — atualizar semanalmente.

## Resumo

| Estado | Contagem aproximada |
|--------|---------------------|
| Fechado (código/SQL/CI) | H-001–H-005, H-008–H-010, H-013, H-016–H-020 (parcial logs), H-026, H-035–H-037 (métrica textual), migrações até **0041** |
| Parcial / docs rascunho | H-011, H-012, H-014, H-015, H-022, H-023, H-025, H-027 (ADRs), H-032 (ADR-003) |
| Externo ou Onda 1.1 | H-024, H-028–H-031, H-033 (smoke real), H-034, H-038, H-039, H-029 (job CI opcional) |

## % P1 (estimativa manual)

- **Código/SQL:** maior parte dos P1 de engenharia entregues; validar com `make test` + `make mvp-gate` em CI.
- **Documental / legal:** RIPD + DPO + Grafana 7 dias — **abertos** até ação humana.

## Notas da semana

- Adicionada migração **0041** (FORCE RLS `cnpj_consultas` + histórico empresa).
- Teste integração **H-003** em `tests/integration/test_qdi_rag_revoke_authenticated_postgres.py`.
- **npm audit CI:** threshold **critical** (HIGH no Next 14.x — middleware — até decisão de upgrade).

## Próxima atualização

- Copiar para `STATUS_REMEDIACAO_<nova-data>.md` e arquivar esta linha temporal.
