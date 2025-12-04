#!/bin/bash
# =============================================================================
# Script de Inicialização do PostgreSQL - Pet Control System
# Cria usuário da aplicação e extensões necessárias
# =============================================================================

set -e

# Criar usuário da aplicação
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Criar usuário da aplicação
    CREATE USER pet_control_user WITH PASSWORD '${POSTGRES_APP_PASSWORD:-pet_control_pass}';
    
    -- Conceder permissões no banco
    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO pet_control_user;
    GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO pet_control_user;
    
    -- Conectar ao banco e criar extensões
    \c ${POSTGRES_DB}
    
    -- Extensão para full-text search em português
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    
    -- Extensão para funções de texto
    CREATE EXTENSION IF NOT EXISTS unaccent;
    
    -- Conceder permissões no schema public
    GRANT ALL ON SCHEMA public TO pet_control_user;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pet_control_user;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pet_control_user;
    
    -- Configurar permissões padrão para objetos futuros
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO pet_control_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO pet_control_user;
    
    -- Log de sucesso
    SELECT 'PostgreSQL inicializado com sucesso!' as status;
EOSQL

echo "✅ Usuário pet_control_user criado com sucesso!"
echo "✅ Extensões instaladas: pg_trgm, unaccent"

