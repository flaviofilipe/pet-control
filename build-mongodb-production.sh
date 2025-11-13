#!/bin/bash
# =============================================================================
# Script de Build de Produção - Pet Control MongoDB
# =============================================================================
# Este script facilita o build e push da imagem MongoDB customizada para o ECR
#
# Uso:
#   ./build-mongodb-production.sh
#   ./build-mongodb-production.sh v1.0.0
#
# Pré-requisitos:
#   - Docker instalado
#   - AWS CLI configurado
#   - Permissões ECR configuradas
# =============================================================================

set -e  # Exit on error

# Configurações
APP_NAME="pet-control-mongodb"
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
echo -e "${BLUE}🗄️  Pet Control MongoDB - Build de Produção${NC}"
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

# Verificar se repositório ECR existe, se não, criar
echo -e "${BLUE}🔍 [0/5] Verificando repositório ECR...${NC}"
if aws ecr describe-repositories --repository-names ${APP_NAME} --region ${AWS_REGION} > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Repositório ${APP_NAME} já existe${NC}"
else
    echo -e "${YELLOW}⚠️  Repositório ${APP_NAME} não existe. Criando...${NC}"
    aws ecr create-repository \
        --repository-name ${APP_NAME} \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true \
        --tags Key=Application,Value=pet-control Key=Component,Value=database Key=Environment,Value=production \
        > /dev/null
    echo -e "${GREEN}✅ Repositório criado com sucesso!${NC}"
fi
echo ""


# Passo 1: Build da imagem
echo -e "${BLUE}🔨 [1/5] Building imagem MongoDB...${NC}"
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

# Passo 2: Autenticar no ECR
echo -e "${BLUE}🔐 [2/5] Autenticando no AWS ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

echo -e "${GREEN}✅ Autenticação concluída!${NC}"
echo ""

# Passo 3: Taguear para o ECR
echo -e "${BLUE}🏷️  [3/5] Tagueando imagem para ECR...${NC}"
docker tag ${APP_NAME}:${VERSION} ${ECR_REPOSITORY}:${VERSION}
docker tag ${APP_NAME}:latest ${ECR_REPOSITORY}:latest

echo -e "${GREEN}✅ Tags criadas:${NC}"
echo -e "   - ${ECR_REPOSITORY}:${VERSION}"
echo -e "   - ${ECR_REPOSITORY}:latest"
echo ""

# Passo 4: Push para o ECR
echo -e "${BLUE}📤 [4/5] Fazendo push para ECR...${NC}"
echo -e "${YELLOW}   Aguarde, isso pode levar alguns minutos...${NC}"
echo ""

docker push ${ECR_REPOSITORY}:${VERSION}
docker push ${ECR_REPOSITORY}:latest

echo -e "${GREEN}✅ Push concluído!${NC}"
echo ""

# Passo 5: Verificar imagens no ECR
echo -e "${BLUE}🔍 [5/5] Verificando imagens no ECR...${NC}"
aws ecr list-images --repository-name ${APP_NAME} --region ${AWS_REGION} --output table

echo ""
echo -e "${GREEN}✅ Verificação concluída!${NC}"
echo ""

# Resumo
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 Build de MongoDB concluído com sucesso!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}📝 Informações da Imagem:${NC}"
echo ""
echo -e "${BLUE}📦 Imagem Local:${NC}"
echo -e "   docker images | grep ${APP_NAME}"
echo ""
echo -e "${BLUE}📦 Imagem no ECR:${NC}"
echo -e "   ${GREEN}${ECR_REPOSITORY}:${VERSION}${NC}"
echo -e "   ${GREEN}${ECR_REPOSITORY}:latest${NC}"
echo ""
echo -e "${YELLOW}📝 Próximos passos no EC2:${NC}"
echo ""
echo -e "1️⃣  ${BLUE}Autenticar no ECR:${NC}"
echo -e "   aws ecr get-login-password --region ${AWS_REGION} | \\"
echo -e "     docker login --username AWS --password-stdin ${ECR_REGISTRY}"
echo ""
echo -e "2️⃣  ${BLUE}Fazer pull da imagem:${NC}"
echo -e "   docker pull ${ECR_REPOSITORY}:${VERSION}"
echo ""
echo -e "3️⃣  ${BLUE}Parar container MongoDB antigo (se existir):${NC}"
echo -e "   docker stop pet-mongodb && docker rm pet-mongodb"
echo ""
echo -e "4️⃣  ${BLUE}Criar arquivo .env-mongodb:${NC}"
echo -e "   cat > ~/.env-mongodb << 'EOF'"
echo -e "   MONGO_INITDB_ROOT_USERNAME=admin"
echo -e "   MONGO_INITDB_ROOT_PASSWORD=sua_senha_super_segura"
echo -e "   MONGO_INITDB_DATABASE=pet_control"
echo -e "   MONGO_APP_PASSWORD=senha_app_super_segura"
echo -e "   EOF"
echo -e "   chmod 600 ~/.env-mongodb"
echo ""
echo -e "5️⃣  ${BLUE}Iniciar nova versão:${NC}"
echo -e "   docker run -d \\"
echo -e "     --name pet-mongodb \\"
echo -e "     --restart unless-stopped \\"
echo -e "     -p 127.0.0.1:27017:27017 \\"
echo -e "     --env-file ~/.env-mongodb \\"
echo -e "     -v pet-mongodb-data:/data/db \\"
echo -e "     -v pet-mongodb-backup:/backup \\"
echo -e "     ${ECR_REPOSITORY}:${VERSION} \\"
echo -e "     mongod --auth"
echo ""
echo -e "6️⃣  ${BLUE}Verificar logs:${NC}"
echo -e "   docker logs -f pet-mongodb"
echo ""
echo -e "7️⃣  ${BLUE}Verificar health:${NC}"
echo -e "   docker exec pet-mongodb health-check"
echo ""
echo -e "8️⃣  ${BLUE}Testar conexão:${NC}"
echo -e "   docker exec -it pet-mongodb mongosh pet_control \\"
echo -e "     -u pet_control_user -p sua_senha"
echo ""
echo -e "${GREEN}✨ Mensagens esperadas:${NC}"
echo -e "   - 🚀 [1/3] Iniciando configuração do banco de dados Pet Control..."
echo -e "   - ✅ Usuário root criado com sucesso!"
echo -e "   - ✅ Usuário da aplicação criado: pet_control_user"
echo -e "   - ✅ Coleção profiles criada"
echo -e "   - ✅ Coleção pets criada"
echo -e "   - ✅ Coleção vacinas criada"
echo -e "   - ✅ Coleção ectoparasitas criada"
echo -e "   - ✅ Coleção vermifugos criada"
echo -e "   - ✅ [2/3] Todos os índices foram criados com sucesso!"
echo -e "   - ✅ [3/3] Dados de exemplo inseridos com sucesso!"
echo -e "   - 🚀 [4/4] Inserindo dados informativos (vacinas, ectoparasitas, vermífugos)..."
echo -e "   - 🎉 Configuração do MongoDB concluída!"
echo ""
echo -e "${YELLOW}📊 Recursos da Imagem:${NC}"
echo -e "   - ${GREEN}5 coleções${NC} com validações JSON Schema"
echo -e "   - ${GREEN}21 índices${NC} otimizados"
echo -e "   - ${GREEN}Dados de exemplo${NC} (3 profiles, 3 pets)"
echo -e "   - ${GREEN}Scripts utilitários${NC} (backup, restore, health-check)"
echo -e "   - ${GREEN}Configurações otimizadas${NC} (cache 1GB, compression, profiling)"
echo ""
echo -e "${YELLOW}🔒 String de Conexão (Aplicação):${NC}"
echo -e "   mongodb://pet_control_user:senha@mongodb:27017/pet_control?authSource=pet_control"
echo ""
echo -e "${YELLOW}💾 Backup Automático (Cron - Opcional):${NC}"
echo -e "   # Backup diário às 2h da manhã"
echo -e "   0 2 * * * docker exec pet-mongodb backup-mongo backup_\$(date +\\%Y\\%m\\%d)"
echo ""

