# Handoff QualiDiagIQ — próxima sessão (agente / Allan)

> **Propósito:** retomar trabalho sem depender da memória do chat (sessões noturnas, outro assistente, ou você após pausa).  
> **Atualizado:** 2026-04-30  
> **Local canônico:** `docs/HANDOFF_PROXIMA_SESSAO_QDI.md` (versionado no Git).

---

## 1. Estado recente do codebase (resumo)

- **WORM + evidência:** migrações `0005`, `0006`; campos `hash_sha256`, `score_completo`, `versao_otimista`; `PATCH` relatório com **`If-Match`** (lock otimista).
- **Catálogo de perguntas:** JSON em `src/infrastructure/questionario/data/perguntas_mvp.json` + loader `json_banco_loader.py`; router usa cache por processo (`carregar_banco_mvp()`).
- **Testes:** `make lint`, `mypy src/`, `pytest` devem passar; integração Postgres WORM em `tests/integration/test_worm_postgres.py` (marca `postgres`).
- **MoSCoW / lacunas:** ver lista objetiva já discutida — principal gap MVP = **35 perguntas** (`docs/refs/05_QUESTIONARIO_v1.md`), outputs M04–M08, RAG Lexiq (Beta).

---

## 2. Como acelerar com agente “à noite” (expectativa realista)

1. O agente **não roda sozinho** após fechar o Cursor; use uma **sessão Agent** com prompt fechado até terminar, ou **Cloud Agents / CI** no GitHub se disponível no plano.
2. Trabalhar sempre em **branch** `feat/qdi-…`; **não fazer push/rebase/merge** sem confirmação explícita do Allan (regra do projeto).
3. Ao terminar cada bloco: `make lint`, `make format`, `make test` (ou equivalentes), `mypy src/`.
4. **Commit** Conventional em PT-BR quando Allan revisar (ex.: `feat(qdi-api): endpoint questionário adaptativo`).

---

## 3. Fila priorizada para próximas sessões (blocos isolados)

Cada bloco = uma sessão focada; não misturar dois blocos sem necessidade.

| ID | Escopo | Pronto quando |
|----|--------|----------------|
| **A** | `GET /diagnosticos/questionario` — perfil empresa (query ou body) → lista aplicável via `GerarQuestionarioAdaptativoUseCase` + `carregar_banco_mvp()` | Contrato OpenAPI + testes integration/unit; front pode consumir depois |
| **B** | Expandir `perguntas_mvp.json` com **lote 1** do doc `docs/refs/05_QUESTIONARIO_v1.md` (ex.: 21 núcleo), IDs UUID estáveis novos documentados | Loader continua verde; smoke POST diagnóstico com subset de IDs |
| **C** | Estender domínio `TipoPergunta` / parsing se o doc exige BINÁRIA, MÚLTIPLA_ESCOLHA, CHECKLIST | `CalcularScoreUseCase` e testes domain atualizados |
| **D** | OpenTelemetry mínimo no `lifespan` do FastAPI + spans nas rotas principais | Dependências já no `pyproject`; sem regressão de testes |
| **E** | Idempotência **persistente** (tabela Postgres + migração), substituindo TTL só em memória | POST replay sob restart de processo; RLS/tenant coerente |

**Fora de escopo noturno sem Allan:** RAG Lexiq completo, LangGraph, conector Winthor, decisões de produto ambíguas.

---

## 4. Prompt modelo (colar no Agent)

```
Branch: feat/qdi-<nome-curto> (criar localmente).

Escopo: apenas o bloco <A|B|C|D|E> descrito em docs/HANDOFF_PROXIMA_SESSAO_QDI.md seção 3.

Não fazer: git push, escopo fora do bloco, refactors cosméticos amplos.

Ao terminar: make lint; make test; mypy src; listar arquivos alterados e critérios "pronto quando" cumpridos.
```

---

## 5. Documentos obrigatórios de contexto (antes de codar features)

1. `docs/refs/01_PRD_BASE.md`  
2. `docs/refs/02_MOSCOW_FEATURES.md`  
3. `docs/refs/05_QUESTIONARIO_v1.md`  
4. `docs/refs/04_METODOLOGIA.md`  
5. `docs/01_arquitetura.md`  
6. `docs/02_dominio_qdi.md`  

---

## 6. Próximo passo recomendado

Executar **bloco A** (`GET` questionário adaptativo) — maior desbloqueio para o wizard Next.js sem esperar as 35 perguntas completas.

---

## 7. Pós-implementação (Allan)

- [ ] Revisar diff  
- [ ] `make test` local  
- [ ] Commit PT-BR  
- [ ] Atualizar este handoff (secção 1 + marcar bloco concluído)
