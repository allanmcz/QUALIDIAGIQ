# ADR-011 — PWA no QualiDiagIQ (Next.js 14): âmbito Onda 1

Data: 2026-05-05  
Estado: **aceite — Onda 1 fase B1** (manifest + metadata; SW em fase B2)

## Contexto

O roadmap (`ROADMAP_HANDOFF_REFACTOR_LGPD_PWA`, parte D) prevê PWA para melhorar experiência mobile **com risco**: service worker interfere em **cache**, **auth** (tokens, BFF/proxy) e **rotas dinâmicas**. Stack: Next.js **14.2** (App Router).

## Opções consideradas

| Opção | Prós | Contras |
|-------|------|---------|
| **A — Sem PWA MVP** | Menor risco | Sem “instalar app” |
| **B — PWA mínimo** em duas sub-fases | **B1:** manifest + ícones + metadata — baixo risco · **B2:** SW (Workbox/`next-pwa`) só após hardening | B2 exige testes manuais login/dashboard/wizard |
| **C — PWA completo** de uma vez | UX tipo app | Regressões silenciosas; **rejeitado** para Onda 1 |

## Decisão

- **Opção escolhida:** **B**, com **B1 implementada agora** e **B2 planeada** (branch dedicada quando houver janela exclusiva).  
- **Motivo:** cumprir instalabilidade parcial / Lighthouse sem introduzir SW antes de política de cache escrita e QA mobile.  
- **Data de revisão:** 2026-08-01 ou antes do primeiro go-live comercial mobile-critical.  
- **Responsável:** Allan Marcio (produto) + pair técnico.

## Restrições de engenharia (B2 — quando implementada)

1. **Não** cachear `/api/*`, `/api-backend/*` nem rotas autenticadas sem política explícita.  
2. Dashboard e páginas pós-login: **network-first** ou **sem cache**.  
3. `/wizard`: regressão obrigatória após qualquer SW.  
4. Touch targets ≥ 44px — cruzar com `e2e/a11y-critical.spec.ts` e QA manual.

## Evidência baseline (handoff)

Executar após alterações front:

```bash
cd frontend && npm run build && npm run test:e2e
```

Registrar resultado no PR ou em `docs/operacao/ROADMAP_HANDOFF_PROGRESSO_SYNC.md` (hash Git).

## Próximos passos (checklist)

- [x] Manifest + metadata + documentação (`frontend/README.md`, este ADR)  
- [ ] Branch `feat/qdi-front-pwa-onda1` — **opcional** até iniciar B2 (SW)  
- [x] **B2 (2026-05-10):** `@ducanh2912/next-pwa` + `next.config.mjs` + exclusões API/`api-backend` + `/offline` · SW **desactivado** quando `CI=true` (Actions / Playwright)  
- [ ] Testes manuais: login → dashboard → wizard feliz **com** SW (build local sem `CI=true`)

## Referências

- Plano: `docs/operacao/PLANO_HANDOFF_JANELA_23H_LGPD_PWA.md`  
- Progresso Git: `docs/operacao/ROADMAP_HANDOFF_PROGRESSO_SYNC.md`  
