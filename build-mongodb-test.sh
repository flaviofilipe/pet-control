#!/bin/bash
# =============================================================================
# Script para Build da Imagem MongoDB para Testes
# =============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

APP_NAME="pet-control-mongodb"
VERSION="test"
USERNAME="root"
PASSWORD="root"
DATABASE="pet_control"

# remove container if exists
docker stop pet-mongodb-test
docker rm pet-mongodb-test

# remove volume if exists
docker volume rm pet-mongodb-test-data

# remove image if exists
docker rmi ${APP_NAME}:${VERSION}

# Passo 1: Build da imagem
echo -e "${BLUE}🔨 [1/3] Building imagem MongoDB...${NC}"
echo -e "${YELLOW}   Dockerfile: Dockerfile.mongodb${NC}"
echo -e "${YELLOW}   Incluindo:${NC}"
echo -e "     - Scripts de inicialização (01-init-db.js, 02-create-indexes.js, 03-seed-data.js, 04-seed-info-data.js)"
echo -e "     - Configurações otimizadas (mongod.conf)"
echo -e "     - Scripts utilitários (backup, restore, health-check)"
echo ""

docker build \
  -f Dockerfile.mongodb \
  --no-cache \
  -t ${APP_NAME}:${VERSION} \
  -t ${APP_NAME}:latest \
  .

echo -e "${GREEN}✅ Build concluído!${NC}"
echo ""

# Passo 2: Executar container
echo -e "${BLUE}🚀 [2/3] Executando container MongoDB...${NC}"
docker run -d \
  --name pet-mongodb-test \
  --network pet-network \
  -p 27017:27017 \
  -v pet-mongodb-test-data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=${USERNAME} \
  -e MONGO_INITDB_ROOT_PASSWORD=${PASSWORD} \
  -e MONGO_INITDB_DATABASE=${DATABASE} \
  -e MONGO_APP_PASSWORD=${PASSWORD} \
  ${APP_NAME}:${VERSION}

echo -e "${GREEN}✅ Container executado!${NC}"
echo ""

# Passo 3: Verificar logs
echo -e "${BLUE}📋 [3/3] Verificando logs...${NC}"
docker logs pet-mongodb-test --tail 10

echo -e "${GREEN}✅ Logs verificados!${NC}"