# ADR-020 — Go-live: risco residual JWT em `localStorage` (complemento ADR-004)

Data: 2026-05-11  
Estado: **aceite para MVP** (QDI-H-034 — fase curta)

## Contexto

O MVP do painel armazena JWT em **`localStorage`**, o que expõe o token a scripts maliciosos (classe XSS). A mitigação completa é cookie **HttpOnly** + BFF (**ADR-004**).

## Decisão de go-live (Beta)

1. Aceitar risco **residual documentado** até Onda **1.1**, desde que:
   - `npm audit` / gitleaks no CI (**ADR-016**);
   - erros do proxy Next não vazem stack (**QDI-H-036**);
   - Sentry com scrub (**QDI-H-016**);
   - pentest (**QDI-H-028**) sem P1 aberto sem compensação.
2. Copy de produto **não** prometer «sessão inviolável» enquanto ADR-004 não estiver implementado.

## Consequências

- Ata de go-live deve listar explicitamente «JWT em localStorage — ADR-020» como risco aceite.
- Onda 1.1 remove o token sensível do `localStorage` ou documenta exceção aprovada pelo PO.

## Referências

- **ADR-004** — roadmap técnico HttpOnly.
- `.cursor/rules/qdi-lexico-plataforma.mdc`
