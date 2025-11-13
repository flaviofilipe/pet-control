#!/bin/bash
# =============================================================================
# Script de Restore do MongoDB - Pet Control System
# =============================================================================
# Este script restaura um backup do banco de dados MongoDB
#
# Uso:
#   restore-mongo /backup/backup_20251110_120000
#
# Exemplo dentro do container:
#   docker exec pet-mongodb restore-mongo /backup/backup_20251110_120000
# =============================================================================

set -e  # Exit on error

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configurações
BACKUP_PATH="$1"
DB_NAME="${MONGO_INITDB_DATABASE:-pet_control}"
MONGO_USER="${MONGO_INITDB_ROOT_USERNAME:-root}"
MONGO_PASS="${MONGO_INITDB_ROOT_PASSWORD:-root}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔄 MongoDB Restore - Pet Control${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Validar parâmetros
if [ -z "$BACKUP_PATH" ]; then
    echo -e "${RED}❌ Erro: Path do backup não fornecido!${NC}"
    echo ""
    echo -e "${YELLOW}Uso:${NC}"
    echo -e "  restore-mongo /backup/backup_20251110_120000"
    echo ""
    echo -e "${YELLOW}Backups disponíveis:${NC}"
    ls -lh /backup/ 2>/dev/null || echo "  Nenhum backup encontrado"
    exit 1
fi

# Verificar se o backup existe
if [ ! -d "$BACKUP_PATH" ]; then
    echo -e "${RED}❌ Erro: Backup não encontrado em ${BACKUP_PATH}${NC}"
    echo ""
    echo -e "${YELLOW}Backups disponíveis:${NC}"
    ls -lh /backup/ 2>/dev/null || echo "  Nenhum backup encontrado"
    exit 1
fi

echo -e "${YELLOW}📝 Configurações:${NC}"
echo -e "   Database:     ${GREEN}${DB_NAME}${NC}"
echo -e "   Backup Path:  ${GREEN}${BACKUP_PATH}${NC}"
echo ""

# Confirmação
echo -e "${YELLOW}⚠️  ATENÇÃO: Esta operação irá SUBSTITUIR os dados atuais!${NC}"
echo -e "${YELLOW}Pressione CTRL+C para cancelar ou aguarde 5 segundos...${NC}"
sleep 5
echo ""

# Realizar restore
echo -e "${BLUE}🔄 Iniciando restore...${NC}"

if [ -n "$MONGO_USER" ] && [ -n "$MONGO_PASS" ]; then
    # Restore com autenticação
    mongorestore \
        --db="$DB_NAME" \
        --dir="$BACKUP_PATH/$DB_NAME" \
        --username="$MONGO_USER" \
        --password="$MONGO_PASS" \
        --authenticationDatabase=admin \
        --gzip \
        --drop \
        --quiet
else
    # Restore sem autenticação
    mongorestore \
        --db="$DB_NAME" \
        --dir="$BACKUP_PATH/$DB_NAME" \
        --gzip \
        --drop \
        --quiet
fi

# Verificar sucesso
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Restore concluído com sucesso!${NC}"
    echo ""
    
    # Mostrar estatísticas
    echo -e "${YELLOW}📊 Verificando dados restaurados:${NC}"
    mongosh "$DB_NAME" --quiet --eval "
        print('Coleções:');
        db.getCollectionNames().forEach(function(col) {
            var count = db[col].countDocuments();
            print('  - ' + col + ': ' + count + ' documentos');
        });
    "
    echo ""
else
    echo -e "${RED}❌ Erro ao realizar restore!${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 Restore finalizado!${NC}"
echo -e "${BLUE}========================================${NC}"

