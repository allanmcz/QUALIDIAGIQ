# Frontend — QualiDiagIQ

> **Status:** MVP App Router ativo (Next 15.x) — wizard, dashboard M05/M06/M12 e páginas públicas (`/metodologia`, LGPD).

## PWA — Onda 1 (ADR-011)

- **B1 (actual):** `public/manifest.json` + `metadata.manifest` + `viewport.themeColor` em `app/layout.tsx` — sem service worker.  
- **B2 (planeado):** SW com política explícita (**não** cachear `/api-backend`, `/api/*`, rotas autenticadas); branch sugerida `feat/qdi-front-pwa-onda1`.  
- Após alterações PWA: `npm run build` + smoke manual login → dashboard → `/wizard`.

## E2E com mocks do painel (BFF + `/api-backend`)

O `playwright.config.ts` define `NEXT_PUBLIC_API_URL=/api-backend` (por omissão) e `API_PROXY_TARGET` para o proxy do Next alcançar a API. Os specs que simulam login usam `e2e/helpers/mock_bff_painel_auth.ts` (`Set-Cookie` `qdi_painel_access` + corpo `{ ok: true, … }`). Para o passo 1 do wizard, preferir `fillWizardCnpjPasso1` em `e2e/helpers/wizard_cnpj_e2e.ts` (evita flakiness com `react-hook-form`). **Gate reprodutível (CI / sprint hardening):** na raiz do monorepo `make fe-playwright-ci`, ou em `frontend/` `npm run test:e2e:ci` (`CI=1` → 1 worker + retries no `playwright.config.ts`).

## E2E integrado (API Python real — C1)

Variáveis típicas no mesmo shell antes de subir Next + Playwright:

- `NEXT_PUBLIC_API_URL` — URL da API (ex.: `http://127.0.0.1:8765`).
- `PLAYWRIGHT_SKIP_WEBSERVER=1` — quando Next já está em background (`npm run dev -p 3333`).
- `PLAYWRIGHT_BASE_URL` / `PLAYWRIGHT_PORT` — base do Next (ex.: `http://127.0.0.1:3333`).
- `PLAYWRIGHT_INTEGRATED=1` — habilita `e2e/dashboard-list-integrado.spec.ts`.

Script auxiliar: `npm run test:e2e:integrado` (ajuste env conforme o host; requer API com `QDI_CI_PLAYWRIGHT_INTEGRATED=1` e Postgres migrado + seed `0005`).

## Armazenamento local (MVP)

O wizard usa **`localStorage`** para rascunho de UX (`wizard_draft`), pendente legado pós-login (`pending_diagnostico`) e token de resgate OAuth (`rascunho_resgate_token`), conforme `lib/wizard/*` e `.cursor/rules/qdi-storage-policy.mdc`. **Não** usar `sessionStorage` em fluxo novo (há migração única session→local onde ainda existir legado). Diagnóstico concluído self-service: dados na **BD** + **GET** `/diagnosticos/self-service/conclusao-visualizacao` (query `diagnostico_id` + `leitura_token`). Roadmap: autosave do wizard na API e cookies httpOnly (**ADR-004**). Não colocar JWT ou segredos em chaves de rascunho.

| Chave / API | Tecnologia | Uso resumido |
|-------------|------------|--------------|
| `wizard_draft` | `localStorage` | Rascunho do wizard (passos 1–2 e estado parcial). |
| `pending_diagnostico` | `localStorage` | Payload pendente legado até POST autenticado (migrar para rascunho BD quando possível). |
| `qdi_rascunho_resgate_token_v1` | `localStorage` | Token opaco da BD após «Entrar» (redirect perde o `#`). |
| `admin_token`, `admin_nome` | `localStorage` | Metadados / legado do painel; JWT de acesso tende a ir em cookie **httpOnly** (`qdi_painel_access`) via BFF. |

## Sessão do painel (BFF + proxy)

- **Login:** `POST /api/auth/login` (Route Handler) chama a FastAPI, define cookie `qdi_painel_access` (**HttpOnly**, `SameSite=Lax`, `Secure` em produção) e devolve JSON **sem** `access_token` no corpo.
- **Cadastro:** `POST /api/auth/cadastro` — mesma política de cookie e corpo que o login.
- **Logout:** `POST /api/auth/logout` limpa o cookie.
- **Sessão (UX):** `GET /api/auth/session` expõe apenas dados não sensíveis.
- **Chamadas à API:** com `NEXT_PUBLIC_API_URL=/api-backend`, o `app/api-backend/[[...slug]]/route.ts` faz proxy same-origin; se o `fetch` não enviar `Authorization`, o servidor injeta `Bearer` a partir do cookie. Use `credentials: "include"` nos `fetch` ao proxy.
- **Exemplo local:** ver `frontend/.env.local.example` (`API_PROXY_TARGET` + `NEXT_PUBLIC_API_URL=/api-backend`).

## Stack-alvo

- Next.js 15 (App Router)
- React 19
- TypeScript 5.5+
- Tailwind CSS 3.4+
- shadcn/ui
- recharts (radar + heatmap)
- lucide-react (ícones)

> Chamadas a modelos de IA no **browser** não são requisito do MVP: o SDK Anthropic foi **removido** do frontend (**ADR-017**); recomendações usam a API FastAPI.

## Inicialização (executar uma vez)

```bash
cd frontend
npx create-next-app@14 . --ts --tailwind --app --eslint --no-src-dir
npm install lucide-react @radix-ui/react-progress recharts

# Setup shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card form input label select progress dialog
```

Ou rode pelo Makefile:

```bash
make frontend-init
```

## Estrutura prevista (após inicialização)

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                          # landing page (lead magnet)
│   ├── diagnostico/
│   │   ├── novo/page.tsx                 # captura de lead
│   │   ├── [id]/page.tsx                 # questionário adaptativo
│   │   └── [id]/relatorio/page.tsx       # dashboard navegável
│   └── metodologia/page.tsx              # manifesto público de pesos
├── components/
│   ├── ui/                               # shadcn/ui
│   ├── questionario/
│   │   ├── pergunta-card.tsx
│   │   ├── progresso.tsx
│   │   └── wizard.tsx
│   └── relatorio/
│       ├── score-radar.tsx               # recharts
│       ├── heatmap-criticidade.tsx
│       ├── cronograma.tsx
│       └── recomendacoes-list.tsx
├── lib/
│   ├── api.ts                            # cliente HTTP da API FastAPI
│   ├── tenant.ts                         # gestão de X-Tenant-ID
│   └── utils.ts
└── public/
    └── (assets)
```

## Páginas-chave do MVP

| Rota | Função | Sprint |
|------|--------|--------|
| `/` | Landing page com pitch + CTA | 2 |
| `/diagnostico/novo` | Form de captura de lead | 2 |
| `/diagnostico/[id]` | Wizard adaptativo | 3 |
| `/diagnostico/[id]/relatorio` | Dashboard navegável + score 0-100 | 3 |
| `/metodologia` | Transparência dos pesos | 3 |

## Design System

- Cores: Tributiq palette (a definir com Allan — ver `06_LOGOMARCAS/`)
- Tipografia: Inter (default) + JetBrains Mono para números/score
- Espaçamento: Tailwind padrão (escala 4px)

## Notas

- **Armazenamento no navegador (MVP):** `localStorage` para painel e caches de wizard descritos na tabela acima; **proibido** `sessionStorage` em código novo. Resultado pós-conclusão self-service vem da **API** (PostgreSQL), não de storage de sessão.
- **Tenant ID** em produção deve vir de JWT/cookies seguros — não confiar só em storage JS para dados sensíveis.
- **PDF** é gerado server-side (FastAPI + WeasyPrint), não client-side.
