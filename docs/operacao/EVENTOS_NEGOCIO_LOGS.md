# Eventos de negócio e correlação (logs)

## Identificador de pedido

- Header **`X-Trace-Id`** (middleware `trace_context`) — propagado para logs estruturados da API.
- Clientes podem enviar valor externo; caso contrário o servidor gera UUID.

## Eventos recomendados (nível `info` / `warning`)

| Área | Evento (chave sugerida) | Quando |
|------|-------------------------|--------|
| Auth | `auth_login_sucesso` / falha | POST `/auth/login` |
| Diagnóstico | `diagnostico_finalizado` | Use case ``RealizarDiagnostico`` após persistência; ``diagnostico_criado`` / PATCH — alinhar noutros fluxos |
| PDF | `pdf_geracao_ok` / `pdf_geracao_falhou` | Geração WeasyPrint |
| Mutação | `diagnostico_mutacao_audit_gravada` | Auditoria pós-mutação (migração 0026) |
| Idempotência | `idempotency_backend_startup` | Lifespan — backend Postgres ativo (`app.state.idempotency_backend_active`) |
| Plano painel | `plano_painel_resposta_fallback_motor_legado` | Resposta HTTP sem plano materializado na BD (motor legado) |
| LLM | `llm_backend_anthropic_sem_api_key` | Fallback para Ollama quando `QDI_LLM_BACKEND=anthropic` sem chave |

Cruzamento com código: **`docs/operacao/AUDITORIA_EVENTOS_VS_CODIGO.md`** (QDI-H-022).

## OpenTelemetry

Guia local: `docs/operacao/OTEL_QUICKSTART_LOCAL.md`. Variáveis: `OTEL_TRACING_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`, etc. — `README.md` raiz.

## Propagação W3C Trace Context (QDI-H-008)

- O proxy Next (`frontend/app/api-backend/[[...slug]]/route.ts`) repassa **`traceparent`** e **`tracestate`** para a API quando presentes no pedido do browser.
- A API aceita estes cabeçalhos no CORS (`src/presentation/api/main.py`) para permitir correlação ponta-a-ponta com exportadores OTLP.
