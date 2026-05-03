# Cronograma concentrado — **03 a 05 de maio de 2026**

> **Premissa:** equipa reduzida (Allan + agente/Eng + jurídico/Ops sob demanda). Ajustar horários ao teu bloco de **45 min** com pausas.

### Atalho — cenário **D** (demo + consultoria no MacBook, sem público)

Se adoptaste a [**definição D**](./01_AVALIACAO_GAP_MVP_100.md) ([`00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md`](./00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md)):

| Dia | Foco único |
|-----|----------------|
| **03** | `make dev` + subset **B1** PDF + **1** gravação ou PDF de exemplo (dados fictícios) |
| **04** | `make mvp-gate` + `verify-schema-mvp-strict` no Postgres local **60322** + roteiro oral 15 min |
| **05** | Repetição ensaio + nota “MVP-D fechado” em `HANDOFF_PROXIMA` (opcional) |

**Não** executar linhas de calendário abaixo que falem em D4, jurídico comercial ou tag — são para **A/B**.

---

## Sábado **03-05-2026** — Congelamento + PDF + decisões *(A / B)*

| Janela | Entrega | Detalhe |
|--------|---------|---------|
| Manhã | **Congelamento código** | Branch `release/mvp-2026-05-05` ou tag preparatória; sem features novas só correções P0 |
| Manhã | **P5a** | Percorrer `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md` — fechar itens **objetivos** (layout, hierarquia, contraste, rodapé) |
| Tarde | **P5b** | Subir/validar **espelho WeasyPrint** conforme `RUNBOOK_DEPLOY_ROLLBACK.md` + nota de versões/fontes |
| Tarde | **D3 / D5** | Se não houver tempo: registar **“adiado até pós-MVP”** com data em `DECISOES_PRODUTO_MVP_D1_D5.md` |
| Fim do dia | **D4** | URL canónica + `NEXT_PUBLIC_*` + CORS — uma linha “assinado” no doc de decisões ou ticket |

**Saída do dia:** PDF exemplo no espelho + checklist B1 majoritariamente **[x]** + decisões D escritas.

---

## Domingo **04-05-2026** — Smoke, schema, jurídico, release *(A / B)*

| Janela | Entrega | Detalhe |
|--------|---------|---------|
| Manhã | **A2–A3** | `make mvp-gate`, `verify-schema-mvp-strict` no DB alvo |
| Manhã | **A5** | Smoke manual `SMOKE_MVP_FECHADO.md` |
| Tarde | **G-J1** (se alvo B) | Encaminhar ou receber parecer mínimo jurídico; se impossível: **declarar alvo A** por escrito |
| Tarde | **P6 cloud** (opcional) | Evidência ou **dispensa explícita** no `CHECKLIST` |
| Fim do dia | **G-A1** | Nome da tag acordado (ex. `v1.0.0-mvp`) + rascunho entrada `CHANGELOG_MVP` |

**Saída do dia:** evidências A2/A3/A5 anexadas ou referenciadas + changelog pronto para merge.

---

## Segunda **05-05-2026** — Corte final *(A / B)*

| Janela | Entrega | Detalhe |
|--------|---------|---------|
| Manhã | **Última verificação** | `make test` + Playwright smoke mínimo se tocou front |
| Manhã | **Tag + push tag** | Após merge na branch acordada |
| Meio-dia | **Atualização handoff** | `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` §12.3 + data “MVP técnico fechado 2026-05-05” |
| Tarde | **Comunicação interna** | Mensagem curta: alvo A vs B cumprido + link para esta pasta |

**Saída do dia:** repositório com **tag** + **CHANGELOG** + checklist Allan atualizado.

---

## Dependências cruzadas (não bloquear A)

- Jurídico **não** pronto a 05-05 → mantém **alvo A** e abre **follow-up** “MVP institucional” com data.  
- **3 contadores externos** não fechados → mover para **pós-MVP comercial** com registo no checklist sec. 5.

---

*Riscos:* [`04_RISCOS_DEPENDENCIAS_DECISOES.md`](./04_RISCOS_DEPENDENCIAS_DECISOES.md)
