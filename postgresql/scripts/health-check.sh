#!/bin/bash
# =============================================================================
# Health Check Script para PostgreSQL
# =============================================================================

set -eo pipefail

# Verificar se o PostgreSQL está aceitando conexões
pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q

# Verificar se pode executar queries
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" > /dev/null

echo "PostgreSQL está saudável"
exit 0

