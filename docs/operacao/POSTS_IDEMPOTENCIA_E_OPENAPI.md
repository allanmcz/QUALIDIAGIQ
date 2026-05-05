# POSTs sob `/diagnosticos/` — Idempotency-Key e OpenAPI

## Mecanismo

O **`IdempotencyMiddleware`** (`src/presentation/api/middleware/idempotency.py`) exige o header **`Idempotency-Key`** em **todos** os **POST** cujo path começa por **`/diagnosticos/`** (inclui rotas aninhadas como rascunho self-service, quadro, M12, etc., salvo evolução futura documentada).

- Resposta repetida com a mesma chave e o mesmo contexto de autenticação devolve **`X-Idempotent-Replay: true`** quando aplicável.
- Detalhe de validação: header ausente → **400** com mensagem explícita.

## OpenAPI / Swagger

Rotas POST documentadas em `diagnostico_router.py` referenciam Idempotency-Key na **description** e/ou parâmetro **Header** onde o router expõe explícito.

## Testes de regressão

- `tests/unit/presentation/test_idempotency_middleware.py` — ausência de chave, replay, tenants distintos.
