# ADR-018 — Content-Security-Policy (CSP) com nonce no Next.js — spike

Data: 2026-05-11  
Estado: **proposta / spike** (QDI-H-021)

## Contexto

Mitigar XSS (especialmente com JWT em `localStorage`, **ADR-004**) exige CSP estrita; `nonce` por pedido é o padrão moderno para permitir scripts inline controlados no App Router.

## Decisão (spike)

1. Avaliar `middleware.ts` emitindo `Content-Security-Policy` com `script-src 'nonce-{random}'` + hashes para scripts estáticos inevitáveis.
2. Integrar com **Turbopack/Webpack** e `next/script` — documentar exceções (analytics, Sentry browser).
3. **Não** ativar CSP bloqueante em produção sem checklist de regressão visual e E2E.

## Consequências

- Spike pode resultar em PR dedicado pós-MVP ou Onda 1.1.
- Até lá: manter `npm audit`, scrub Sentry (**ADR-016**, QDI-H-016) e proxy com erros genéricos (QDI-H-036).

## Referências

- [MDN — CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- **ADR-004** — roadmap cookie HttpOnly.
