# Auditoria — eventos de log recomendados vs código (QDI-H-022)

> Cruzamento entre `docs/operacao/EVENTOS_NEGOCIO_LOGS.md` e chaves **`structlog`** observadas no repositório (amostra; atualizar quando novos fluxos forem adicionados).

## Legenda

| Estado | Significado |
|--------|-------------|
| **Implementado** | Chave presente em código (nome exato ou prefixo estável). |
| **Parcial** | Comportamento coberto por logs genéricos / HTTP, sem chave dedicada. |
| **Pendente** | Recomendado na tabela de eventos, ainda sem instrumentação dedicada. |

## Matriz (amostra)

| Área | Evento recomendado (doc) | Estado | Onde / chave real |
|------|---------------------------|--------|-------------------|
| Auth | `auth_login_sucesso` | Parcial | Login não emite chave única; erros: `admin_sem_hashed_password`, `admin_sem_tenant_id` (`routes_login.py`). |
| Auth | cadastro consultor | Implementado | `cadastro_consultor_b2b_ok` (`routes_cadastro.py`). |
| Auth | JWT inválido | Implementado | `jwt_invalido`, `jwt_self_service_invalido` (`dependencies.py`). |
| Diagnóstico | `diagnostico_criado` | Parcial | Use cases / routers podem não centralizar uma única chave — rever em hardening. |
| PDF | `pdf_geracao_*` | Implementado | `pdf_generator_weasyprint.py` (warnings/errors de geração). |
| Mutação | `diagnostico_mutacao_audit_gravada` | Parcial | Trigger/migração 0026 — confirmar log explícito em adapter se necessário. |
| CNPJ | fallback / erros | Implementado | `cnpj_brasil_api_timeout`, `cnpj_minha_receita_falhou`, etc. (`cnpj_provedor_externo_http.py`). |
| RAG / Lexiq | erros embedding | Implementado | `rag_embedding_openai_falhou`, `rag_pgvector_busca_falhou`, `lexiq_guardrail_rag_erro`. |
| LLM | fallback backend | Implementado | `llm_backend_anthropic_sem_api_key` + `evento=llm_plano_fallback_backend` (`dependencies.py`). |
| Plano painel | materializado ausente | Implementado | `plano_painel_resposta_fallback_motor_legado` (`diagnostico_helpers.py`). |
| Idempotência | backend ativo | Implementado | `idempotency_backend_startup` (`main.py` lifespan). |

## Próximo passo

- Normalizar eventos de diagnóstico (`diagnostico_criado`, `diagnostico_finalizado`) numa única passagem de use cases com nomes estáveis.
- Exportar chaves para o dashboard (QDI-H-024) após Grafana disponível.
