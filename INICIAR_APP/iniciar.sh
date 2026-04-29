#!/bin/bash

# Cores para o output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}   Iniciando o Ambiente QualiDiagIQ (MVP)        ${NC}"
echo -e "${GREEN}=================================================${NC}"

# Função para encerrar os processos em background quando o script for parado (Ctrl+C)
cleanup() {
    echo -e "\n${RED}Encerrando os serviços...${NC}"
    kill $BACKEND_PID
    kill $FRONTEND_PID
    echo -e "${GREEN}Serviços encerrados com sucesso!${NC}"
    exit 0
}

# Captura o sinal SIGINT (Ctrl+C) e chama a função cleanup
trap cleanup SIGINT

# 1. Iniciar o Backend (FastAPI)
echo -e "${BLUE}[BACKEND]${NC} Iniciando a API (FastAPI) na porta 8000..."
cd ..
make dev &
BACKEND_PID=$!
# Volta para INICIAR_APP
cd INICIAR_APP

# Aguarda 3 segundos para o backend respirar
sleep 3

# 2. Iniciar o Frontend (Next.js)
echo -e "${YELLOW}[FRONTEND]${NC} Iniciando a Interface Web (Next.js) na porta 3000..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!
cd ../INICIAR_APP

echo -e "\n${GREEN}=================================================${NC}"
echo -e "${GREEN} Tudo pronto! A aplicação está rodando.${NC}"
echo -e " Frontend (Wizard): ${BLUE}http://localhost:3000${NC}"
echo -e " Backend (Swagger): ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "Pressione [Ctrl+C] a qualquer momento para parar ambos os serviços."

# Espera os processos terminarem (o que previne o script de fechar sozinho)
wait $BACKEND_PID
wait $FRONTEND_PID
