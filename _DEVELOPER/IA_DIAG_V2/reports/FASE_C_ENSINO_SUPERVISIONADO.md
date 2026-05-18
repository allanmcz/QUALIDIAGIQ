# FASE C — Ensino Supervisionado (10 casos)

> **Status:** Pre-preenchido para validacao de Allan  
> **Data:** 2026-05-17  
> **Rubrica:** media >= 2.5 aprova; ver `ENSINO_SUPERVISIONADO_QDI.md`

Cada caso abaixo traz **resposta esperada canonica** (promover para contexto apos aprovacao).

---

## SUP-001 — Escopo QDI

**Pergunta:** O que fica fora do MVP do QDI?

**Resposta esperada:**

```text
Fora do MVP: apuracao CBS/IBS continua (QAI), split payment (QFC), auditoria continua de motores (QMI),
defesa de auto de infracao, recuperacao ativa pre-CBS (RestituIQ). Dentro: diagnostico 0-100,
questionario adaptativo, score auditavel, plano de acao, PDF, painel consultor, self-service OTP.
```

**Promover para memoria:** `scope.md` — lista MoSCoW WON'T.

---

## SUP-002 — Clean Architecture

**Pergunta:** Onde fica uma regra pura de score?

**Resposta esperada:**

```text
Regra pura e invariantes: src/domain/ (value objects, entidades, servicos de dominio).
Orquestracao e persistencia: src/application/ (use case) + port; adapter em infrastructure.
Nunca no router FastAPI.
```

---

## SUP-003 — Adapter LLM

**Pergunta:** Criar adapter novo ou auditar existente?

**Resposta esperada:**

```text
Auditar e evoluir: src/domain/ports/llm_gateway.py, gateway_router.py, llm_ollama.py,
llm_langgraph_ollama.py. Nao criar adapter paralelo sem ADR (IA_DIAG_V2 ADR-IA-001).
```

---

## SUP-004 — Fonte

**Pergunta:** Pode responder CBS/IBS sem fonte?

**Resposta esperada:**

```text
Nao. Resposta tributaria exige citacao (LC 214/2025, EC 132/2023, NT 2025.002, ABNT quando aplicavel)
ou declarar "base insuficiente" (DP-006). Sem citacao valida = guardrail rejeita (principio QDI #7).
```

---

## SUP-005 — RAG

**Pergunta:** O que fazer sem fonte primaria suficiente?

**Resposta esperada:**

```text
Responder "base insuficiente para responder com seguranca a partir das fontes locais" e listar lacunas.
Nao inventar aliquota, artigo ou obrigacao. Oferecer consulta a Lexiq quando integrada.
```

---

## SUP-006 — Multi-tenant

**Pergunta:** Como tratar tenant_id em IA?

**Resposta esperada:**

```text
tenant_id sempre do JWT (claim), nunca header cleartext. RAG normativo global (classe A) pode ser shared;
dados de diagnostico e checkpoints futuros isolados por tenant_id + RLS PostgreSQL.
```

---

## SUP-007 — Evidencia

**Pergunta:** Como preservar auditabilidade?

**Resposta esperada:**

```text
Diagnostico finalizado WORM; retificacoes append-only; hash em artefatos; historico LLM em
diagnostico_explicacao_score_llm_historico; respostas materializadas em diagnostico_resposta_questionario.
```

---

## SUP-008 — Stack

**Pergunta:** Quando usar Pydantic v2?

**Resposta esperada:**

```text
Schemas HTTP e DTOs externos: src/presentation (FastAPI). Domain usa dataclass frozen, nao BaseModel.
```

---

## SUP-009 — Tom

**Pergunta:** Como explicar para Allan?

**Resposta esperada:**

```text
PT-BR, tecnico, sem infantilizar. Analogias Delphi/Oracle/Winthor quando ajudam. Quatro perfis:
mentor, arquiteto, pair programmer, instrutor.
```

---

## SUP-010 — Roadmap

**Pergunta:** Qual fase antes de integrar ao produto?

**Resposta esperada:**

```text
A estabilizar Ollama → B benchmark → C memoria supervisionada → D RAG piloto com citacao →
Go/No-Go → E integracao gateway (Onda IA 1.1). Nao pular para src/ sem Fase B+D verdes.
```

---

## Checklist Allan (ao acordar)

- [ ] Aprovar ou corrigir cada SUP-001..010
- [ ] Promover regras aprovadas para `.ollama/context/` ou Modelfile (quando existir)
