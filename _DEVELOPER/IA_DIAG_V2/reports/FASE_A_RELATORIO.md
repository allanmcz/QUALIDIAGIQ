# FASE_A_RELATORIO — Estabilizacao Ollama

> **Data:** 2026-05-17 (UTC 2026-05-18 ~01:07)  
> **Executor:** Agente Cursor (handoff Allan — descanso)  
> **Status:** **Go com ressalva**

## 1. Versao

Comando:

```bash
ollama --version
```

Resultado:

```text
ollama version is 0.21.0
Warning: client version is 0.20.4
```

**Ressalva:** divergencia client (0.20.4) vs server (0.21.0). Recomendado `brew upgrade ollama` quando Allan retornar (nao executado neste handoff para nao alterar ambiente sem supervisao).

## 2. Modelos instalados

Comando:

```bash
ollama list
```

Resultado (host CLI — lista completa):

```text
mxbai-embed-large:latest    669 MB
qwen2.5-coder:14b           9.0 GB
qwen2.5-coder:7b            4.7 GB
qwen2.5:32b-instruct        19 GB
llama3.2:latest             2.0 GB
qwen2.5-coder:32b           19 GB
deepseek-coder-v2:latest    8.9 GB
gpt-oss:120b                65 GB
deepseek-r1:8b              5.2 GB
deepseek-r1:70b             42 GB
gemma3:12b                  8.1 GB
```

**Nota:** `curl /api/tags` na mesma porta devolve subconjunto (`qdi-assistant`, `mxbai-embed-large`, `llama3`) — indica **dois servidores** na porta 11434 (ver secao 5).

## 3. API local

Comando:

```bash
curl -s http://localhost:11434/api/tags
```

Resultado:

```text
JSON valido com models[] (qdi-assistant:latest, mxbai-embed-large:latest, llama3:latest, ...)
```

**Gate:** API responde — **OK**.

## 4. Smoke test

Modelo usado:

```text
llama3.2:latest (via POST /api/generate — CLI `ollama run` travou >5 min)
```

Pergunta:

```text
Responda em PT-BR, em uma frase: qual e o objetivo do QDI?
```

Resposta:

```text
O QDI (Questão de Introdução) é um exame administrado para avaliar a aptidão dos candidatos
a trabalhar como auditores internos no Brasil...
```

**Analise:** resposta em PT-BR, latencia ~16s apos cold load (~15s load). **Conteudo errado** para dominio QualiDiagIQ (alucinacao generica) — esperado em modelo sem Modelfile; reforca necessidade de `qdi-assistant` + RAG (Fases C/D).

Metricas API:

```text
total_duration: ~16s
load_duration: ~14.9s
eval_count: 72
```

## 5. Portas e processos

Comandos:

```bash
lsof -nP -iTCP:11434 -sTCP:LISTEN
lsof -nP -iTCP:11435 -sTCP:LISTEN
```

Resultado:

```text
11434: com.docke (Docker qdi-ollama) *:11434
11434: ollama (PID nativo) 127.0.0.1:11434
11435: nenhum
```

**Ressalva critica:** dois listeners na **mesma porta** (Docker + processo nativo). Pode causar `ollama run` interativo travar ou listas de modelos divergentes. **Acao recomendada:** parar um dos dois (`brew services stop ollama` OU `docker compose stop ollama`) e manter apenas o servico usado pelo QDI (`docker compose` alinha com `make dev`).

Container Docker:

```text
qdi-ollama  Up 2h (healthy)  0.0.0.0:11434->11434
```

## 6. Problemas encontrados

| # | Problema | Severidade |
|---|----------|------------|
| 1 | Client/server Ollama 0.20.4 vs 0.21.0 | Media |
| 2 | Dois processos na porta 11434 | Alta |
| 3 | `ollama run` CLI travou; API HTTP funcionou | Media |
| 4 | Smoke sem persona QDI alucinou significado de "QDI" | Baixa (esperado) |

## 7. Decisao

| Criterio | Resultado |
|---|---|
| API respondeu | Sim |
| Modelo respondeu (via API) | Sim |
| Sem servidor duplicado critico | **Nao** — duplicidade documentada |
| Sem travamento recorrente na API | Sim |

Decisao final:

```text
Go com ressalva — prosseguir Fase B via API HTTP (scripts/ia_diag_v2_fase_b_benchmark.py).
Antes de integracao produto, unificar instancia Ollama (Docker OU nativo, nao ambos).
```

## 8. Proximo passo

- Fase B em execucao: `reports/fase_b_raw.json` + `FASE_B_BENCHMARK_MODELOS.md`
- Allan: alinhar Ollama unico + `brew upgrade ollama` se desejar eliminar warning de versao
