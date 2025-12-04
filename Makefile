# =============================================================================
# Makefile - Pet Control System
# =============================================================================
# Comandos disponíveis:
#   make help     - Mostra esta ajuda
#   make dev      - Inicia ambiente de desenvolvimento completo
#   make test     - Inicia ambiente de testes (apenas PostgreSQL)
#   make db       - Inicia apenas o PostgreSQL
#   make down     - Para todos os containers
#   make clean    - Remove containers, volumes e imagens
#   make logs     - Mostra logs dos containers
#   make shell    - Abre shell no container da aplicação
#   make psql     - Abre psql no container do PostgreSQL
#   make migrate  - Executa migrações do banco
#   make seed     - Popula banco com dados iniciais
#   make pytest   - Executa testes automatizados
# =============================================================================

.PHONY: help dev test db down clean logs shell psql migrate seed pytest build status

# Cores para output
GREEN  := \033[0;32m
BLUE   := \033[0;34m
YELLOW := \033[1;33m
RED    := \033[0;31m
NC     := \033[0m

# =============================================================================
# Ajuda
# =============================================================================
help:
	@echo ""
	@echo "$(BLUE)╔═══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║         Pet Control System - Comandos Disponíveis             ║$(NC)"
	@echo "$(BLUE)╚═══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Ambientes:$(NC)"
	@echo "  $(YELLOW)make dev$(NC)      - Inicia desenvolvimento (PostgreSQL + App + Adminer)"
	@echo "  $(YELLOW)make test$(NC)     - Inicia ambiente de testes (apenas PostgreSQL)"
	@echo "  $(YELLOW)make db$(NC)       - Inicia apenas o PostgreSQL"
	@echo ""
	@echo "$(GREEN)Gerenciamento:$(NC)"
	@echo "  $(YELLOW)make down$(NC)     - Para todos os containers"
	@echo "  $(YELLOW)make clean$(NC)    - Remove containers, volumes e imagens"
	@echo "  $(YELLOW)make status$(NC)   - Mostra status dos containers"
	@echo "  $(YELLOW)make logs$(NC)     - Mostra logs (uso: make logs ou make logs s=app)"
	@echo ""
	@echo "$(GREEN)Banco de Dados:$(NC)"
	@echo "  $(YELLOW)make psql$(NC)     - Abre console psql"
	@echo "  $(YELLOW)make migrate$(NC)  - Executa migrações Alembic"
	@echo "  $(YELLOW)make seed$(NC)     - Popula banco com dados iniciais"
	@echo ""
	@echo "$(GREEN)Desenvolvimento:$(NC)"
	@echo "  $(YELLOW)make shell$(NC)    - Abre shell no container da app"
	@echo "  $(YELLOW)make pytest$(NC)   - Executa testes automatizados"
	@echo "  $(YELLOW)make build$(NC)    - Rebuild das imagens"
	@echo ""
	@echo "$(GREEN)Conexão PostgreSQL:$(NC)"
	@echo "  Host:     localhost"
	@echo "  Port:     5432"
	@echo "  Database: pet_control"
	@echo "  User:     pet_control_user"
	@echo "  Password: pet_control_pass"
	@echo ""

# =============================================================================
# Ambientes
# =============================================================================

# Desenvolvimento completo (PostgreSQL + App + Adminer)
dev:
	@echo "$(BLUE)🚀 Iniciando ambiente de desenvolvimento...$(NC)"
	docker compose --profile dev up -d --build
	@echo ""
	@echo "$(GREEN)✅ Ambiente iniciado!$(NC)"
	@echo ""
	@echo "$(YELLOW)📋 Serviços disponíveis:$(NC)"
	@echo "  - App:      http://localhost:8000"
	@echo "  - Adminer:  http://localhost:8080"
	@echo "  - PostgreSQL: localhost:5432"
	@echo ""
	@echo "$(YELLOW)Para ver logs:$(NC) make logs"

# Ambiente de testes (apenas PostgreSQL)
test: down
	@echo "$(BLUE)🧪 Iniciando ambiente de testes...$(NC)"
	docker compose --profile test up -d --build
	@echo ""
	@echo "$(YELLOW)⏳ Aguardando PostgreSQL estar pronto...$(NC)"
	@sleep 3
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if docker compose exec -T postgresql pg_isready -U postgres > /dev/null 2>&1; then \
			echo "$(GREEN)✅ PostgreSQL está pronto!$(NC)"; \
			break; \
		fi; \
		echo "  Tentativa $$i/10..."; \
		sleep 2; \
	done
	@echo ""
	@echo "$(GREEN)Conexão para testes:$(NC)"
	@echo "  DATABASE_URL=postgresql+asyncpg://pet_control_user:pet_control_pass@localhost:5432/pet_control"

# Apenas PostgreSQL
db:
	@echo "$(BLUE)🐘 Iniciando PostgreSQL...$(NC)"
	docker compose --profile db up -d --build
	@echo ""
	@echo "$(GREEN)✅ PostgreSQL iniciado!$(NC)"
	@echo "$(YELLOW)Para conectar:$(NC) make psql"

# =============================================================================
# Gerenciamento
# =============================================================================

# Para todos os containers
down:
	@echo "$(YELLOW)⏹️  Parando containers...$(NC)"
	docker compose --profile dev --profile test --profile db down
	@echo "$(GREEN)✅ Containers parados!$(NC)"

# Remove tudo (containers, volumes, imagens)
clean:
	@echo "$(RED)🧹 Removendo containers, volumes e imagens...$(NC)"
	docker compose --profile dev --profile test --profile db down -v --rmi local
	docker system prune -f
	@echo "$(GREEN)✅ Limpeza concluída!$(NC)"

# Status dos containers
status:
	@echo "$(BLUE)📊 Status dos containers:$(NC)"
	@docker compose ps -a

# Logs dos containers
logs:
ifdef s
	docker compose logs -f $(s)
else
	docker compose logs -f
endif

# =============================================================================
# Banco de Dados
# =============================================================================

# Console psql
psql:
	@echo "$(BLUE)🐘 Conectando ao PostgreSQL...$(NC)"
	docker compose exec postgresql psql -U pet_control_user -d pet_control

# Migrações Alembic
migrate:
	@echo "$(BLUE)📦 Executando migrações...$(NC)"
	docker compose exec app uv run alembic upgrade head
	@echo "$(GREEN)✅ Migrações executadas!$(NC)"

# Seeds do banco
seed:
	@echo "$(BLUE)🌱 Populando banco com dados iniciais...$(NC)"
	docker compose exec app uv run python -m app.database.seeds.run_seeds
	@echo "$(GREEN)✅ Seeds executados!$(NC)"

# =============================================================================
# Desenvolvimento
# =============================================================================

# Shell no container da app
shell:
	docker compose exec app /bin/bash

# Rebuild das imagens
build:
	@echo "$(BLUE)🔨 Rebuild das imagens...$(NC)"
	docker compose build --no-cache
	@echo "$(GREEN)✅ Build concluído!$(NC)"

# Executa testes
pytest:
	@echo "$(BLUE)🧪 Executando testes...$(NC)"
	@export DATABASE_URL="postgresql+asyncpg://pet_control_user:pet_control_pass@localhost:5432/pet_control" && \
	uv run pytest -v
	@echo "$(GREEN)✅ Testes concluídos!$(NC)"

# =============================================================================
# Atalhos úteis
# =============================================================================

# Reinicia ambiente de dev
restart: down dev

# Rebuild e reinicia
rebuild: clean dev

