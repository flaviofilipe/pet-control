#!/bin/bash
# =============================================================================
# Script de Backup do MongoDB - Pet Control System
# =============================================================================
# Este script realiza backup completo do banco de dados MongoDB
#
# Uso:
#   backup-mongo                    # Backup com timestamp
#   backup-mongo custom-name        # Backup com nome customizado
#
# Exemplo dentro do container:
#   docker exec pet-mongodb backup-mongo
# =============================================================================

set -e  # Exit on error

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configurações
BACKUP_DIR="${BACKUP_DIR:-/backup}"
DB_NAME="${MONGO_INITDB_DATABASE:-pet_control}"
MONGO_USER="${MONGO_INITDB_ROOT_USERNAME:-root}"
MONGO_PASS="${MONGO_INITDB_ROOT_PASSWORD:-root}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${1:-backup_${TIMESTAMP}}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔄 MongoDB Backup - Pet Control${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}📝 Configurações:${NC}"
echo -e "   Database:     ${GREEN}${DB_NAME}${NC}"
echo -e "   Backup Path:  ${GREEN}${BACKUP_PATH}${NC}"
echo -e "   Timestamp:    ${GREEN}${TIMESTAMP}${NC}"
echo ""

# Realizar backup
echo -e "${BLUE}🔄 Iniciando backup...${NC}"

if [ -n "$MONGO_USER" ] && [ -n "$MONGO_PASS" ]; then
    # Backup com autenticação
    mongodump \
        --db="$DB_NAME" \
        --out="$BACKUP_PATH" \
        --username="$MONGO_USER" \
        --password="$MONGO_PASS" \
        --authenticationDatabase=admin \
        --gzip \
        --quiet
else
    # Backup sem autenticação
    mongodump \
        --db="$DB_NAME" \
        --out="$BACKUP_PATH" \
        --gzip \
        --quiet
fi

# Verificar sucesso
if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    echo -e "${GREEN}✅ Backup concluído com sucesso!${NC}"
    echo ""
    echo -e "${YELLOW}📊 Informações:${NC}"
    echo -e "   Tamanho:      ${GREEN}${BACKUP_SIZE}${NC}"
    echo -e "   Localização:  ${GREEN}${BACKUP_PATH}${NC}"
    echo ""
    
    # Listar arquivos do backup
    echo -e "${YELLOW}📁 Conteúdo do backup:${NC}"
    ls -lh "$BACKUP_PATH/$DB_NAME/" 2>/dev/null || ls -lh "$BACKUP_PATH/"
    echo ""
    
    # Sugestão de como copiar para host
    echo -e "${YELLOW}💡 Para copiar o backup para o host:${NC}"
    echo -e "   ${BLUE}docker cp pet-mongodb:${BACKUP_PATH} ./backups/${NC}"
    echo ""
else
    echo -e "${RED}❌ Erro ao realizar backup!${NC}"
    exit 1
fi

# Limpar backups antigos (manter últimos 7 dias)
echo -e "${YELLOW}🧹 Limpando backups antigos (mantém últimos 7 dias)...${NC}"
find "$BACKUP_DIR" -type d -name "backup_*" -mtime +7 -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✅ Limpeza concluída!${NC}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 Backup finalizado!${NC}"
echo -e "${BLUE}========================================${NC}"

