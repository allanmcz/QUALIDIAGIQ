# ADR-017 — Frontend: dependência `@anthropic-ai/sdk` removida (zero imports)

Data: 2026-05-11  
Estado: **aceite**

## Contexto (QDI-H-006)

O `package.json` do Next.js listava `@anthropic-ai/sdk` por histórico de README / template, mas **nenhum** ficheiro `*.ts` / `*.tsx` importava o SDK — superfície de ataque e `npm audit` desnecessários.

## Decisão

1. Remover a dependência do **frontend**; toda chamada a Claude em produção permanece no **backend** (`AnthropicLlmAdapter`, **ADR-003** / **ADR-007**).
2. Se no futuro existir chat tributário no browser, preferir **BFF** que chama a API FastAPI (sem chave Anthropic em JS).

## Consequências

- `npm audit` no CI deixa de analisar essa cadeia no lockfile do frontend.
- Documentação (`frontend/README.md`, `Makefile` alvo `frontend-init`) alinhada.

## Referências

- **ADR-006** — dependências de IA fora de `src/` (núcleo Python).
