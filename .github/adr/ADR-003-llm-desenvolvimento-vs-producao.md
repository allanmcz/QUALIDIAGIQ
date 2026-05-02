# ADR-003 — LLM desenvolvimento (Ollama) vs modelo produção (Claude/API)

Data: 2026-05-05  
Estado: aceito MVP

## Contexto

Stack declarada pelo produto menciona modelo primário Claude (Anthropic). O código expõe `OllamaLlmAdapter` para execução self-hosted/offline (**LC 214/2025** — previsibilidade de ambiente deve ser comunicada quando saídas impactam relatório tributário ao cliente).

## Decisão

1. Desenvolvimento / laboratório usa **`OllamaLlmAdapter`** por padrão (`get_llm_service`), configurável por **`OLLAMA_BASE_URL`** (ou `OLLAMA_URL`) e **`OLLAMA_MODEL`**.
2. Produção cliente pago deve documentar modelo **contratado** (Claude/API ou equivalente) em variável de ambiente **`LLM_PROVIDER`** + versão modelo em changelog interno antes de comunicar SLA de precisão.
3. Outputs exibidas ao cliente final da assessoria sempre passam disclaimers já presentes nos textos UX (consultoria tributária, não parecer jurídico).

## Consequências

- Divergências de comportamento Dev vs Produção ficam tratadas como **infra**, não regressão matemática do score (motor de score permanece determinístico).
- Time avalia atualização deste ADR quando tiers **Plus/Pro** tiverem anexo contratual modelo.
