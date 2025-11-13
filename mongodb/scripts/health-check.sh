#!/bin/bash
# =============================================================================
# Health Check Script - MongoDB Pet Control
# =============================================================================
# Este script verifica se o MongoDB está saudável e respondendo
# Usado pelo Docker HEALTHCHECK
# =============================================================================

# Configurações
MAX_RETRIES=3
RETRY_DELAY=2

# Tentar conectar ao MongoDB
for i in $(seq 1 $MAX_RETRIES); do
    # Verificar se o MongoDB está respondendo
    if mongosh --quiet --eval "db.adminCommand('ping').ok" > /dev/null 2>&1; then
        # MongoDB está saudável
        exit 0
    fi
    
    # Se não for a última tentativa, aguardar antes de tentar novamente
    if [ $i -lt $MAX_RETRIES ]; then
        sleep $RETRY_DELAY
    fi
done

# MongoDB não está respondendo
exit 1

