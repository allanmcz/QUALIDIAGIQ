# Roteiro demo + consultoria — **15 minutos** (MVP-D)

> **Uso:** ensaio supervisionado no **MacBook** com `make dev` (localhost **60001** / API **60000**).  
> **Dados:** preferir **CNPJ e e-mail fictícios** (LC 13.709/2018 — minimização).

---

## Parte A — Demo guiada (~5 min)

| Min | Passo | O que mostrar |
|-----|-------|----------------|
| 0–1 | Abrir | `http://127.0.0.1:60001/wizard` (ou URL do teu `make dev`) |
| 1–3 | Lead + LGPD | Preencher perfil; marcar aceite LGPD |
| 3–4 | Perfil fiscal | Porte, regime, CNAE de teste |
| 4–5 | Conclusão | Submeter; mencionar **Idempotency-Key** se repetires POST |

---

## Parte B — Consultoria supervisionada (~10 min)

Perguntas sugeridas ao “cliente” (tu ou terceiro na sala):

1. O score por **dimensão** reflecta a tua leitura do negócio neste caso de teste?  
2. O **ranking de gaps** ajuda a priorizar os próximos 30 dias?  
3. A **timeline / cronograma** no detalhe está legível para apresentar a sócio leigo?  
4. O **checklist ABNT (M12)** — consegues marcar um item e ver persistência após refresh?  
5. O **PDF** (se WeasyPrint activo): rodapé com referências **EC 132/2023**, **LC 214/2025**, **ABNT NBR 17301:2026** aparece?  
6. O fluxo **B2B** (`/login` → lista → detalhe) é o que precisas para escritório?  
7. O que **falta** antes de mostrar a um cliente real (sem dados fictícios)?

---

## Checklist pós-ensaio (1 min)

- [ ] Anotar **um** gap de UX ou copy para backlog.  
- [ ] Confirmar que **não** ficaram dados sensíveis reais no browser se a demo foi só de teste.

---

*Relacionado:* [`HANDOFF_PLANO_EXECUCAO_MVP_05052026.md`](./HANDOFF_PLANO_EXECUCAO_MVP_05052026.md) · [`SMOKE_MVP_FECHADO.md`](../../docs/operacao/SMOKE_MVP_FECHADO.md)
