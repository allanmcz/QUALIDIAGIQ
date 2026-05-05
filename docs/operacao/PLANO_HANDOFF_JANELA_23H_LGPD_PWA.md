# Plano de handoff — janela até às 23h (LGPD técnico + PWA + fechos do roadmap)

| Campo | Valor |
|-------|-------|
| **Objetivo** | Maximizar o que **pode ser entregue ou preparado** numa única janela noturna, sem ilusão de “LGPD completo” ou “PWA em produção” sem ADR e testes. |
| **Referência** | `_DEVELOPER/DEV_DIAG_04052026/ROADMAP_HANDOFF_REFACTOR_LGPD_PWA.md` (painel: A/B ✅ · C/D ⏳) |
| **ADRs associados** | `ADR-011` (PWA B1 aceite) · `ADR-012` (desenho LGPD + inventário) — `.github/adr/` |
| **Implementação handoff (Git)** | 2026-05-05 — manifest/viewport, runbook, templates jurídicos, progresso em `ROADMAP_HANDOFF_PROGRESSO_SYNC.md` |

## 1. Premissas realistas de tempo

| Símbolo | Significado |
|---------|-------------|
| **⚡** | ~30–45 min — cabe quase sempre antes das 23h |
| **◆** | ~1–2 h — escolher 1–2 por noite |
| **✚** | >2 h ou dependência externa — **não** prometer fecho na mesma noite |

Ajuste à tua hora de início: se sobrarem **menos de 2 h**, faça só **§3 + §4 + §7** (ADRs + sequência + comando de validação).

## 2. Trilho paralelo — Jurídico / negócio (sem código)

Tudo isto **desbloqueia** engenharia; pouco serve inventar API “art. 18” sem isto alinhado.

| # | Entrega | Owner | Cabe até 23h? |
|---|---------|-------|----------------|
| J1 | **DPO** nome + e-mail institucional acordados para publicação | Jurídico / Allan | ⚡ se já decidido internamente |
| J2 | **RIPD** — versão 0.1 (processo diagnóstico + bases legais + retenção) **sem dados reais** no repo | DPO + negócio | ◆ (rascunho) |
| J3 | **Política de privacidade / termos** — versão datada alinhada ao fluxo actual (self-service + conta na plataforma) | Jurídico | ◆ (revisão) |
| J4 | **Workshop 45 min** só para **WORM × anonimização × pedido de eliminação** — decisão gravada no corpo do ADR-012 | Allan + jurídico (opcional) | ⚡–◆ |

**Handoff:** documentos formais podem viver **fora do Git**; no repo ficam ADR + checklist + runbook (§6).

## 3. Trilho engenharia — P0-07 (LGPD técnico)

**Ordem obrigatória:** ADR-012 **antes** de migrações novas ou endpoints sensíveis.

| # | Entrega | Esforço | Critério de aceite mínimo |
|---|---------|---------|---------------------------|
| E-L1 | Ler ADR-012 e **preencher** secção “Decisões em aberto” com o que já sabes | ⚡ | Lista de bullets não vazia ou explicitamente “bloqueado jurídico até …” |
| E-L2 | `grep` / inventário: `worm`, `diagnostico_mutacao_audit`, tabelas de diagnóstico **sem inventar nomes** | ⚡ | Notas no ADR-012 ou doc linked |
| E-L3 | Esboço de **fluxos art. 18** (exportar / retificar / **limitar tratamento** / eliminar onde aplicável) — **apenas desenho** (sequência + auth + tenant) | ◆ | Diagrama Mermaid ou lista numerada no ADR |
| E-L4 | Implementação **código** (tabela anonimização + endpoints) | ✚ | **Fora** da promessa “até 23h” salvo ADR já fechado há dias |

## 4. Trilho engenharia — P0-06 (PWA)

**Ordem:** ADR-011 **antes** de `next-pwa` ou equivalente no `package.json`.

| # | Entrega | Esforço | Critério de aceite mínimo |
|---|---------|---------|---------------------------|
| E-P1 | ADR-011 lido; **estratégia** escolhida (PWA completo vs “instalável mínimo” vs só responsive) | ⚡–◆ | Caixa “Decisão” preenchida ou “adiado com motivo” |
| E-P2 | Branch `feat/qdi-front-pwa-onda1` criada **local**; baseline `npm run build` + `npm run test:e2e` registados (screenshot/log) | ⚡ | Evidência no PR ou nota no ADR |
| E-P3 | Dependência + `next.config` + SW | ✚ | Só se ADR-011 **aceite** e sobra tempo; caso contrário **não merge** na mesma noite |

## 5. Refinos do roadmap já concluído (A/B) — opcional esta noite

| # | Entrega | Esforço |
|---|---------|---------|
| R1 | Atualizar **painel** no ficheiro `_DEVELOPER/.../ROADMAP_...md` com: hash do último commit, `npm run test:e2e` verde, nota sobre specs **skipped** (`INTEGRATED`, `WIZARD_NORMATIVA`) | ⚡ |
| R2 | Diff OpenAPI (`/docs`) vs artefacto guardado — **opcional** | ◆ |

## 6. Runbook mínimo — “operações sensíveis” (rascunho para P0-07)

Colar no ADR-012 ou criar `docs/operacao/RUNBOOK_DIREITOS_TITULAR_RASCUNHO.md` quando o desenho estabilizar:

1. **Quem** pode solicitar (titular autenticado? representante?)
2. **Como** se prova tenant + vínculo com o diagnóstico
3. **O que** é exportável (JSON? PDF já existente?)
4. **O que** é imutável por WORM e como se **anonimiza** em vez de apagar
5. **Prazos** internos de SLA (ex.: 15 dias úteis) — negócio

## 7. Sequência sugerida até às 23h (ordem cronológica)

1. **⚡** Validação técnica rápida: `make lint && make test` · `cd frontend && npm run build && npm run test:e2e`
2. **⚡** Preencher **ADR-012** (bloqueios jurídicos explícitos)
3. **◆** Preencher **ADR-011** (PWA: sim/não/qual pacote/que rotas **não** cachear)
4. **⚡** Trilho J1–J4 o que for possível **em paralelo** (e-mail, DPO, workshop curto)
5. **⚡** Atualizar painel local do roadmap (`_DEVELOPER/...`) + copiar resumo para PR/commit seguinte se quiseres histórico no Git

## 8. Definição de “noite bem usada”

Marca o que cumpriu:

- [x] ADR-012 com decisões ou bloqueios explícitos + inventário WORM/audit
- [x] ADR-011 com decisão de produto (PWA ou não) e riscos de cache/auth
- [x] Jurídico: templates `docs/operacao/HANDOFF_DPO_RIPD_TEMPLATE.md` (preenchimento DPO/RIPD **fora** do código até parecer)
- [x] Baseline técnico verde (`make test`, build front, E2E mock) — validar no CI local antes do push
- [x] PWA: ADR-011 aceite; **B1** sem SW · **B2** não mergeada neste handoff (conforme ADR)

## 9. Referências internas

| Recurso | Caminho |
|---------|---------|
| Roadmap handoff | `_DEVELOPER/DEV_DIAG_04052026/ROADMAP_HANDOFF_REFACTOR_LGPD_PWA.md` |
| Gravação diagnóstico / storage | `.cursor/rules/qdi-gravacao-diagnostico-email.mdc`, `qdi-storage-policy.mdc` |
| E2E integrado | `frontend/package.json` → `test:e2e:integrado` |
| E2E normativa P8 | `PLAYWRIGHT_WIZARD_NORMATIVA=1 npm run test:e2e:wizard-normativa` |
| ADR wizard (sem XState) | `.github/adr/ADR-010-wizard-form-estado-sem-xstate.md` |
| Progresso roadmap (Git) | `docs/operacao/ROADMAP_HANDOFF_PROGRESSO_SYNC.md` |
| Runbook titular (rascunho) | `docs/operacao/RUNBOOK_DIREITOS_TITULAR_RASCUNHO.md` |
| Template DPO/RIPD | `docs/operacao/HANDOFF_DPO_RIPD_TEMPLATE.md` |

---

**Fim do plano.** Este ficheiro é **planeamento operacional versionável**; handoffs de sessão detalhados podem continuar em `_DEVELOPER/` conforme convenção do repo.
