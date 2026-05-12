# Política de logs estruturados, retenção e redaction — QualiDiagIQ

> QDI-H-015 — alinha engenharia a LGPD (Lei 13.709/2018 art. 37, art. 46) e ao plano de observabilidade.

## Formato

- **Biblioteca:** `structlog` em toda a camada de adapters e routers críticos (anti-padrão S-06: sem `print()` em API).
- **Correlação:** `X-Trace-Id` + (quando aplicável) **W3C Trace Context** repassado pelo proxy Next — ver `docs/operacao/EVENTOS_NEGOCIO_LOGS.md`.

## Redaction de PII

- **Sentry:** `before_send` em `src/presentation/api/main.py` mascara chaves sensíveis no payload de `request` (melhor esforço — não substitui DLP de rede).
- **Logs de aplicação:** evitar valores completos de e-mail, telefone, CPF, tokens e corpos de OTP; preferir hashes ou identificadores opacos (`diagnostico_id`, `tenant_id`).

## Retenção (orientação até fecho jurídico)

| Tipo | Orientação | Notas |
|------|--------------|--------|
| Logs de acesso / aplicação | Alinhar a `docs/operacao/RETENCAO_DADOS.md` e ao RIPD | Agregar em staging antes de arquivar |
| Traces OTLP | Retenção do collector (Grafana Tempo / vendor) | QDI-H-024 |
| Evidências fiscais | Imutáveis (WORM) — não misturar com logs voláteis | ADR-012 |

## Revisão

- DPO / segurança da informação devem ratificar prazos antes do go-live público.
