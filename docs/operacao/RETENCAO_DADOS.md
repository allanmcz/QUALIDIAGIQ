# Retenção de dados — QualiDiagIQ (rascunho técnico)

> Prazos definitivos no **RIPD** e política publicada. Valores abaixo espelham ADR-012.

## Diagnóstico finalizado (conteúdo técnico + hash)

- **Orientação:** 5 anos após a data de referência fiscal aplicável (fundamento: prescrição decadencial — **CTN, arts. 173 e 174**).

## Dados pessoais do titular (consentimento / marketing)

- **Orientação:** até revogação + período operacional curto (ex.: 6 meses) — ver ADR-012, tabela.

## Logs e auditoria

- **Orientação:** até 5 anos onde exigido para comprovação de medidas de segurança (LGPD, art. 37; Marco Civil).

## Rotinas técnicas

- Jobs de purga/anonimização **apenas** após fecho jurídico e feature flags em produção.
