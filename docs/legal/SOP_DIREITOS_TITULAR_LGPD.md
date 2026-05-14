# SOP — Atendimento a direitos do titular (Lei 13.709/2018 art. 18)

> **RASCUNHO** — rever com **DPO / jurídico** antes de uso operacional com titulares reais.

## Direitos cobertos (art. 18)

Confirmação, acesso, correção, anonimização/bloqueio/eliminação, portabilidade, eliminação de dados tratados com consentimento, informação sobre compartilhamentos e sobre consequências da negativa, revogação de consentimento (incisos I a IX).

## Canal oficial

- **Encarregado (DPO) — designação provisória (MVP):** **Allan Marcio**, pessoa física, e-mail **allan@tributolab.com.br** (PO, 2026-05-13). Espelhado em `LGPD_DPO_EMAIL` (API) e `NEXT_PUBLIC_LGPD_DPO_EMAIL` / `NEXT_PUBLIC_LGPD_DPO_NOME` (Next — ver `frontend/.env.example`). Substituir por designação formal definitiva ou DPO externo quando o controlador decidir.
- Prazo legal de resposta: **15 dias** (art. 19 §1 da Lei 13.709/2018), prorrogável por mais 15 mediante justificativa ao titular.

## Fluxo operacional (resumo)

1. Recebimento e registo no ficheiro `docs/legal/REGISTRO_DIREITOS_TITULAR.csv` (cabecalhos: data, tipo_pedido, identificador_interno, estado, responsavel).
2. Autenticação forte do titular (canal acordado com DPO — não substitui validação jurídica).
3. Categorização do pedido (I–IX) e execução técnica com **mínimo necessário** e trilho de auditoria.
4. Resposta documentada ao titular.
5. Revisão DPO em pedidos de eliminação quando houver obrigação legal de retenção (ex.: trilhos fiscais).

## Exceções a documentar

- Dados anonimizados (art. 12) e base legal de retenção (ex.: obrigações do CTN / SPED — contexto fiscal do produto).

## Referências

- Lei 13.709/2018 — texto integral: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- `_DEVELOPER/DECISAO_EXTERNA/RETENCAO_LOGS_REDACTION.md`
- `_DEVELOPER/DECISAO_EXTERNA/README_PENDENCIAS_GO_LIVE.md`
