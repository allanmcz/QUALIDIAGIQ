# ADR-016 — Cadeia de suprimento: npm audit (CI) e gitleaks (pre-commit)

Data: 2026-05-11  
Estado: **aceite**

## Contexto

O plano de hardening (QDI-H-009, QDI-H-010) exige verificação automática de **vulnerabilidades em dependências npm** e deteção de **segredos** em commits.

## Decisão

1. **CI:** no job `frontend-e2e` (`.github/workflows/ci.yml`), após `npm ci`, executar `npm audit --omit=dev --audit-level=high`. Falhas bloqueiam merge até correção ou exceção documentada.
2. **Local / pre-commit:** ficheiro `.pre-commit-config.yaml` com hook oficial **gitleaks** (`gitleaks/gitleaks`). Ativação: `pip install pre-commit && pre-commit install` (documentar no README se ainda não existir).

## Consequências

- `npm audit` pode gerar falsos positivos ou alertas sem fix imediato — tratar via bump de dependência ou supressão temporária com justificação no PR.
- gitleaks exige binário disponível no ambiente do developer (pre-commit descarrega release).

## Referências

- [npm audit](https://docs.npmjs.com/cli/v10/commands/npm-audit)
- [gitleaks](https://github.com/gitleaks/gitleaks)
