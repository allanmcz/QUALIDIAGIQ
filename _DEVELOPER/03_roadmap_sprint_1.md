# Roadmap — Sprint 1 do MVP do QDI

> **Janela:** 30 dias × 3h/dia = ~90h úteis
> **Modo:** dual-track 70% QMI / 30% QDI (ADR-008) — neste sandbox foca QDI ~3h/dia em dias dedicados (Ter, Qui)
> **Equivalente solo:** ~45h dedicadas ao QDI no Sprint 1
> **Objetivo:** API funcional com fluxo questionário → score → relatório PDF (sem IA ainda — IA vem no Sprint 4)

---

## 1. Resumo do Sprint 1

| Semana | Foco | Features (MoSCoW) | Saída esperada |
|--------|------|-------------------|----------------|
| **S1** (dias 1-7) | Setup + Domain | M02 (motor de score) | Domain layer completo + tests ≥ 85% |
| **S2** (dias 8-14) | Application + Infra | M01 (wizard) + M11 (eixos ABNT) | Use cases + repos Supabase |
| **S3** (dias 15-21) | Presentation | M07 (recomendações) + M03 (pesos) | API endpoints com Swagger |
| **S4** (dias 22-30) | Output + Lead | M04 (PDF) + M09 (lead magnet) | Fluxo end-to-end funcional |

---

## 2. Plano Dia-a-Dia

### Semana 1 — Setup + Domain Layer

**Dia 1 (Ter, ~3h):**
- [ ] Inicializar Git: `git init` no diretório `018-QUALIDIAGIQ/`
- [ ] Configurar venv: `make install`
- [ ] Validar VS Code + Claude Code (extensões instaladas)
- [ ] Subir Docker: `make dev` (apenas DB)
- [ ] Validar conexão local Supabase

**Dia 2 (Qui, ~3h):**
- [ ] Implementar `domain/value_objects/score.py` (já existe stub — completar)
- [ ] Tests: `tests/unit/domain/test_score.py`
- [ ] Cobertura ≥ 90% para value objects

**Dia 3 (Ter, ~3h):**
- [ ] Implementar `domain/entities/diagnostico.py` (já existe stub — completar)
- [ ] Tests: completar `test_diagnostico.py` (cobertura ≥ 85%)
- [ ] Implementar 5 cenários de teste por entidade

**Dia 4 (Qui, ~3h):**
- [ ] Implementar `domain/repositories/diagnostico_repository.py` (interface — pronta)
- [ ] Implementar `domain/repositories/pergunta_repository.py` (nova)
- [ ] Implementar `domain/repositories/resposta_repository.py` (nova)
- [ ] Tests: mocks dos ports

**Dia 5 (Ter, ~3h):**
- [ ] Implementar `domain/entities/pergunta.py`
- [ ] Implementar `domain/entities/resposta.py`
- [ ] Tests respectivos

**Dia 6 (Qui, ~3h):**
- [ ] Migrar dados-base de TABELAS_TRIBUTARIAS para seeders Supabase
- [ ] Schema SQL inicial (migrations 001_inicial.sql)

**Dia 7 (Ter, ~3h):**
- [ ] Code review com Claude Code (revisar Clean Architecture)
- [ ] Merge da feature M02 (motor de score domain)

---

### Semana 2 — Application + Infrastructure

**Dia 8 (Qui, ~3h):**
- [ ] Implementar `application/use_cases/realizar_diagnostico.py` (já existe stub)
- [ ] Tests: caso de uso com mocks

**Dia 9 (Ter, ~3h):**
- [ ] Implementar `application/use_cases/calcular_score.py` (motor com pesos transparentes)
- [ ] Tests: 5 casos de teste com pesos diferentes

**Dia 10 (Qui, ~3h):**
- [ ] Implementar `application/use_cases/gerar_questionario_adaptativo.py`
- [ ] Lógica de filtro condicional por segmento+regime+porte+UF

**Dia 11 (Ter, ~3h):**
- [ ] Implementar `infrastructure/repositories/supabase_diagnostico_repository.py` (já existe stub)
- [ ] Tests: integração com Supabase local

**Dia 12 (Qui, ~3h):**
- [ ] Implementar `infrastructure/repositories/supabase_pergunta_repository.py`
- [ ] Implementar `infrastructure/repositories/supabase_resposta_repository.py`

**Dia 13 (Ter, ~3h):**
- [ ] Implementar dimensão `COMPLIANCE_ABNT` (eixos PDCA × 7 eixos da norma)
- [ ] Tests: validação cobertura completa dos 7 eixos

**Dia 14 (Qui, ~3h):**
- [ ] Code review semana 2
- [ ] Merge das features M01 + M11

---

### Semana 3 — Presentation Layer

**Dia 15 (Ter, ~3h):**
- [ ] Implementar `presentation/api/main.py` (já existe stub)
- [ ] Adicionar middleware de tenant resolver (header X-Tenant-ID)

**Dia 16 (Qui, ~3h):**
- [ ] Implementar `presentation/api/routes/diagnostico.py`
- [ ] Endpoints: POST /diagnosticos, GET /diagnosticos/:id

**Dia 17 (Ter, ~3h):**
- [ ] Implementar `presentation/api/routes/perguntas.py`
- [ ] Endpoints: GET /perguntas (filtrado por contexto)

**Dia 18 (Qui, ~3h):**
- [ ] Implementar schemas Pydantic v2 separados das entities
- [ ] Validação de payloads (CNPJ, UF, etc.)

**Dia 19 (Ter, ~3h):**
- [ ] Implementar geração determinística de recomendações (regras simples)
- [ ] Tests: 10 cenários típicos

**Dia 20 (Qui, ~3h):**
- [ ] Manifesto público de pesos (`docs/MANIFESTO_PESOS.md`)
- [ ] Endpoint público: GET /metodologia (transparência radical)

**Dia 21 (Ter, ~3h):**
- [ ] Code review semana 3
- [ ] Merge das features M07 + M03

---

### Semana 4 — Output + Lead Magnet

**Dia 22 (Qui, ~3h):**
- [ ] Implementar `infrastructure/pdf/weasyprint_generator.py`
- [ ] Template Jinja2 base (`templates/relatorio.html`)

**Dia 23 (Ter, ~3h):**
- [ ] Estilizar PDF (CSS print-friendly)
- [ ] Cabeçalho + rodapé + paginação

**Dia 24 (Qui, ~3h):**
- [ ] Implementar `application/use_cases/gerar_relatorio.py`
- [ ] Integração WeasyPrint com Supabase Storage

**Dia 25 (Ter, ~3h):**
- [ ] Implementar lead capture form (frontend Next.js — basic)
- [ ] Endpoint: POST /leads (cria tenant + diagnóstico)

**Dia 26 (Qui, ~3h):**
- [ ] Implementar envio de e-mail (link do relatório)
- [ ] Adapter SMTP (em dev: MailCatcher)

**Dia 27 (Ter, ~3h):**
- [ ] Testes E2E (Playwright): fluxo completo lead → relatório
- [ ] Bug fixing

**Dia 28 (Qui, ~3h):**
- [ ] Documentação API (OpenAPI / Swagger UI personalizado)
- [ ] README detalhado

**Dia 29 (Ter, ~3h):**
- [ ] Code review final
- [ ] Performance check (latência P95 < 500ms)

**Dia 30 (Qui, ~3h):**
- [ ] **Demo Sprint 1** — gravar vídeo de 5 min
- [ ] Retrospectiva: o que funcionou + o que ajustar
- [ ] Planejamento Sprint 2 (IA + RAG)

---

## 3. Critérios de Aceitação do Sprint 1

- [ ] **Cobertura de testes domain ≥ 85%**
- [ ] **5 cases de calibração** com scores plausíveis (varejo, indústria, serviços, agro, saúde)
- [ ] **API documentada** com Swagger UI acessível
- [ ] **Fluxo end-to-end** funcional: lead → questionário → score → PDF → e-mail
- [ ] **Manifesto público** de pesos publicado em `/metodologia`
- [ ] **7 dimensões** implementadas (incluindo Compliance ABNT)
- [ ] **CI green** em GitHub Actions (quando promovido para `02_PRODUTOS/`)

## 4. Riscos do Sprint 1

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| Setup Supabase local gerar problemas (Apple Silicon) | Média | Usar OrbStack + imagem `supabase/postgres:15.6.1.146` |
| Calibração de pesos demorar mais que previsto | Alta | Não calibrar definitivamente — Sprint 1 usa pesos provisórios |
| WeasyPrint Apple Silicon instalação | Média | Container Docker isola a complexidade |
| Allan ter dia ruim (saúde) | Média | Pular para próximo dia da rotação Ter/Qui — não acumular |
| Frontend Next.js consumir tempo demais | Alta | MVP usa apenas form HTML simples; Next.js completo no Sprint 2 |

## 5. O que NÃO Fazer no Sprint 1

- ❌ Implementar LLM/RAG (Sprint 4)
- ❌ Conectar Winthor (Sprint 8+)
- ❌ Benchmark setorial multi-tenant (Sprint 6)
- ❌ Frontend Next.js completo com shadcn/ui (Sprint 2)
- ❌ Calibração final de pesos (Sprint 5+ com cases reais)
- ❌ Promoção para `02_PRODUTOS/QDI-DIAGNOSTICO_FISCAL/SRC/` (após validação MVP)

## 6. Próximo Passo Imediato

```bash
cd /Users/allan/GD_TRIBUTOLAB/014-SAAS_REFORMA/DIAGNOSTICO_REFORMA_MANUS/05_PROPOSTA_018_QUALIDIAGIQ/018-QUALIDIAGIQ
code .          # ou: claude
```

No VS Code:
1. Aceitar instalação das extensões recomendadas (popup)
2. Cmd+Shift+P → "Python: Select Interpreter" → `./.venv/bin/python` (após `make install`)
3. Abrir `.claude/CLAUDE.md` para entender o contexto carregado
4. Iniciar Dia 1 do roadmap acima
