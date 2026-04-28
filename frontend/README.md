# Frontend — QualiDiagIQ

> **Status:** scaffold pendente — inicializar com Next.js 14 antes do Sprint 2.

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

- **Não usar localStorage/sessionStorage** — armazenar tudo em React state ou Supabase
- **Tenant ID** vem da URL ou cookie httpOnly (não exposto ao JS)
- **PDF** é gerado server-side (FastAPI + WeasyPrint), não client-side
