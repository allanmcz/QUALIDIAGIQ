# ADR-010 — Estado do wizard diagnóstico: React Hook Form + hook próprio (sem XState no MVP)

Data: 2026-05-05  
Estado: aceite (Onda 1.0 / refactor WizardForm)

## Contexto

O `WizardForm` concentra fluxo multi-passo (identificação, perfil, questionário adaptativo), integrações com API (catálogo, CNAE, rascunho self-service, JWT pendente) e regras de UX. O roadmap de refactor (`_DEVELOPER/DEV_DIAG_04052026/ROADMAP_HANDOFF_REFACTOR_LGPD_PWA.md`) mencionava **XState** como opção se a complexidade justificasse.

## Decisão

**Não** adoptar XState (nem outra state machine explícita) no wizard para o MVP / Onda 1.0.

A modelagem permanece em:

- **React Hook Form** — fonte de verdade dos campos e validação Zod;
- **`useWizardState`** — orquestração (passo atual, efeitos colaterais, carregamento de perguntas, rascunho, navegação);
- **Sub-componentes por passo** (`WizardStep*`) — apresentação desacoplada.

## Consequências

- **Positivas:** menos dependências, curva de manutenção alinhada ao stack Next.js 14 actual; diff de PRs mais legível para o equipa.
- **Negativas / risco:** transições de passo não são formalmente diagramadas numa máquina de estados; regressões exigem testes manuais focados e E2E onde existirem.

## Revisão futura

Reavaliar XState (ou equivalente) se surgirem **muitas** transição condicionais cruzadas (ex.: forks por segmento + normativa + erros de rede) que tornem o hook ilegível ou propensos a bugs de estado impossível.

## Referências

- Handoff: `_DEVELOPER/DEV_DIAG_04052026/ROADMAP_HANDOFF_REFACTOR_LGPD_PWA.md` (fases W1–W5)
- Componentes: `frontend/components/wizard/WizardForm.tsx`, `useWizardState.ts`, `frontend/components/wizard/steps/`
