# POSTs com Idempotency-Key — lista explícita + OpenAPI

## Mecanismo

O **`IdempotencyMiddleware`** (`src/presentation/api/middleware/idempotency.py`) **não** aplica-se a todos os POST sob `/diagnosticos/` — apenas aos caminhos **explicitamente listados** em código (lista branca), mais uma **excepção** por padrão de path:

| Critério | Comportamento |
|----------|----------------|
| POST em `/diagnosticos/…/retificacao` (com ou sem `/` final) | **Exige** `Idempotency-Key` (ADR-012 §5 — replay previsível da retificação append-only). |
| POST num dos paths exatos abaixo | **Exige** `Idempotency-Key`. |
| Qualquer outro POST | **Não** é interceptado por este middleware para validação de chave. |

Paths POST atualmente na lista fixa:

- `/diagnosticos`, `/diagnosticos/`
- `/diagnosticos/self-service`
- `/diagnosticos/rascunho-self-service`
- `/diagnosticos/rascunho-self-service/concluir`
- `/diagnosticos/rascunho-self-service/vincular-conta`
- `/diagnosticos/vincular-leads-self-service`, `/diagnosticos/vincular-leads-self-service/`
- `/referencia/cnpj/consulta_cnpj`

- Resposta repetida com a mesma chave e o mesmo contexto de autenticação pode devolver **`X-Idempotent-Replay: true`** quando aplicável (cache Postgres ou memória).
- Header ausente nas rotas cobertas → **400** com mensagem explícita.

## OpenAPI / Swagger

Rotas POST que exigem idempotência devem documentar **`Idempotency-Key`** na **description** e/ou parâmetro **Header** no router (ex.: `diagnostico_core_router`, `cnpj_router`, fluxos self-service).

## Testes de regressão

- `tests/unit/presentation/test_idempotency_middleware.py` — ausência de chave, replay, tenants distintos, inclusão de `/diagnosticos/{uuid}/retificacao`.
