# Bases legais do tratamento — QualiDiagIQ (rascunho técnico)

> **Atenção:** texto orientador para jurídico/DPO. Não substitui política de privacidade publicada nem RIPD assinado.

## Finalidades e bases (LGPD, art. 7º)

| Finalidade | Base legal sugerida | Notas técnicas |
|------------|---------------------|----------------|
| Execução do diagnóstico e entrega do relatório | Art. 7º, V (execução de contrato / procedimentos preliminares) | Dados mínimos no wizard; tenant RLS. |
| OTP e comunicações transaccionais | Art. 7º, V | E-mail transaccional via fornecedor configurado. |
| Segurança, prevenção a fraude, métricas agregadas | Art. 7º, IX (legítimo interesse) + Art. 10 quando aplicável | Logs com `trace_id`; Sentry com scrubbing. |
| Obrigações legais / defesa em controvérsia | Art. 7º, II | Retenção núcleo fiscal — ver ADR-012 e `docs/operacao/RETENCAO_DADOS.md`. |

## Normas sectoriais relevantes

- **EC 132/2023** e **LC 214/2025** — enquadramento da reforma do consumo (contexto do produto).
- **Lei 13.709/2018 (LGPD)** — tratamento de dados pessoais.

## Próximo passo

Validação e assinatura pelo **encarregado/DPO** e publicação alinhada ao site.
