# ADR-016 — Cadeia de suprimento: npm audit (CI) e gitleaks (pre-commit)

Data: 2026-05-11  
**Atualização (postura H-009):** 2026-05-13 — CI com `npm audit --omit=dev --audit-level=high`; tríade quando não há fix; exceção apenas com **ADR** adicional (sem waiver silencioso).  
Estado: **aceite**

## Contexto

O plano de hardening (QDI-H-009, QDI-H-010) exige verificação automática de **vulnerabilidades em dependências npm** e deteção de **segredos** em commits.

## Decisão

1. **CI:** no job `frontend-e2e` (`.github/workflows/ci.yml`), após `npm ci`, executar `npm audit --omit=dev --audit-level=high`. **HIGH** e **CRITICAL** falham o job por defeito (bloqueiam merge). Alinhado a `docs/seguranca/POLITICA_SEGURANCA_INFORMACAO.md`.
2. **Local / pre-commit:** ficheiro `.pre-commit-config.yaml` com hook oficial **gitleaks** (`gitleaks/gitleaks`). Ativação: `pip install pre-commit && pre-commit install` (documentar no README se ainda não existir).

## HIGH sem fix upstream (triage obrigatório)

Quando o **passo 1** (`npm audit --omit=dev`) revelar **HIGH** **sem** correção disponível (situação frequente em pacotes de baixa manutenção ou até em frameworks com advisory sem patch na série instalada), a equipa deve seguir **uma** das vias abaixo, por ordem de preferência:

1. **Substituir o pacote** por um equivalente **ativamente mantido** (melhor caminho).
2. Usar **`overrides`** no `package.json` forçando uma versão segura de uma dependência **transitiva** (caminho cirúrgico), com testes de regressão e nota explícita no PR.
3. **Aceitar o risco** com **supressão documentada** via **novo ADR** (não basta comentário no PR): identificar o advisory (GHSA/CVE), superfície exposta no QDI, mitigações compensatórias, dono e **data de revisão**.

**«Tolerância zero» na prática:** não é absoluta no sentido de proibir qualquer HIGH residual em circunstância extrema; obriga **rito de exceção formal** — merge com HIGH conhecido só após **ADR dedicado** (e, quando couber, entrada em `_DEVELOPER/DECISAO_EXTERNA/PENDENCIA_UPGRADE_NEXT14.md` com issue e prazo).

## Consequências

- O pipeline pode permanecer vermelho até existirem bumps, `overrides` válidos ou ADR de exceção com plano de saída.
- `npm audit` pode gerar falsos positivos ou alertas sem patch — tratar na triagem acima (nunca ignorar sem registo).
- gitleaks exige binário disponível no ambiente do developer (pre-commit descarrega release).

## Referências

- [npm audit](https://docs.npmjs.com/cli/v10/commands/npm-audit)
- [gitleaks](https://github.com/gitleaks/gitleaks)
- [package.json overrides](https://docs.npmjs.com/cli/v10/configuring-npm/package-json#overrides)
