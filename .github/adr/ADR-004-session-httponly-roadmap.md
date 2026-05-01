# ADR-004 — Sessão B2B: `localStorage` (MVP) → cookie HttpOnly + refresh (meta)

Data: 2026-05-05  
Estado: proposta / roadmap (**Fase F** — plano analise §11)

## Contexto

O wizard B2B e o dashboard armazenam JWT em **`localStorage`**, expondo classe de ataques XSS a token de sessão (**LGPD**/boa prática de segurança de aplicações).

## Decisão atual (Beta)

Permitido apenas **ambientes controlados Beta** até decisão Allan / primeiro cliente Enterprise.

## Decisão futura (alvo)

1. Migrar fluxo **`/auth/login`** FastAPI ou Supabase Auth com **cookies HttpOnly** + **SameSite** adequado ao domínio.
2. Frontend Next.js ler sessão apenas via middleware/proxy próprio (**BFF**) sem expor Bearer em JS navegável.
3. Eliminar uso de campos **`admin_*`** persistidos texto claro onde possível (reduz superfície de ataque combinada XSS).

Implementação será priorizada conforme backlog comercial antes de marca **Enterprise** com exigências ABNT de governança de TI.
