# Backup e recuperação — QualiDiagIQ (rascunho operacional)

## PostgreSQL (Supabase)

- **Responsável:** operação da conta Supabase / DBA designado.
- **Frequência:** conforme plano do fornecedor (PITR disponível nas tiers pagas).
- **Teste de restauro:** semestral em ambiente não produtivo; registar evidência no ticket interno.

## Object storage / artefactos

- PDFs e ficheiros gerados: política de retenção alinhada a `docs/operacao/RETENCAO_DADOS.md`.

## RTO / RPO (placeholder)

| Métrica | Alvo inicial (MVP) | Notas |
|---------|-------------------|--------|
| RPO | ≤ 24 h | Depende do backup contínuo Supabase. |
| RTO | ≤ 4 h | Ajustar após dimensionamento real. |
