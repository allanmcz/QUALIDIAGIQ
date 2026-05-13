# OWASP ZAP — baseline em staging (QDI-H-029)

> Complementa Playwright no CI. Execução **manual ou job dedicado** contra URL de staging (não rodar contra produção sem autorização).

## Pré-requisitos

- Staging com API + Next publicados e TLS válido (ou rede interna confiável).
- Variável `ZAP_TARGET` = URL base (ex.: `https://api-staging.exemplo.com`).

## Execução no GitHub Actions

Workflow **manual**: `.github/workflows/zap-baseline-dispatch.yml` — *Actions* → *ZAP baseline (manual)* → indicar `target_url` (URL pública de staging).

## Execução local (Docker)

```bash
docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t "$ZAP_TARGET" -r zap-report.html
```

- Falhar o pipeline se política interna exigir **0 HIGH** após triagem (ajustar `-c` rules quando houver ficheiro de config versionado).

## Evidências

- Arquivar `zap-report.html` no sistema de tickets / drive do projeto.
- Abrir issues P1/P2/P3 com etiqueta `onda-1.1` quando não bloquear go-live.

## Cruzamento

- `docs/operacao/CHECKLIST_PENTEST_MVP.md`
- QDI-H-028 (pentest contratado) — ZAP **não** substitui pentest profissional.
