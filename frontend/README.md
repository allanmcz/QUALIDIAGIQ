# Frontend — QualiDiagIQ

> **Status:** MVP App Router ativo (Next 14+) — wizard, dashboard M05/M06/M12 e páginas públicas (`/metodologia`, LGPD).

## E2E integrado (API Python real — C1)

Variáveis típicas no mesmo shell antes de subir Next + Playwright:

- `NEXT_PUBLIC_API_URL` — URL da API (ex.: `http://127.0.0.1:8765`).
- `PLAYWRIGHT_SKIP_WEBSERVER=1` — quando Next já está em background (`npm run dev -p 3333`).
- `PLAYWRIGHT_BASE_URL` / `PLAYWRIGHT_PORT` — base do Next (ex.: `http://127.0.0.1:3333`).
- `PLAYWRIGHT_INTEGRATED=1` — habilita `e2e/dashboard-list-integrado.spec.ts`.

Script auxiliar: `npm run test:e2e:integrado` (ajuste env conforme o host; requer API com `QDI_CI_PLAYWRIGHT_INTEGRATED=1` e Postgres migrado + seed `0005`).

## Armazenamento local (MVP)

O wizard usa **`localStorage`** para rascunho (`wizard_draft`) e fila pós-OTP (`pending_diagnostico`), conforme implementação em `lib/wizard/*`. É uma **exceção conscientemente MVP**: dados ficam no browser até envio à API; roadmap BFF/cookie HttpOnly está em **ADR-004**. Não colocar tokens JWT ou segredos nessas chaves.

| Chave / API | Tecnologia | Uso resumido |
|-------------|------------|--------------|
| `wizard_draft` | `localStorage` | Rascunho do wizard (passos 1–2 e estado parcial). |
| `pending_diagnostico` | `localStorage` | Payload enfileirado após OTP / antes do POST autenticado. |
| `admin_token`, `admin_nome` | `localStorage` | Sessão painel pós-login B2B (MVP — não é modelo-alvo produção). |
| `sessionStorage` (chave interna) | `sessionStorage` | Payload diagnóstico quando o fluxo redireciona a login antes do POST — ver `lib/wizard/pending_diagnostico.ts`. |

## Stack-alvo

- Next.js 14 (App Router)
- React 19
- TypeScript 5.5+
- Tailwind CSS 3.4+
- shadcn/ui
- Anthropic SDK (`@anthropic-ai/sdk`) para chat-tributário
- recharts (radar + heatmap)
- lucide-react (ícones)

## Inicialização (executar uma vez)

```bash
cd frontend
npx create-next-app@14 . --ts --tailwind --app --eslint --no-src-dir
npm install @anthropic-ai/sdk lucide-react @radix-ui/react-progress recharts

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

- **Armazenamento no navegador (excepção MVP):** o fluxo actual usa **`localStorage`** para o token do painel após login (`admin_token`, `admin_nome`) e **`sessionStorage`** para o payload do diagnóstico quando o utilizador é enviado ao login antes do POST (`frontend/lib/wizard/pending_diagnostico.ts`). Isto **não** é o modelo-alvo de produção (cookies httpOnly + backend); está documentado nas páginas de login e deve ser substituído num roadmap de hardening.
- **Tenant ID** em produção deve vir de JWT/cookies seguros — não confiar só em storage JS para dados sensíveis.
- **PDF** é gerado server-side (FastAPI + WeasyPrint), não client-side.
