# Checklist rastreável — implementação MVP pós-Docker (dev)

**Criação:** 2026-05-10  
**Objetivo:** lista única para ir marcando item a item o que falta entre **Docker Compose local** (`make dev`), gates automatizados, evidências operacionais e decisões humanas (PDF, RLS, MUST).  
**Fontes:** `docs/operacao/EXECUCAO_DEV_09052026_V2_CHECKLIST_OPS.md`, `docs/operacao/DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md`, `docs/operacao/SMOKE_MVP_FECHADO.md`.

> **Regra:** evidências versionadas sem passwords em texto plano, tokens JWT reais, service role keys nem dumps com dados pessoais.

**Nota sobre decisões consolidadas:** o ficheiro `_DEVELOPER/DEV_09052026_V2/DECISOES_CONSOLIDADAS_DEV_09052026_V2.md` **não está presente neste clone** — se existir noutro ramo ou máquina, sincronizar antes de citar G3 formalmente no Git.

---

## Como usar

- Marcar caixas no editor (`[ ]` → `[x]`).
- Antes de fechar T1.4, garantir T1.1–T1.3 assinaladas ou exceções datadas em `MVP_CRITERIO_CORTE_E_DECLARACAO_MUST.md`.

---

## Pré-voo comum (dev + qualidade)

- [ ] Branch e revisão: `git status --short` e `git rev-parse --short HEAD`
- [ ] Backend: `make lint` e `make test` (ou `make mvp-gate` quando só gates MVP + Postgres)
- [ ] Se mexeu em front no mesmo pacote: `cd frontend && npm run lint`

---

## T1.1 — Gate MVP com Postgres no Docker (`make mvp-gate`)

**Checklist passo-a-passo (executável):** [`CHECKLIST_T1_1_MVP_GATE_DOCKER.md`](./CHECKLIST_T1_1_MVP_GATE_DOCKER.md).

**Objetivo:** mesmo Postgres que o `docker-compose.yml` expõe em desenvolvimento (imagem **pgvector/pgvector:pg16**, migrações), sem obrigar Supabase cloud para o MVP.

**Stack:**

- [x] `make dev` (ou pelo menos `docker compose up -d db`)
- [x] Postgres no host típico: `127.0.0.1:60322`

**Comandos (variáveis — `Makefile` exporta default local se omitidas):**

```bash
export QDI_POSTGRES_TEST_URL="${QDI_POSTGRES_TEST_URL:-postgresql://postgres:postgres@127.0.0.1:60322/postgres}"
export DATABASE_URL="${DATABASE_URL:-$QDI_POSTGRES_TEST_URL}"

make mvp-gate
make verify-schema-mvp-strict
```

**Aceite:**

- [x] `make mvp-gate` verde com Postgres do Docker local
- [x] `make verify-schema-mvp-strict` OK com a mesma URL
- [x] Log datado anexado em `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md` ou artefacto equivalente (sem secrets na evidência) — *evidência em [`CHECKLIST_T1_1_MVP_GATE_DOCKER.md`](./CHECKLIST_T1_1_MVP_GATE_DOCKER.md) §Passo 5 (2026-05-10, `328b13e`).*
- [ ] Opcional pré-go-live público: repetir gate contra **Supabase gerido** e arquivar segunda evidência (G3)

**Referência env:** `.env.example` — secção testes / gates (`QDI_POSTGRES_TEST_URL`).

---

## T1.2 — Cinco PDFs reais e sign-off contábil

**Cases obrigatórios:**

- [ ] Varejo (ex.: supermercado ou drogaria)
- [ ] Indústria (ex.: manufatura)
- [ ] Serviços (ex.: consultoria ou TI)
- [ ] Agro (ex.: produção primária)
- [ ] Saúde (ex.: clínica ou laboratório)

**Por PDF:**

- [ ] Marcadores M04: capa, síntese executiva, dimensões e gaps
- [ ] Blocos dinâmicos: cronograma 5 fases, matriz de impacto, checklist do plano
- [ ] Rodapé: LC 214/2025, EC 132/2023, ABNT NBR 17301:2026
- [ ] PT-BR e acentuação corretas
- [ ] Locale `pt_BR.UTF-8` no render
- [ ] Proteção de quebra na síntese executiva (`page-break-inside: avoid`)

**Aceite:**

- [ ] Cinco PDFs referenciados no checklist B.2 de `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md`
- [ ] Sign-off contábil formalizado (ata datada — responsável definido em `DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md` §2)
- [ ] `docs/operacao/WEASYPRINT_RUNTIME.md` cumprido nos checkpoints aplicáveis

---

## T1.3 — Smoke RLS dois tenants (Postgres Docker local)

**Objetivo:** isolamento multi-tenant no **mesmo** Postgres do Compose (paridade semântica com CI / `make mvp-gate`).

**Passos manuais (evidência humana):**

- [ ] `make dev` ou `docker compose up -d db` + migrações aplicadas
- [ ] Dois tenants / JWTs distintos; API local típica `http://127.0.0.1:60000` (compose)
- [ ] Inserir diagnóstico no tenant A; com JWT do tenant B: `GET /diagnosticos/{id_A}` → `404` ou equivalente documentado
- [ ] Opcional: SQL controlado com `SET qdi.jwt_tenant_id` (role de serviço)

**Aceite:**

- [ ] `docs/operacao/EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md` preenchido com menção explícita **«Postgres Docker Compose — 127.0.0.1:60322»** (ou URL efectiva **sem** secrets)
- [ ] Captura ou nota em `docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md` (sem JWT real no Git)
- [ ] Caixa «Isolamento confirmado» assinalada
- [ ] Opcional: repetir em projeto Supabase cloud antes do go-live público

---

## T1.4 — Declaração MUST 12/12 (assinatura humana)

**Pré-condições:**

- [ ] T1.1 fechado
- [ ] T1.2 fechado
- [ ] T1.3 fechado

**Documento:** `docs/operacao/MVP_CRITERIO_CORTE_E_DECLARACAO_MUST.md`

- [ ] ACT-K01: frase de corte (lançamento vs Beta/SHOULD)
- [ ] ACT-K03: confirmação dos 12 MUST no sentido funcional + auditável mínimo
- [ ] Exceções residuais datadas ou registo explícito «nenhuma»
- [ ] Assinatura humana (Allan ou responsável definido)
- [ ] Hash Git do pacote de evidência registado

---

## T2 — LGPD / DPO / RIPD (paralelo ao técnico)

Resumo alinhado ao checklist operacional completo — detalhe em `EXECUCAO_DEV_09052026_V2_CHECKLIST_OPS.md`:

- [ ] **T2.1** Workshop J4 (WORM × anonimização × eliminação) — `HANDOFF_DPO_RIPD_TEMPLATE.md` §J4
- [ ] **T2.2** DPO designado — §J1 + env front (`NEXT_PUBLIC_LGPD_DPO_*`)
- [ ] **T2.3** RIPD v0.1 — §J2 ou referência em `docs/legal/STATUS_JURIDICO_MVP.md`

**Formulário de decisões:** `docs/operacao/DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md` (secções 5–9).

---

## T4.1 — M08 Lexiq (próximo sprint engenharia)

Critério de aceite futuro (não bloqueia T1 se registado como SHOULD pós-MVP): bullets com `evidencia_lexiq`, rejeição sem citação ou score do retriever abaixo de 0,65, testes e PDF smoke — ver `EXECUCAO_DEV_09052026_V2_CHECKLIST_OPS.md` (secção T4.1).

- [ ] Prioridade M08 confirmada versus SHOULD (`DECISOES_PENDENTES` §10)

---

## Lacunas técnicas / CI (estado do repositório)

Marque quando validado na vossa máquina ou no GitHub:

- [ ] **CI backend:** job corre migrações + `pytest` completo (inclui os mesmos testes que `make mvp-gate` combina); **não** há passo com o nome `make mvp-gate` — paridade é por inclusão nos testes, não pelo alvo Make
- [ ] **Porta Postgres:** CI usa `localhost:5432` (serviço Actions); dev local usa `60322` — ambos válidos após export correcto de `QDI_POSTGRES_TEST_URL`
- [ ] **`make ci-integration`:** exige `POSTGRES_CI_URL` definido manualmente (espelho local do fluxo CI)

---

## Fechamento operacional

- [ ] `docs/operacao/ROADMAP_HANDOFF_PROGRESSO_SYNC.md` atualizado (data, hash, estado real)
- [ ] Changelog / ata da semana: o que ficou manual ou evidência cloud opcional
- [ ] Commit apenas sem artefactos sensíveis
