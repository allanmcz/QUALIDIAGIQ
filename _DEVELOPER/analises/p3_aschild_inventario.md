# Inventário `asChild` — componente Button (P3)

> Gerado para handoff §11 T4 — uso de `Button` com filho único (ex.: Next.js `Link`).

Arquivos com `asChild` (grep `frontend/app` + `frontend/components`, `*.tsx`):

| Arquivo | Uso |
|---------|-----|
| `frontend/app/page.tsx` | CTA principal → `Link` |
| `frontend/app/dashboard/page.tsx` | Link “login” dentro do aviso sem sessão |
| `frontend/app/dashboard/diagnosticos/[id]/DiagnosticoDetalheClient.tsx` | Botão secundário com `Link` |
| `frontend/app/sucesso/page.tsx` | CTA pós-wizard |

**Implementação:** `frontend/components/ui/button.tsx` — modo `asChild` com `cloneElement` e tipo `SlotProps` (`data-slot` + `className`).

**Console:** validar manualmente em dev nas rotas `/`, `/dashboard`, `/sucesso` (avisos de terceiros podem persistir).
