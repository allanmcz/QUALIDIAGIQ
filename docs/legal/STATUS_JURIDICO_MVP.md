# Status jurídico — páginas MVP (termos / privacidade)

**Objetivo:** registrar o que o repositório cobre e o estado do parecer sobre `/termos` e `/privacidade`.

## Situação no código (2026-05-01)

| Artefacto | Estado |
|-----------|--------|
| `frontend/app/termos/page.tsx` | Minuta pública; **aprovada** (parecer externo + aprovação produto — ver abaixo). |
| `frontend/app/privacidade/page.tsx` | Política MVP LGPD; **aprovada** no mesmo pacote. |
| Aceite técnico persistido | Campo `aceite_termos_privacidade_em` no POST `/diagnosticos/` (migração **0012**) |

## Aprovação produto (controlador)

| Campo | Valor |
|-------|-------|
| **Decisão** | **Aprovada** a publicação da minuta veiculada em **`/termos`** e **`/privacidade`**, com implementação dos apontamentos do parecer jurídico e manutenção do texto **coerente com a operação** (stack, operadores, retenções). |
| **Data** | 2026-05-07 |
| **Registo** | Allan — produto QualiDiagIQ / Tributiq (controlador). |

## Parecer formal (advogado)

| Campo | Valor |
|-------|-------|
| **Arquivo no repositório** | `docs/legal/PARECER JURÍDICO - QualiDiagIQ_7242.pdf` |
| **Registro** | Parecer jurídico arquivado em `docs/legal/` (2026-05-07). |
| **Conclusão (advogado)** | **Aprovação da minuta** de Termos de Uso e Política de Privacidade, **desde que** sejam considerados os ajustes indicados no parecer e que o texto publicado permaneça **compatível com a operação real** (arquitetura, operadores, fluxo de dados). Cfr. itens 21–23 do PDF (Maceió/AL, 5 de maio de 2026). |

Substituir ou acrescentar PDF se houver nova versão assinada; manter este `STATUS_*` alinhado ao ficheiro vigente.

## Pendências operacionais (não substituem o parecer)

1. **Canal de titular** (e-mail/DPO) nas páginas — preencher com contacto oficial **em produção** quando o domínio e o DPO estiverem fixos.
2. **Versão publicada** — registrar número/data da política após cada revisão (controle de mudanças / changelog interno).

## Critério de aceite para “jurídico OK” no checklist MVP

- [x] Parecer formal arquivado referenciando as páginas de termos e privacidade — ver PDF na pasta `docs/legal/`.
- [x] Registro em `docs/CHANGELOG_MVP.md` (**[Unreleased]** 2026-05-07 — entrada jurídico). Copiar para linha datada do release quando existir tag semver de produto.

**Base legal de referência:** LGPD (Lei 13.709/2018); Marco Civil (Lei 12.965/2014) quando aplicável ao site/saas.
