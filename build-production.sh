#!/bin/bash
# =============================================================================
# Script de Build de Produção - Pet Control API
# =============================================================================
# Este script facilita o build e push da imagem de produção para o ECR
#
# Uso:
#   ./build-production.sh
#
# Pré-requisitos:
#   - Docker instalado
#   - AWS CLI configurado
#   - Autenticação no ECR feita
# =============================================================================

set -e  # Exit on error

# Configurações
APP_NAME="pet-control"
VERSION="${1:-latest}"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Pet Control - Build de Produção${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar se AWS_ACCOUNT_ID está definido
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${YELLOW}⚠️  AWS_ACCOUNT_ID não definido. Tentando detectar...${NC}"
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
    
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        echo -e "${RED}❌ Erro: Não foi possível detectar AWS_ACCOUNT_ID${NC}"
        echo -e "${YELLOW}💡 Defina a variável: export AWS_ACCOUNT_ID=seu-id-da-conta${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ AWS Account ID detectado: ${AWS_ACCOUNT_ID}${NC}"
fi

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_REPOSITORY="${ECR_REGISTRY}/${APP_NAME}"

echo -e "${BLUE}📋 Configurações:${NC}"
echo -e "   App Name:     ${GREEN}${APP_NAME}${NC}"
echo -e "   Version:      ${GREEN}${VERSION}${NC}"
echo -e "   AWS Region:   ${GREEN}${AWS_REGION}${NC}"
echo -e "   AWS Account:  ${GREEN}${AWS_ACCOUNT_ID}${NC}"
echo -e "   ECR Registry: ${GREEN}${ECR_REGISTRY}${NC}"
echo ""

# Passo 1: Build da imagem
echo -e "${BLUE}🔨 [1/4] Building imagem de produção...${NC}"
docker build \
  --build-arg ENV=production \
  --no-cache \
  -t ${APP_NAME}:${VERSION} \
  -t ${APP_NAME}:latest \
  .

echo -e "${GREEN}✅ Build concluído!${NC}"
echo ""

# Passo 2: Autenticar no ECR
echo -e "${BLUE}🔐 [2/4] Autenticando no AWS ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

echo -e "${GREEN}✅ Autenticação concluída!${NC}"
echo ""

# Passo 3: Taguear para o ECR
echo -e "${BLUE}🏷️  [3/4] Tagueando imagem para ECR...${NC}"
docker tag ${APP_NAME}:${VERSION} ${ECR_REPOSITORY}:${VERSION}
docker tag ${APP_NAME}:latest ${ECR_REPOSITORY}:latest

echo -e "${GREEN}✅ Tags criadas!${NC}"
echo ""

# Passo 4: Push para o ECR
echo -e "${BLUE}📤 [4/4] Fazendo push para ECR...${NC}"
docker push ${ECR_REPOSITORY}:${VERSION}
docker push ${ECR_REPOSITORY}:latest

echo -e "${GREEN}✅ Push concluído!${NC}"
echo ""

# Resumo
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 Build de produção concluído com sucesso!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}📝 Próximos passos no EC2:${NC}"
echo ""
echo -e "1️⃣  Autenticar no ECR:"
echo -e "   ${BLUE}aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}${NC}"
echo ""
echo -e "2️⃣  Fazer pull da imagem:"
echo -e "   ${BLUE}docker pull ${ECR_REPOSITORY}:${VERSION}${NC}"
echo ""
echo -e "3️⃣  Parar container antigo:"
echo -e "   ${BLUE}docker stop pet-control && docker rm pet-control${NC}"
echo ""
echo -e "4️⃣  Iniciar nova versão:"
echo -e "   ${BLUE}docker run -d --name pet-control --restart unless-stopped -p 8000:8000 --env-file ~/.env-pet-control ${ECR_REPOSITORY}:${VERSION}${NC}"
echo ""
echo -e "5️⃣  Verificar logs:"
echo -e "   ${BLUE}docker logs -f pet-control${NC}"
echo ""
echo -e "${GREEN}✨ Mensagem esperada: 🚀 Starting in PRODUCTION mode with Gunicorn + 4 Uvicorn workers...${NC}"
echo ""

