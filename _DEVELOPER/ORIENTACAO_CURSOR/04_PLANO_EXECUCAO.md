# Plano de Execução S0.5 → S4 — QDI no Cursor

| Campo | Valor |
|---|---|
| **Janela total** | 02/05/2026 (sáb) → 30/06/2026 (ter) — **9 semanas** |
| **Capacidade líquida** | 5,5h/dia × 5 dias × 9 semanas = **247h** |
| **Aceleração IA (Cursor + Claude)** | 2,0× → **~420h equivalentes** |
| **Demanda Onda 1.0** | ~150h equivalentes |
| **Folga programada** | 60-65% — generosa |
| **Versão** | 1.0 |

---

## 1. Visão geral cronológica

```
S0.5 │ 02-04/mai │ Hardening (12 P0)              │ ~22h IA
 S1  │ 04-15/mai │ Domain core + Wizard 25-40     │ ~50h IA
 S2  │ 18-29/mai │ Score Engine + ABNT 17301      │ ~50h IA
 S3  │ 01-12/jun │ PDF + Lead-magnet + Cross-sell │ ~50h IA
 S4  │ 15-30/jun │ Beta privado + bug fixing      │ ~40h IA
══════════════════════════════════════════════════
Total ~212h IA · capacidade 420h · folga ~50%
```

---

## 2. SPRINT S0.5 — HARDENING (02-04/mai/2026)

> **Objetivo único:** zerar os 12 P0 da auditoria antes da S1 oficial.

### 2.1 Sexta-feira 01/05 — feriado do Trabalhador (OFF)

Descanso obrigatório. Sem código.

### 2.2 Sábado 02/05 — manhã (5h líquidas)

#### Bloco 1 — Schema SQL e RLS (08:00-09:30, 1h30)

**Objetivo:** consolidar fonte única de verdade do schema com RLS efetivo.

**Tarefas (P0-12 + P0-05):**

```bash
# 1. Criar estrutura de migrations
mkdir -p src/infrastructure/db/migrations/

# 2. Migrar conteúdo unificado (cole no Cursor)
```

**Prompt para Cursor (Cmd+L):**

```
Tarefa: consolidar schemas SQL em fonte única com RLS efetivo

Camada Clean Arch: infrastructure/db/migrations/
Princípios NN aplicáveis: §10.1 (Multi-tenant RLS), §10.4 (WORM)

Especificação:
- Criar 0001__criar_tabela_diagnosticos.sql unificando init.sql + 001_initial_schema.sql
- Adicionar coluna `plano` (do init.sql) + `hash_sha256 CHAR(64)` (para WORM)
- Adicionar coluna `score_completo JSONB` para auditabilidade (§10.11)
- Adicionar coluna `versao_otimista INT DEFAULT 1` (lock otimista)
- Adicionar `CONSTRAINT chk_status` (do 001_initial)
- Adicionar `vigencia_inicio TIMESTAMPTZ` em tabelas de regras
- Habilitar RLS com policies SELECT/INSERT/UPDATE/DELETE
- Policy usa `auth.jwt() ->> 'tenant_id'`, NÃO `auth.uid()`
- Criar trigger `block_update_finalizado` (§10.4)

- Criar 0002__criar_tabela_admins.sql
- Criar 0003__criar_tabela_perguntas.sql (com vigencia_inicio/fim)

Entregáveis:
- src/infrastructure/db/migrations/0001__criar_tabela_diagnosticos.sql
- src/infrastructure/db/migrations/0002__criar_tabela_admins.sql
- src/infrastructure/db/migrations/0003__criar_tabela_perguntas.sql
- Atualizar docker-compose.yml para montar migrations/ via supabase-cli
- Deletar init.sql (raiz) — referência morta

Commit: arch(qdi-infra): ADR-002 consolidar schema SQL com RLS efetivo
```

**Validação:**

```bash
make down && make dev
docker exec qdi-db psql -U postgres -d postgres -c "\d diagnosticos"
docker exec qdi-db psql -U postgres -d postgres -c "\d+ diagnosticos" | grep "Row Level Security"
# Deve mostrar: "Row Level Security is enabled"
```

**PAUSA 09:30-09:45** (15min hidratação + glicemia)

---

#### Bloco 2 — JWT custom claim + remoção de backdoors (09:45-11:30, 1h45)

**Tarefas (P0-01, P0-02, P0-03, P0-04):**

**Prompt:**

```
Tarefa: substituir auth atual por JWT custom claim com tenant_id

Camada Clean Arch: presentation/api + infrastructure/config
Princípios NN aplicáveis: §10.1 (Multi-tenant), Segurança (S-01..S-06)

Especificação:
- Criar src/infrastructure/config/settings.py com pydantic-settings:
  - jwt_secret_key (env JWT_SECRET_KEY, sem default)
  - jwt_algorithm = "HS256"
  - jwt_expire_minutes = 480 (8h, não 24h)
  - cors_allowed_origins (csv via env)
  - supabase_url, supabase_anon_key

- Refatorar src/presentation/api/routers/auth_router.py:
  - REMOVER linha SECRET_KEY hardcoded
  - REMOVER endpoint /auth/create_admin (mover para CLI)
  - REMOVER backdoor "admin123" (linhas 64-66)
  - Atualizar create_access_token para incluir tenant_id no payload
  - Trocar datetime.utcnow() por datetime.now(UTC)

- Refatorar src/presentation/api/dependencies.py:
  - REMOVER get_tenant_id (header cleartext)
  - CRIAR get_current_user_tenant via HTTPBearer + jwt.decode

- Criar src/scripts/criar_admin.py (CLI para criação de admin)

- Atualizar .env.example sem segredos
- Gerar nova JWT_SECRET_KEY (não cometer):
  python -c "import secrets; print(secrets.token_urlsafe(64))"

Entregáveis:
- src/infrastructure/config/settings.py
- src/presentation/api/routers/auth_router.py (refatorado)
- src/presentation/api/dependencies.py (refatorado)
- src/scripts/criar_admin.py
- .env.example atualizado
- tests/unit/presentation/test_auth_router.py com 5 cenários

Commit: feat(qdi-auth): substituir header cleartext por JWT com tenant_id claim

Refs: `_DEVELOPER/ANALISE_30042026/03_PLANO_ACAO_S05_HARDENING.md` §Bloco 2
```

**Validação:**

```bash
make test  # tests/unit/presentation/test_auth_router.py 5 cenários ok
grep -r "qualidiagiq-super-secret" src/  # deve retornar zero
grep -r "admin123" src/  # deve retornar zero
```

**Pausa almoço 11:30-12:30**

---

#### Bloco 3 — CORS lockdown + idempotência (12:30-13:00, 30min)

**Tarefas (P0-06, P0-10):**

**Prompt:**

```
Tarefa: configurar CORS seguro + middleware de idempotência

Camada Clean Arch: presentation/api/middleware
Princípios NN aplicáveis: §10.3 (Idempotência), Segurança S-05

Especificação:
- Atualizar main.py:
  - CORS com lista explícita via settings.cors_allowed_origins
  - Manter allow_credentials=True
  - allow_headers explícitos (Content-Type, Authorization, Idempotency-Key)
  - Adicionar header de exposição "X-Idempotent-Replay"

- Criar src/presentation/api/middleware/idempotency.py:
  - BaseHTTPMiddleware
  - POST sem Idempotency-Key → 400
  - POST com chave repetida → mesmo body + header X-Idempotent-Replay: true
  - Cache TTLCache (cachetools) com 1h ttl, MVP em memória
  - Em produção (futuro): trocar por Redis

- Registrar middleware no main.py

Entregáveis:
- src/presentation/api/middleware/__init__.py
- src/presentation/api/middleware/idempotency.py
- main.py atualizado (CORS + middleware)
- tests/unit/presentation/test_idempotency_middleware.py com 3 cenários

Commit: feat(qdi-api): adicionar middleware de idempotência e CORS seguro
```

**Encerramento sábado 13:00** — 5h líquidas concluídas.

---

### 2.3 Domingo 03/05 — OFF inegociável

Descanso. **Não codifique.**

---

### 2.4 Segunda 04/05 — manhã (4h líquidas, antes de S1 oficial)

#### Bloco 4 — Bugs runtime + Clean Arch (08:00-09:30, 1h30)

**Tarefas (P0-07, P0-08, P0-09):**

**Prompt:**

```
Tarefa: corrigir bugs runtime + introduzir Port BaseNormativaPort

Camada Clean Arch: application + infrastructure
Princípios NN aplicáveis: Clean Arch (Application sem I/O), §10.7 (citação RAG)

Especificação:

1. Corrigir bug PorteEmpresa.MEDIA (P0-07):
   - src/application/services/consultoria_service.py:44
   - Trocar PorteEmpresa.MEDIA → PorteEmpresa.MEDIO (e adicionar ENTERPRISE)
   - Adicionar tests/unit/application/test_consultoria_service.py com 3 portes

2. Migrar repository para AsyncClient (P0-08):
   - src/infrastructure/repositories/supabase_diagnostico_repository.py
   - Trocar Client síncrono por AsyncClient
   - Adicionar await em todas as chamadas
   - Tratamento de erro com structlog

3. Criar Port + Adapter para BaseNormativa (P0-09):
   - src/application/ports/base_normativa.py (ABC)
   - src/infrastructure/adapters/base_normativa_filesystem.py
   - Adapter recebe path via __init__, com cache LRU
   - Refatorar realizar_diagnostico.py removendo os.path.join + open()
   - Injetar via dependencies.py

Entregáveis:
- 3 testes unit PorteEmpresa (médio/grande/enterprise)
- AsyncClient em todos os repositórios
- Port BaseNormativaPort + adapter
- realizar_diagnostico.py SEM imports de os
- dependencies.py atualizado

Commits:
- fix(qdi-app): corrigir PorteEmpresa.MEDIA → MEDIO em consultoria_service
- refactor(qdi-infra): migrar SupabaseDiagnosticoRepository para AsyncClient
- arch(qdi-app): introduzir BaseNormativaPort para isolar I/O da Application
```

**PAUSA 09:30-09:45**

---

#### Bloco 5 — Limpeza + commit hook (09:45-10:45, 1h)

**Tarefas (P0-11, M-01, M-02):**

**Prompt:**

```
Tarefa: instalar commit-msg hook PT-BR + remover código morto

Camada Clean Arch: infrastructure (cleanup)
Princípios NN aplicáveis: §10.8 (commits PT-BR)

Especificação:

1. Hook commit-msg PT-BR:
   - Criar .githooks/commit-msg com regex
   - Configurar: git config core.hooksPath .githooks
   - Tornar executável: chmod +x

2. Remover código morto (achados auditoria Manus):
   - Deletar src/infrastructure/pdf/generator.py (M-01)
   - Deletar src/infrastructure/email/smtp_email_service.py (M-02)
   - Mover src/infrastructure/templates/* → src/infrastructure/adapters/templates/
   - Atualizar pdf_generator_weasyprint.py: templates_dir
   - Verificar dependencies.py — confirmar adapter ativo

3. Configurar settings.py com env CORS_ALLOWED_ORIGINS

Entregáveis:
- .githooks/commit-msg
- Pastas src/infrastructure/pdf/ e src/infrastructure/email/ removidas
- src/infrastructure/adapters/templates/ com relatorio_diagnostico.html + style.css
- pdf_generator_weasyprint.py com path atualizado

Commits:
- chore(qdi-build): instalar hook commit-msg para Conventional Commits PT-BR
- chore(qdi-cleanup): remover códigos mortos pdf/generator.py e email/smtp_email_service.py

Refs: `_DEVELOPER/ANALISE_30042026/05_COMPARATIVO_MANUS_vs_CLAUDE.md` §7.2
```

---

#### Bloco 6 — Validação final + ADR-001 (10:45-12:00, 1h15)

**Tarefas:**

```bash
# Bateria de validação final S0.5
make test                          # 100% verde
make lint                          # zero warnings
make type-check                    # zero erros
docker compose down && docker compose up -d
curl http://localhost:8000/health  # ok
```

**Criar ADR-001:**

```bash
mkdir -p docs/adrs
cat > docs/adrs/ADR-001-decisoes-fundacionais-s05.md <<'EOF'
# ADR-001 — Decisões fundacionais (Sprint S0.5 Hardening)

**Data:** 2026-05-04 · **Status:** Aceito · **Autor:** Allan + Claude

## Contexto
Auditoria de 30/04/2026 identificou 12 P0 bloqueadores. Esta ADR formaliza
decisões arquiteturais tomadas durante a Sprint S0.5 (02-04/05/2026).

## Decisões

### D-001 — JWT com claim `tenant_id`
Substituído header `X-Tenant-ID` cleartext por JWT custom claim.
Cliente Supabase recebe AsyncClient com `set_session(jwt)`.
Justificativa: §10.1 INSTRUCAO_KICKOFF — multi-tenant dia-1.

### D-002 — Migrations em src/infrastructure/db/migrations/
Eliminado init.sql raiz. Fonte única de verdade.
Versionamento via Supabase CLI ou Alembic (futuro).
Justificativa: §10.4 (WORM) + RLS efetivo.

### D-003 — Padrão de Port: ABC + @abstractmethod
Padronizado todos os ports. Eliminada mistura com Protocol.
Justificativa: legibilidade + analogia com interfaces Delphi.

### D-004 — Estrutura de pastas em minúsculas
Mantida convenção Python idiomática (PEP 8).
DIVERGE da §10.9 INSTRUCAO_KICKOFF (que pediu PT-MAIÚSCULAS).
Justificativa: ferramentas (mypy, pytest) tratam maiúsculas como classes.
Documentação a atualizar — INSTRUCAO_KICKOFF v1.1.

### D-005 — Idempotência via middleware in-memory (MVP)
TTLCache 1h. Trocar por Redis em produção.
Justificativa: §10.3 + simplicidade MVP.

### D-006 — LLM primário Anthropic Claude Sonnet 4.6
Ollama vira DEV-only. OpenAI vira fallback batch.
Justificativa: stack canônica + qualidade RAG citável.

### D-007 — Commits PT-BR via hook commit-msg
Conventional Commits com escopo `qdi-*`.
Hook bloqueia inglês.
Justificativa: §10.8.

## Consequências
- ✅ RLS multi-tenant funcional
- ✅ Segurança hardening completa
- ✅ 12 P0 zerados
- ⚠️ INSTRUCAO_KICKOFF §10.9 a atualizar para refletir D-004
- ⚠️ Custo Anthropic vs Ollama em prod a monitorar (S2-S3)

## Próximas ADRs
- ADR-002 — Schema SQL consolidado com RLS (concluído nesta S0.5)
- ADR-003 — Modelo de versionamento normativo (S1)
- ADR-004 — Estratégia de Lexiq (S1)
EOF
```

**Commit:**

```bash
git add docs/adrs/ADR-001*.md
git commit -m "arch(qdi-docs): publicar ADR-001 com 7 decisões fundacionais da S0.5

Refs: `_DEVELOPER/ANALISE_30042026/05_COMPARATIVO_MANUS_vs_CLAUDE.md`
"
```

**Encerramento segunda 12:00** — S0.5 completa. **9h líquidas usadas.**

---

### 2.5 Critérios de aceitação S0.5

- [ ] 12 P0 da auditoria resolvidos com commits em PT-BR
- [ ] `make test` retorna 100% verde
- [ ] `make lint` zero warnings
- [ ] `make type-check` zero erros
- [ ] POST `/diagnosticos/` exige JWT com `tenant_id` claim
- [ ] POST `/diagnosticos/` exige `Idempotency-Key`
- [ ] `init.sql` removido; migrations rodam via compose
- [ ] Hook `commit-msg` rejeita mensagens em inglês
- [ ] ADR-001 publicado em `docs/adrs/`
- [ ] Bug `PorteEmpresa.MEDIA` corrigido com teste
- [ ] Camada Application sem `os.path` ou `open()`
- [ ] Códigos mortos M-01 e M-02 removidos

---

## 3. SPRINT S1 — DOMAIN CORE + WIZARD (04-15/mai)

> **Goal:** wizard funcional com 25-40 perguntas adaptativas + score determinístico em 7 dimensões.

### 3.1 S1 — Semana 1 (04-08/mai)

| Dia | Bloco manhã (3h) | Bloco tarde (2,5h) |
|---|---|---|
| Seg 04/05 | Continuar S0.5 (Bloco 6) | Domain entities — Recomendacao + Evidencia |
| Ter 05/05 | Domain entities — Pergunta com vigencia | Domain — testes (cobertura DOMAIN ≥ 87%) |
| Qua 06/05 | RagBaseConhecimentoPort + adapter Lexiq stub | Wizard state machine (LangGraph esqueleto) |
| Qui 07/05 | LangGraph — nodes principais | LangGraph — edges adaptativas (regime/setor/porte) |
| Sex 08/05 | Banco de 35 perguntas em SQL (migration 0004) | **Revisão estratégica 17h** (ritual semanal) |

### 3.2 S1 — Semana 2 (11-15/mai)

| Dia | Bloco manhã (3h) | Bloco tarde (2,5h) |
|---|---|---|
| Seg 11/05 | PerguntaRepository + remoção do hardcode no router | Refatorar diagnostico_router para usar repository |
| Ter 12/05 | Implementar `aplicavel_para` adaptativo no use case | Persistir ScoreCompleto JSONB no banco |
| Qua 13/05 | Tests integration: criar 5 cenários RLS | Tests integration: testcontainers Postgres |
| Qui 14/05 | Refatorar GET /diagnosticos retornar score persistido | LLM Anthropic adapter (substituir Ollama em dev) |
| Sex 15/05 | Bug fixing + cobertura DOMAIN ≥ 90% | **Encerramento S1 17h** + commit master |

### 3.3 Critérios S1

- [ ] Wizard responde 25-40 perguntas adaptativas
- [ ] Score 0-100 calculado em 7 dimensões
- [ ] Pesos versionados (com `vigencia_inicio/fim`)
- [ ] Coverage DOMAIN ≥ 87% (meta progressiva)
- [ ] 5 testes integration RLS verdes
- [ ] LLM Anthropic adapter operacional
- [ ] PerguntaRepository carrega de DB
- [ ] ADR-003 (versionamento normativo) publicado

---

## 4. SPRINT S2 — SCORE ENGINE + ABNT 17301 (18-29/mai)

> **Goal:** motor de score robusto com aderência ABNT 17301 mensurável.

### 4.1 S2 — Semana 3 (18-22/mai)

| Dia | Bloco manhã (3h) | Bloco tarde (2,5h) |
|---|---|---|
| Seg 18/05 | CalcularAderenciaABNT17301 use case | 7 eixos PDCA — dimensão COMPLIANCE_ABNT |
| Ter 19/05 | Recomendações regra-baseadas (8 regras MUST) | Cross-sell engine (QFI/QMI triggers) |
| Qua 20/05 | RAG citável Anthropic — 1ª iteração | Validação score retriever ≥ 0.65 |
| Qui 21/05 | NivelMaturidade calibração com casos reais | Persistência score completo + auditoria |
| Sex 22/05 | Trail de auditabilidade ("explique meu 87") | **Revisão estratégica 17h** |

### 4.2 S2 — Semana 4 (25-29/mai)

| Dia | Bloco manhã (3h) | Bloco tarde (2,5h) |
|---|---|---|
| Seg 25/05 | OpenTelemetry instrumentação inicial | structlog + contextvars (tenant_id em log) |
| Ter 26/05 | OTLP exporter + Jaeger local docker | Métricas Prometheus básicas |
| Qua 27/05 | Hardening de retry/circuit breaker (tenacity + pybreaker) | Tests de chaos (LLM down, DB down) |
| Qui 28/05 | Refatoração + dívida técnica (P2 issues) | Cobertura geral ≥ 82% |
| Sex 29/05 | Bug fixing + smoke test E2E | **Encerramento S2 17h** |

### 4.3 Critérios S2

- [ ] CalcularAderenciaABNT17301 com 7 eixos PDCA
- [ ] Recomendações cross-sell (8 regras + 3 testes integ)
- [ ] RAG citável Anthropic operacional (sem alucinação)
- [ ] Trilha auditável persistida (cliente recupera "como cheguei a 87")
- [ ] OpenTelemetry exporta para Jaeger local
- [ ] structlog com `tenant_id` em 100% dos logs de request
- [ ] Coverage geral ≥ 82%
- [ ] ADR-005 (estratégia RAG Lexiq) publicado

---

## 5. SPRINT S3 — PDF + LEAD-MAGNET + UX (01-12/jun)

> **Goal:** PDF executivo profissional + landing page funcional + cross-sell.

### 5.1 S3 — Semana 5 (01-05/jun)

| Dia | Bloco manhã (3h) | Bloco tarde (2,5h) |
|---|---|---|
| Seg 01/06 | WeasyPrint template HTML profissional | CSS print + branding Tributiq |
| Ter 02/06 | Plotly gráficos: radar 7 dimensões | Plotly: comparativo CBS/IBS vs PIS/COFINS |
| Qua 03/06 | Validação WeasyPrint M2 Max ARM | Testes E2E (PDF não-vazio, ≥8 páginas) |
| Qui 04/06 | Frontend: refatorar 25-40 perguntas dinâmicas | Frontend: integrar wizard com LangGraph backend |
| Sex 05/06 | Frontend: completar 27 UFs + responsivo mobile | **Revisão estratégica 17h** |

### 5.2 S3 — Semana 6 (08-12/jun)

| Dia | Bloco manhã (3h) | Bloco tarde (2,5h) |
|---|---|---|
| Seg 08/06 | Landing page lead-magnet (Next.js) | Captura de email + agendamento |
| Ter 09/06 | Email transacional com PDF anexo | Tests de SMTP (testcontainers MailHog) |
| Qua 10/06 | Dashboard tenant-specific (lista diagnósticos) | RLS testes Frontend |
| Qui 11/06 | Refinos UX + acessibilidade WCAG AA | Lighthouse score ≥ 90 |
| Sex 12/06 | Bug fixing + smoke E2E completo | **Encerramento S3 17h** |

### 5.3 Critérios S3

- [ ] PDF gerado com 8-12 páginas reais (não dummy)
- [ ] Plotly: radar 7 dimensões + comparativos
- [ ] Frontend Wizard com 25-40 perguntas vindas do backend
- [ ] Mobile responsivo (iPhone + Android)
- [ ] Lead-magnet landing page captura email
- [ ] Email transacional envia PDF
- [ ] Dashboard tenant operacional
- [ ] Lighthouse ≥ 90 (Performance, Accessibility, SEO)

---

## 6. SPRINT S4 — BETA + LANÇAMENTO (15-30/jun)

> **Goal:** validação com 5 contadores piloto + lançamento Onda 1.0.

### 6.1 S4 — Semana 7 (15-19/jun)

| Dia | Bloco manhã (3h) | Bloco tarde (2,5h) |
|---|---|---|
| Seg 15/06 | Onboarding Beta privado contador 1 | Coleta de feedback estruturado |
| Ter 16/06 | Onboarding Beta contador 2 | Bug fixing prioridade contador 1 |
| Qua 17/06 | Onboarding Beta contadores 3-4 | Bug fixing prioridade contador 2 |
| Qui 18/06 | Onboarding Beta contador 5 | NPS survey + entrevistas |
| Sex 19/06 | Consolidar feedback dos 5 | **Revisão estratégica 17h** |

### 6.2 S4 — Semana 8 (22-26/jun)

| Dia | Bloco manhã (3h) | Bloco tarde (2,5h) |
|---|---|---|
| Seg 22/06 | Aplicar correções P1 do feedback | Re-deploy + smoke test |
| Ter 23/06 | Aplicar correções P2 do feedback | Documentação pública lead-magnet |
| Qua 24/06 | Hardening final segurança | Pen-test interno |
| Qui 25/06 | Documentação OpenAPI completa | Postman collection oficial |
| Sex 26/06 | Bug fixing + smoke E2E final | **Revisão estratégica 17h** |

### 6.3 S4 — Semana 9 (29-30/jun)

| Dia | Bloco manhã (3h) | Bloco tarde (2,5h) |
|---|---|---|
| Seg 29/06 | Comunicado lançamento (LinkedIn, parceiros) | Monitoramento APM Jaeger |
| Ter 30/06 | 🚀 **LANÇAMENTO ONDA 1.0 às 09:00** | Comemoração + retrospectiva |

### 6.4 Critérios de Lançamento Onda 1.0

- [ ] 5 contadores piloto onboardados e usando ativamente
- [ ] NPS dos pilotos ≥ 50 (ou meta alternativa: ≥3 promotores em 5)
- [ ] Bugs P0 zerados · Bugs P1 ≤ 3
- [ ] Smoke test E2E verde (wizard completo + PDF gerado)
- [ ] Coverage geral ≥ 80% (DOMAIN ≥ 85%)
- [ ] CI/CD GitHub Actions verde
- [ ] OpenAPI documentação 100%
- [ ] Mobile testado em iPhone + Android
- [ ] RLS multi-tenant validado (5 testes integration)
- [ ] LGPD compliance: termos de uso + RoPA

---

## 7. Rituais e protocolos de saúde

### 7.1 Rotina diária

```
07:30 — Acordar · Glicemia · Café leve
08:00 — Início bloco 1 (3h)
09:30 — Pausa 15min (hidratação)
12:00 — Almoço + descanso 1h30
13:30 — Início bloco 2 (2,5h)
15:00 — Pausa 15min
16:00 — Encerrar código · Revisar plano · git status
17:00 — Atividade pessoal / família
21:00 — Sem código pós este horário
22:00 — Sono (≥ 6h)
```

### 7.2 Sextas — revisão estratégica (17h, semanal)

- Status: o que foi feito esta semana?
- Métricas: cobertura, número de issues fechadas, NPS preliminar
- Bloqueios: o que está travado? Por quê?
- Próxima semana: 3 prioridades concretas
- Atualizar este `04_PLANO_EXECUCAO.md`

### 7.3 Domingo — OFF inegociável

Sem código. Sem repositório. Sem leitura técnica.

### 7.4 Sinais de alerta

Se aparecerem, **PARAR** imediatamente:

- Glicemia > 180 mg/dL ou < 70 mg/dL
- Pressão > 140/90 mmHg
- Sessão > 60 min sem pausa
- Confusão mental, dor de cabeça persistente
- Discussão técnica circular sem progresso > 30 min

---

## 8. Métricas de progresso (acompanhar diariamente)

| Métrica | Meta S0.5 | Meta S1 | Meta S2 | Meta S3 | Meta S4 |
|---|---:|---:|---:|---:|---:|
| Cobertura DOMAIN | 85% | 87% | 88% | 90% | 90% |
| Cobertura geral | 80% | 80% | 82% | 84% | 85% |
| P0 abertos | 0 | 0 | 0 | 0 | 0 |
| P1 abertos | 18 | 8 | 4 | 2 | 0 |
| P2 abertos | 16 | 12 | 8 | 5 | 3 |
| Commits PT-BR | 100% | 100% | 100% | 100% | 100% |
| Princípios não-neg | 5/12 | 8/12 | 10/12 | 11/12 | 12/12 |

Como medir:

```bash
# Cobertura por camada
pytest tests/unit/domain --cov=src/domain --cov-report=term

# Princípios — checklist em `_DEVELOPER/ANALISE_30042026/04_CHECKLIST_PRINCIPIOS_NAO_NEGOCIAVEIS.md`

# P0/P1 — TaskList no Cursor (ou GitHub Issues, se preferir)
```

---

## 9. Plano B — se algo der errado

| Cenário | Mitigação |
|---|---|
| Allan adoece >2 dias | Postergar S4 em 1 semana; reduzir escopo Onda 1.0 para 6 MUST |
| LLM Anthropic indisponível | Fallback Ollama local + GPT-4o-mini batch |
| Validação WeasyPrint quebra em ARM | Fallback: gerar PDF via Chrome headless temporariamente |
| Contador piloto não engaja | Buscar 5 novos via LinkedIn / WhatsApp em S3 |
| LC 214 sofre alteração | Atualizar Lexiq em 24h via migration de versionamento |
| Bug P0 descoberto em S4 | Postergar feature MUST não-crítica; foco em correção |

---

## 10. Encerramento

Allan, este plano é **executável e calibrado** para sua capacidade real (5,5h/dia × 5 dias × 9 semanas) com **folga de 50%** considerando aceleração IA. Os marcos são realistas e a Sprint S0.5 garante fundação limpa.

**A regra-mãe que sustenta tudo:**

> *"5 cafés com contadores valem mais do que 40h de código."*

Disparar mensagens piloto em **S0** (já passou) ou **S1 manhã** é a alavanca crítica. Sem feedback real, todo este plano é hipótese.

**Sucesso da Onda 1.0 = produto técnico bom + 5 contadores ativos.**

---

**Próximo:** [`05_PROMPTS_OPERACIONAIS.md`](./05_PROMPTS_OPERACIONAIS.md)

**Autor:** Claude · **Versão:** 1.0 · **Data:** 30/04/2026
