# Prompt — agente (fecho técnico MVP até **2026-05-05**)

Copiar para o Cursor / Claude. **Não** inclui push/rebase sem confirmação do Allan.

```text
Contexto: fechar Definição A do pacote `_DEVELOPER/MVP_05052026/01_AVALIACAO_GAP_MVP_100.md` até 2026-05-05.

Ler antes de codar:
- `_DEVELOPER/MVP_05052026/02_CRITERIOS_ACEITE_EVIDENCIAS.md`
- `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md`
- `docs/operacao/SMOKE_MVP_FECHADO.md`
- `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` §12.3 (P5)

Escopo permitido:
- Correções P0/P1 em PDF WeasyPrint (template/CSS), env espelho, scripts de verificação
- Ajustes CORS / exemplos env documentados
- Atualização de docs de evidência (checklist, changelog **rascunho** — a tag final é humana)

Fora de escopo até após o corte:
- Billing real, QAI/QFC/QMI, features SHOULD novas, migrações só por necessidade P0

Entrega:
- `make format && make lint && make test && make type-check`
- Se tocou front: `npm run build` (pasta frontend)
- Resumo em PT-BR: o que mudou + onde está a evidência (caminhos de ficheiros)

Não fazer: git push / git rebase sem confirmação explícita do Allan.
```

---

*Índice da pasta:* [`README.md`](./README.md)
