# Status jurídico — páginas MVP (termos / privacidade)

**Objetivo:** registrar o que o repositório cobre e o estado do parecer sobre `/termos` e `/privacidade`.

## Situação no código (2026-05-01)

| Artefacto | Estado |
|-----------|--------|
| `frontend/app/termos/page.tsx` | Minuta pública; **aprovada** (parecer externo + aprovação produto — ver abaixo). |
| `frontend/app/privacidade/page.tsx` | Política MVP LGPD; **aprovada**; secção **`#dpo`** com e-mail via `NEXT_PUBLIC_LGPD_DPO_*`. |
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

## Canal DPO (implementação técnica)

| Campo | Valor |
|-------|-------|
| **URL pública** | `https://<site>/privacidade#dpo` (âncora `id="dpo"`). |
| **Configuração** | `NEXT_PUBLIC_LGPD_DPO_EMAIL` (obrigatório para exibir o mailto); opcional `NEXT_PUBLIC_LGPD_DPO_NOME`, `NEXT_PUBLIC_POLITICA_PRIVACIDADE_VERSAO`, `NEXT_PUBLIC_POLITICA_PRIVACIDADE_VIGENCIA`. |
| **Exemplo institucional** | **MVP (2026-05-13):** encarregado provisório **Allan Marcio** (pessoa física), e-mail **allan@tributolab.com.br**, em `frontend/.env.example`, `frontend/.env.production.example`, `docker-compose.yml` (serviço `web`) e default de `LGPD_DPO_EMAIL` em `Settings`. Substituir se o controlador nomear outro DPO ou domínio institucional definitivo. |
| **API (paridade)** | `GET /public/institucional` — `lgpd_dpo_email`, `lgpd_retencao_referencia_dias`, caminho `/privacidade/solicitacoes` |

## Designação do encarregado (registo PO — 2026-05-13)

- **Nome:** Allan Marcio (pessoa física).  
- **Função:** Encarregado de Proteção de Dados (DPO) **provisório**, até designação formal em acto societário / contrato de prestação de serviços ou nomeação de DPO externo.  
- **Canal:** **allan@tributolab.com.br** (deve coincidir com `NEXT_PUBLIC_LGPD_DPO_EMAIL` e `LGPD_DPO_EMAIL` em produção).

## Pendências operacionais (não substituem o parecer)

1. **Produção:** confirmar que o e-mail exibido é o **canal oficial** do encarregado nomeado (Res. ANPD nº 18/2024) e alterar variáveis de deploy se divergirem deste registo provisório.
2. **Versão publicada** — opcional: `NEXT_PUBLIC_POLITICA_PRIVACIDADE_VERSAO` e `_VIGENCIA`; ou registo só no changelog interno.

### Retenção do telefone (baseline controlador — 2026-05)

O fluxo de pedidos tramita pelo DPO (`/privacidade#dpo`) e pela API autenticada `POST /privacidade/solicitacoes` (vide `tests/integration/test_privacidade_api.py`). A secção **`#retencao-telefone`** na página `/privacidade` descreve o enquadramento para equipas operacionais; prazos de SLA de resposta ao titular seguem política interna do controlador.

## Critério de aceite para “jurídico OK” no checklist MVP

- [x] Parecer formal arquivado referenciando as páginas de termos e privacidade — ver PDF na pasta `docs/legal/`.
- [x] Registro em `docs/CHANGELOG_MVP.md` (**[Unreleased]** 2026-05-07 — entrada jurídico). Copiar para linha datada do release quando existir tag semver de produto.

**Base legal de referência:** LGPD (Lei 13.709/2018); Marco Civil (Lei 12.965/2014) quando aplicável ao site/saas.
