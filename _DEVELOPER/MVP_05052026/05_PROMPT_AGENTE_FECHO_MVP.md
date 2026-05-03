# Prompt — agente (fecho técnico MVP até **2026-05-05**)

Copiar para o Cursor / Claude. **Não** inclui push/rebase sem confirmação do Allan.

```text
Contexto: executar `_DEVELOPER/MVP_05052026/HANDOFF_PLANO_EXECUCAO_MVP_05052026.md` (fases F0–F4, IDs Z)
e fechar **Definição D** (demo local + consultoria supervisionada no MacBook, sem site público)
conforme `_DEVELOPER/MVP_05052026/00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md` + secção **2** de
`_DEVELOPER/MVP_05052026/02_CRITERIOS_ACEITE_EVIDENCIAS.md` até 2026-05-05.

Se Allan pedir explicitamente go-live, mudar para Definição A no `01_AVALIACAO_GAP_MVP_100.md`.

Ler antes de codar:
- `_DEVELOPER/MVP_05052026/00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md`
- `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md` (subset itens objetivos)
- `docs/operacao/SMOKE_MVP_FECHADO.md` (smoke local)
- `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` §12.3 (P5)

Escopo permitido:
- Correções P0/P1 em PDF WeasyPrint (template/CSS) para demo em `make dev`
- Scripts / docs de evidência **local** (sem obrigar CORS prod, tag ou deploy)

Fora de escopo (cenário D):
- DNS/D4 produção, P6 Supabase cloud, billing, jurídico comercial para SaaS público, tag de release
- Billing real, QAI/QFC/QMI, features SHOULD novas, migrações só por necessidade P0

Entrega:
- `make format && make lint && make test && make type-check`
- Se tocou front: `npm run build` (pasta frontend)
- Resumo em PT-BR: o que mudou + onde está a evidência (caminhos de ficheiros)

Não fazer: git push / git rebase sem confirmação explícita do Allan.
```

---

*Índice da pasta:* [`README.md`](./README.md)
