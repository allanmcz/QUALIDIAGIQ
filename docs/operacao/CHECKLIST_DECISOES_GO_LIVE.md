# Checklist — decisões teu (PO) vs externos (go-live QDI)

> Uma página para não perder o fio: o que **só tu** fechas (produto/risco/prioridade) vs o que depende de **terceiros ou operações**.  
> Rastreio detalhado: `_DEVELOPER/ANALISE_10052026/PLANO_IMPLEMENTACAO_HANDOFF_CODEX_CLAUDE.md` (gate §5) e `docs/operacao/STATUS_REMEDIACAO_2026-05-11.md`.

**Como usar:** marca `[x]` quando houver **decisão escrita** ou **evidência** (link PR, PDF, print, data). Anexa ata se aceitares risco residual.

---

## 1. Decisões tuas (Allan / PO / produto)

| # | Assunto | IDs | Decisão ou evidência |
|---|---------|-----|----------------------|
| 1 | **Data-alvo de go-live** e o que é **bloqueante** vs “nice to have” | Plano §5 | Data: ______ · Lista P1 bloqueantes: ______ |
| 2 | **JWT em `localStorage` (H-034)** — aceitar risco residual com ADR até Onda 1.1 **ou** exigir cookie httpOnly antes de produção | H-034 | Opção escolhida: ______ · ADR/ata: ______ |
| 3 | **npm audit / Next 14** — tolerar HIGH documentado no CI (threshold critical) **ou** priorizar upgrade / exceção formal | H-009 / notas STATUS | Decisão: ______ |
| 4 | **H-038** tipagem retificação/quadro — priorizar refactor de tipos **ou** manter incremental só onde já está estável | H-038 | Decisão: ______ |
| 5 | **H-039** `useWizardState` — calendário: antes do go-live **ou** Onda 1.1 | H-039 | Decisão: ______ |
| 6 | **CSP “forte”** (nonce + política final, ADR-018) vs **Report-Only** / estado atual | H-021 | Decisão: ______ |
| 7 | **SLO / dono / escalação** (números e dono aceites pela equipa) | H-023 | Documento/ata: ______ |
| 8 | **Retenção de logs + redaction** — política interna assente com engenharia | H-015 | Referência: ______ |

---

## 2. Externos (jurídico, ops, QA ofensivo)

| # | Assunto | IDs | Responsável | Evidência mínima |
|---|---------|-----|---------------|------------------|
| 1 | **Bases legais do tratamento** (dado × finalidade × base × retenção) | H-011 | Jurídico / DPO | Ficheiro em `docs/legal/` + revisão Allan |
| 2 | **RAT** (subprocessadores, transferências) | H-012 | Jurídico / DPO | `docs/legal/RAT.md` atualizado |
| 3 | **RIPD** preenchido e **assinado** | H-030 | DPO | PDF ou registo interno datado |
| 4 | **Designação formal de DPO** | H-031 | Jurídico / contrato | Ato ou contrato arquivado |
| 5 | **Dashboard + ≥ 7 dias de dados** antes do go-live | H-024 | Ops / SRE | URL ou print com intervalo visível |
| 6 | **Pentest** + correção de P1s do relatório | H-028 | Fornecedor + eng | Relatório arquivado + issues fechadas |
| 7 | **Smoke** real em staging (e mobile, se for requisito) | H-033 | QA / Allan | Log ou vídeo + `make go-live` (ou script doc.) verde |
| 8 | **ZAP baseline** em URL de staging | H-029 | Eng + ambiente | Run do workflow `zap-baseline-dispatch.yml` + notas |

---

## 3. Cruzamento rápido (gate Plano §5)

- [ ] P1 código alinhado à política de risco (incl. H-034 se não adiar)
- [ ] P1 documental (H-011, H-012, H-030, H-031)
- [ ] Observabilidade H-024 (janela 7 dias)
- [ ] Qualidade: CI verde (`make test`, lint, type-check conforme repo)
- [ ] Ata de go-live com **riscos residuais** explicitamente aceites (ex.: H-034 só em 1.1)

---

**Última revisão:** 2026-05-13 — criado a pedido do Allan para acompanhar decisões e handoff sem dispersar em vários ficheiros.
