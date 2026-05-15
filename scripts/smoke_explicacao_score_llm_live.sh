#!/usr/bin/env bash
# Smoke manual/local — explicação score LLM (ADR-022 Fase 4).
# Pré-requisito: `make dev` + `make migrate`.
set -euo pipefail

API="${QDI_API_BASE_URL:-http://127.0.0.1:60000}"
EMAIL="${QDI_SMOKE_ADMIN_EMAIL:-ci-dashboard@qualidiagiq.test}"
PASS="${QDI_SMOKE_ADMIN_PASSWORD:-secret}"

echo "→ GET /health/llm"
curl -sS "${API}/health/llm" | python3 -m json.tool

echo "→ POST /auth/login"
TOKEN=$(curl -sS -X POST "${API}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

DID=$(curl -sS "${API}/diagnosticos/" -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
items = d if isinstance(d, list) else d.get('items', [])
fin = [x for x in items if x.get('status') == 'finalizado' and x.get('score_geral') is not None]
if not fin:
    raise SystemExit('Nenhum diagnóstico finalizado com score no painel.')
print(fin[0]['id'])
")

echo "→ POST /diagnosticos/${DID}/explicacao-score-llm"
curl -sS -X POST "${API}/diagnosticos/${DID}/explicacao-score-llm" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Idempotency-Key: smoke-live-$(date +%s)" \
  | python3 -m json.tool | head -20

echo "→ GET /diagnosticos/${DID}/explicacao-score-llm/historico"
curl -sS "${API}/diagnosticos/${DID}/explicacao-score-llm/historico" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -m json.tool | head -25

echo "✅ Smoke API concluído (diag ${DID})."
