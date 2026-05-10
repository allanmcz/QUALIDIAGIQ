# Handoff — plano 6h / hardening S-01 (09/05/2026)

Documento para continuidade sem depender do histórico do chat.

## Entregas aplicadas no repositório

| Item | Descrição |
|------|-----------|
| HTTP **409** | `DiagnosticoNaoFinalizavelError` mapeada em `create_app()` (`main.py`) para `{"detail": str(exc)}`. Use cases `AnexarRelatorioOtimista`, `AtualizarChecklistM12Autoconf`, `AtualizarQuadroImplantacao` propagam a exceção de domínio (sem converter para `ValueError`). |
| Docker non-root | Imagem final: utilizador de sistema `qdiapp` (uid/gid 10001), `chown -R` em `/app`, `USER qdiapp`. Healthcheck usa `127.0.0.1` + timeout explícito. |
| Migração **0031** | `idx_admins_email_lower_trim` em `admins ((lower(trim(email))))` — alinhado a `buscar_admin_por_email_postgres`. |
| PDF / disclaimer | Textos PT/EN reforçam que **não** é parecer jurídico consultivo / binding legal advice. |

## Testes

- `tests/unit/application/test_*` — esperam `DiagnosticoNaoFinalizavelError` onde antes era `ValueError` para estado não finalizado.
- `tests/unit/presentation/test_api.py` — cenários **409** para PATCH relatório, checklist M12 e quadro (mock do use case).
- `tests/unit/infrastructure/test_relatorio_pdf_i18n.py` — assert mínimo no disclaimer.

## Verificação local obrigatória

```bash
make format && make lint && make test
```

Aplicar migração **0031** na base alvo (ordem lexical com as demais em `src/infrastructure/db/migrations/`).

## Commits sugeridos (Conventional Commits PT-BR)

- `feat(qdi-api): mapear DiagnosticoNaoFinalizavelError para HTTP 409`
- `fix(qdi-build): executar container da API como utilizador não-root`
- `feat(qdi-infra): índice funcional admins por e-mail normalizado`
- `docs(qdi-pdf): reforçar disclaimer jurídico no relatório i18n`

(Não foi feito `git push` por este fluxo.)
