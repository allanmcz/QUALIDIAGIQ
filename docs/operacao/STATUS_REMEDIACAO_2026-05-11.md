# Status remediação QDI-H — 2026-05-11

> Modelo do plano `_DEVELOPER/ANALISE_10052026/PLANO_IMPLEMENTACAO_HANDOFF_CODEX_CLAUDE.md` — atualizar semanalmente.

## Resumo

| Estado | Contagem aproximada |
|--------|---------------------|
| Fechado (código/SQL/CI) | H-001–H-005, H-008–H-010, H-013, H-016–H-020, H-021 (Report-Only opcional), **H-022** (``diagnostico_criado``, ``diagnostico_finalizado``, ``diagnostico_rascunho_self_service_gravado``, ``auth_login_sucesso``), H-026, H-029 (workflow dispatch), H-035–H-037, migrações até **0041** |
| Parcial / docs rascunho | H-011, H-012, H-014, H-015, H-023, H-025, H-027, H-032, **H-038** (payload LGPD → ``JsonValue``) |
| Externo ou Onda 1.1 | H-024, H-028–H-031, H-033 (smoke real), H-034, H-039, CSP nonce completo (ADR-018) |

## % P1 (estimativa manual)

- **Código/SQL:** maior parte dos P1 de engenharia entregues; validar com `make test` + `make mvp-gate` em CI.
- **Documental / legal:** RIPD + DPO + Grafana 7 dias — **abertos** até ação humana.

## Notas da semana

- Adicionada migração **0041** (FORCE RLS `cnpj_consultas` + histórico empresa).
- Teste integração **H-003** em `tests/integration/test_qdi_rag_revoke_authenticated_postgres.py`.
- **npm audit CI:** threshold **HIGH** (`--audit-level=high`, ADR-016). Sem fix upstream: substituir pacote, `overrides` ou **ADR de exceção** (sem waiver silencioso).
- **H-022:** ``diagnostico_criado`` + ``diagnostico_finalizado`` em ``realizar_diagnostico.py``; ``diagnostico_rascunho_self_service_gravado`` em rascunho POST; ``auth_login_sucesso`` em ``routes_login.py``; ``RETURNING id`` em ``inserir_rascunho_sync``.
- **H-021:** ``QDI_CSP_REPORT_ONLY=1`` no build Next + documentação em ``.env.example``.
- **H-029:** workflow ``zap-baseline-dispatch.yml`` (execução manual no GitHub).

## Próxima atualização

- Copiar para `STATUS_REMEDIACAO_<nova-data>.md` e arquivar esta linha temporal.
