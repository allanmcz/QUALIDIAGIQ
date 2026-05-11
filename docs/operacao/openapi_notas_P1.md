# Notas OpenAPI — ciclo P1 (integradores)

> Rotas com documentação reforçada (summaries, `Field(description)`, exemplos).  
> Ver também `src/presentation/api/schemas.py` (`MetodologiaResponse`, manifesto).

| Rota | O que mudou (resumo) | Para quem importa |
|------|----------------------|-------------------|
| `GET /diagnosticos/` | Query opcional **`empresa_cnpj`** (14 dígitos, DV válido): filtra por `diagnosticos.empresa_cnpj` no tenant do JWT; **`422`** se DV inválido; `limit`/`offset` inalterados | Painel grelha por empresa (`/dashboard/empresas/[cnpj]`), integradores que paginem por PJ |
| `GET /diagnosticos/metodologia` | Resposta tipada `MetodologiaResponse`; texto sobre pesos macro vs catálogo | Front “metodologia”, parceiros que auditem o motor |
| `GET /diagnosticos/manifesto-pesos` | Summary/description no router; campos do item do manifesto documentados | Benchmarking, transparência LC 214/2025 |
| `POST /diagnosticos/` | Description com **Authorization** + **Idempotency-Key** | Integrações na plataforma, gateways |
| `POST /normativa/validar-ancora` | Summary + exemplo de resposta `valido` / `motivo_rejeicao` | Wizard opcional P8, UX de texto livre |

**Export JSON:** `make openapi-export` → `docs/api/openapi.generated.json` (versionado no repositório; CI valida drift).
