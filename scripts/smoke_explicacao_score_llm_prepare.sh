#!/usr/bin/env bash
# Pré-requisitos do smoke live — Ollama + API com router + admin CI avançado.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API="${QDI_API_BASE_URL:-http://127.0.0.1:60000}"
MODEL="${OLLAMA_MODEL:-llama3}"

echo "→ Garantir serviço Ollama no compose (pull ~3GB na 1.ª vez — pode demorar)"
docker compose pull ollama
docker compose up -d ollama

echo "→ Aguardar Ollama responder (até 120s)"
for i in $(seq 1 24); do
  if docker compose exec -T ollama ollama list >/dev/null 2>&1; then
    break
  fi
  sleep 5
done

echo "→ Modelo ${MODEL} (ignore se já existir)"
docker compose exec -T ollama ollama pull "${MODEL}" || true

echo "→ Recriar API com LLM_ROUTER_ENABLED e OLLAMA_BASE_URL=http://ollama:11434"
# --no-deps: não bloquear no pull do Ollama (~3GB); o serviço ollama sobe em paralelo acima.
docker compose up -d --no-deps --force-recreate api

echo "→ Migração 0046 (perfil avançado CI smoke) + aguardar /health"
sleep 3
docker compose exec -T db psql -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -f /docker-entrypoint-initdb.d/migrations/0046_ci_dashboard_perfil_avancado_smoke.sql \
  2>/dev/null || docker compose exec -T db psql -U postgres -d postgres -c \
  "UPDATE admins SET perfil_conta = 'avancado' WHERE lower(trim(email)) = 'ci-dashboard@qualidiagiq.test';"

for i in $(seq 1 30); do
  if curl -sf "${API}/health" >/dev/null; then
    break
  fi
  sleep 2
done

echo "→ GET /health/llm"
curl -sS "${API}/health/llm" | python3 -m json.tool
LLM_STATUS=$(curl -sS "${API}/health/llm" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))")
if [ "$LLM_STATUS" = "disabled" ]; then
  echo "⚠️  Router LLM desligado na API — confira LLM_ROUTER_ENABLED no container (make dev / compose)." >&2
  exit 1
fi

echo "✅ Prepare concluído. Rode: bash scripts/smoke_explicacao_score_llm_live.sh"
