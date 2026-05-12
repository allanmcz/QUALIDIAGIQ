# Relatório de Avaliação de Tratamento (RAT) — QualiDiagIQ

Documento operacional de suporte ao Art. 37 da Lei nº 13.709/2018 (LGPD), em alinhamento ao inventário de tratamentos e ao **STATUS_JURIDICO_MVP.md** do mesmo diretório.

## Identificação do tratamento

| Campo | Valor |
|-------|--------|
| Produto | QualiDiagIQ (QDI), módulo Tributiq |
| Versão documental | MVP / sprint corrente |
| Responsável pelo tratamento | conforme contrato / política de privacidade publicada no site |

## Finalidades

- Prestação do diagnóstico tributário automatizado (wizard e relatório).
- Comunicações transacionais (OTP por e-mail, confirmação de posse da caixa de entrada).
- Operação da conta na plataforma (autenticação de consultores autorizados).

## Base legal (sumário)

- Execução de contrato e procedimentos preliminares (Art. 7º, V).
- Legítimo interesse, quando aplicável a métricas agregadas de produto (Art. 7º, IX), com teste de balanceamento documentado na camada jurídica.

## Medidas técnicas relevantes (snapshot engenharia)

- Multi-tenant com isolamento por `tenant_id` no PostgreSQL (RLS).
- Evidências e artefactos de diagnóstico com trilhas de auditoria conforme migrações `qdi.*`.
- Tokens de sessão e fluxos self-service descritos na API (`/auth/*`, `/diagnosticos/*`).

## Retenção e eliminação

Prazos e critérios de eliminação devem espelhar a política de retenção aprovada pelo encarregado/DPO e o registro de operações de tratamento (ROT); atualizar esta secção quando o ROT oficial for publicado.

## Revisão

| Data | Autor | Notas |
|------|-------|-------|
| 2026-05-09 | Engenharia QDI | Versão inicial para encadeamento S-02/S-03 (documentação LGPD). |
| 2026-05-11 | Engenharia QDI | Registo de **subprocessadores** de infraestrutura (Supabase, Sentry, e-mail transaccional, LLM em produção conforme ADR-003) deve constar do **Anexo de subprocessadores** aprovado pelo DPO; este RAT referencia `docs/legal/BASES_LEGAIS_TRATAMENTO.md` e `docs/operacao/RETENCAO_DADOS.md` como rastreio técnico. |
