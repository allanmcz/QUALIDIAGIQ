#!/usr/bin/env bash
# Heurística local anti–S-01 (segredos em fonte). Não substitui Gitleaks/Trufflehog em CI corporativo.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v rg >/dev/null 2>&1; then
  echo "⚠️  ripgrep (rg) não encontrado — instale para usar este script."
  exit 0
fi

PATTERN='qualidiagiq-super-secret|admin123|SECRET_KEY\s*=\s*"[^"]+"'

set +e
OUT=$(rg -n --glob '*.py' --glob '*.ts' --glob '*.tsx' --glob '*.js' --glob '*.mjs' \
  "$PATTERN" src/ frontend/ scripts/ 2>/dev/null)
RC=$?
set -e

if [[ $RC -eq 0 && -n "$OUT" ]]; then
  echo "$OUT"
  echo ""
  echo "❌ Possível segredo ou anti-padrão S-01 — revise os matches acima."
  exit 1
fi

echo "✅ Nenhum padrão heurístico crítico encontrado em src/, frontend/, scripts/."
