#!/usr/bin/env bash
#
# QualiDiagIQ — modo “painel”: sobe o Docker, valida /health, imprime URLs e segue os logs.
# Ctrl+C → docker compose down (para todo o stack).
#
# Stack: `make dev` (= docker compose up -d --build --remove-orphans). Mesmo critério do iniciar-app.sh dev.
#
# Para só subir sem logs: ./INICIAR_APP/iniciar-app.sh dev
# Para logs sem derrubar ao sair: ./INICIAR_APP/iniciar-app.sh logs  (Ctrl+C só encerra o tail)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/qdi-env.sh
source "$SCRIPT_DIR/lib/qdi-env.sh"
qdi_cd_root "$SCRIPT_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cleanup() {
  echo -e "\n${RED}Encerrando containers (docker compose down)...${NC}"
  docker compose down
  echo -e "${GREEN}Ambiente encerrado.${NC}"
  exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}   QualiDiagIQ — Docker + logs (MVP)             ${NC}"
echo -e "${GREEN}=================================================${NC}"

echo -e "${BLUE}[STACK]${NC} make dev — Compose com ${YELLOW}--build${NC} se Dockerfile/pyproject mudaram (PostgreSQL + API + Next)…"
make dev

echo -e "\n${BLUE}[CHECK]${NC} GET http://127.0.0.1:60000/health …"
if qdi_health_probe 4; then
  echo -e "${GREEN}✓ API OK (health).${NC}"
else
  echo -e "${YELLOW}⚠ API ainda não respondeu — normal nos primeiros segundos; veja os logs.${NC}"
fi

echo -e "\n${GREEN}=================================================${NC}"
echo -e "${GREEN}Ambiente${NC}"
qdi_print_service_info
echo -e "${GREEN}=================================================${NC}"
echo -e "Seguindo ${BLUE}docker compose logs -f${NC}. ${YELLOW}Ctrl+C${NC} encerra os **containers**."
echo -e "Só tail sem derrubar stack: ${BLUE}./INICIAR_APP/iniciar-app.sh logs${NC}"
echo ""

docker compose logs -f
