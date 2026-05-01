#!/usr/bin/env bash
# cleanup_final.sh — limpeza pós-sandbox para o projeto CALCULAR_TRIB_REFORMA
#
# O sandbox Cowork não consegue:
#  - remover arquivos .DS_Store do Google Drive (TCC restrictions)
#  - remover arquivos com permissão "view-only" no GD
#
# Uso:
#   cd ~/GD_TRIBUTOLAB/014-SAAS_REFORMA/CALCULAR_TRIB_REFORMA
#   bash cleanup_final.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "🧹 Limpando $ROOT ..."

# 1) Remover .DS_Store recursivamente
find "$ROOT" -name ".DS_Store" -type f -delete -print | sed 's/^/  removido: /'

# 2) Remover artefato inválido (HTML disfarçado de JSON)
if [[ -f "$ROOT/raw/openapi-v3.json" ]]; then
  if head -c 20 "$ROOT/raw/openapi-v3.json" | grep -q "<!doctype html>"; then
    rm "$ROOT/raw/openapi-v3.json"
    echo "  removido: raw/openapi-v3.json (HTML, não JSON válido)"
  fi
fi

# 3) Smoke test: validar JSONs
echo ""
echo "✓ Validando JSONs..."
for f in "$ROOT"/examples/*.json "$ROOT"/raw/*.json; do
  python3 -c "import json; json.load(open('$f'))" && echo "  OK  $f" || echo "  FAIL  $f"
done

echo ""
echo "✅ Limpeza concluída."
