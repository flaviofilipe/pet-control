# 🐾 Pet Control - Sistema de Gerenciamento de Pets

## 🚀 Quick Start (Docker)

```bash
# 1. Clone o projeto
git clone <url-do-repositorio>
cd pet-app

# 2. Configure variáveis de ambiente
cp env.example .env
nano .env  # Configure Auth0 e outras variáveis

# 3. Execute com Docker
./build-postgresql-test.sh  # Cria imagem PostgreSQL
docker-compose -f docker-compose.dev.yml up -d

# 4. Execute migrations
export DATABASE_URL="postgresql+asyncpg://pet_control_user:dev_password@localhost:5432/pet_control_dev"
uv run alembic upgrade head

# 5. Acesse a aplicação
curl http://localhost:8000/health  # Verificar se está funcionando
open http://localhost:8000         # Abrir no navegador
```

## 📋 Sobre o Projeto

O **Pet Control** é uma aplicação web completa desenvolvida em Python com FastAPI para o gerenciamento abrangente de pets domésticos. O sistema oferece autenticação segura, cadastro de pets com upload de fotos, controle de tratamentos veterinários (vacinas, ectoparasitas e vermífugos), **sistema de notificações por email**, além de um dashboard intuitivo para acompanhamento da saúde dos animais.

A aplicação é ideal para:
- 🏠 **Tutores de pets** que desejam manter um histórico organizado dos cuidados veterinários
- 🩺 **Veterinários** que precisam acompanhar seus pacientes  
- 🔔 **Clínicas** que querem automatizar lembretes de tratamentos
- 📊 **Gestores** que necessitam de relatórios de saúde animal

## Funcionalidades

- ✅ Autenticação segura com Auth0
- ✅ Cadastro e gerenciamento de pets
- ✅ Upload de fotos com validação e crop
- ✅ Suporte a múltiplos formatos (JPG, PNG, GIF, WebP)
- ✅ Criação automática de miniaturas
- ✅ Interface de crop intuitiva
- ✅ Dashboard responsivo com fotos
- ✅ Perfis de usuário
- ✅ Histórico de tratamentos
- ✅ **Sistema de notificações por email** (tratamentos diários e relatórios mensais)
- ✅ **Health checks** e monitoramento da aplicação
- ✅ **Docker containerizado** para desenvolvimento e produção
- ✅ **PostgreSQL** como banco de dados relacional

## 🚀 Instalação e Configuração

### Pré-requisitos

#### **Opção 1: Desenvolvimento com Docker (Recomendado)**
- **Docker** - Para containerização
- **Docker Compose** - Para orquestração de serviços
- **Conta Auth0** - Para autenticação

#### **Opção 2: Desenvolvimento Local**
- **Python 3.12+** - Linguagem de programação principal
- **PostgreSQL 15+** - Banco de dados relacional
- **UV** - Gerenciador de dependências (recomendado)
- **Conta Auth0** - Para autenticação

## 🚀 Instalação com Docker (Recomendado)

### 🐳 Setup Rápido para Desenvolvimento

#### 1️⃣ Clone o repositório
```bash
git clone <url-do-repositorio>
cd pet-app
```

#### 2️⃣ Configure as variáveis de ambiente

Copie o arquivo de exemplo e configure suas credenciais:

```bash
# Copiar template de configuração
cp env.example .env

# Edite o arquivo .env com suas informações reais
nano .env  # ou seu editor preferido
```

**Variáveis obrigatórias no arquivo `.env`:**
```env
# ========== Auth0 Configuration (OBRIGATÓRIO) ==========
# Obtenha essas informações em https://manage.auth0.com
AUTH0_DOMAIN=seu-dominio.auth0.com
AUTH0_API_AUDIENCE=seu-audience
AUTH0_CLIENT_ID=seu-client-id
AUTH0_CLIENT_SECRET=seu-client-secret
AUTH0_CALLBACK_URI=http://localhost:8000/callback

# ========== PostgreSQL Configuration ==========
DATABASE_URL=postgresql+asyncpg://pet_control_user:pet_control_pass@localhost:5432/pet_control
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# ========== Session Configuration (OBRIGATÓRIO) ==========
# Gere uma chave segura: python -c "import secrets; print(secrets.token_urlsafe(32))"
SESSION_SECRET_KEY=sua-chave-secreta-super-segura-aqui

# ========== Gmail Configuration (OPCIONAL) ==========
# Necessário apenas para notificações de tratamentos
GMAIL_EMAIL=seu-email@gmail.com
GMAIL_PASSWORD=sua-senha-de-app-gmail
GMAIL_SMTP_SERVER=smtp.gmail.com
GMAIL_SMTP_PORT=587
```

#### 3️⃣ Configure o Auth0

1. **Crie uma aplicação no Auth0:**
   - Acesse [Auth0 Dashboard](https://manage.auth0.com)
   - Crie uma nova aplicação do tipo "Regular Web Application"
   - Configure as URLs:
     - **Allowed Callback URLs**: `http://localhost:8000/callback`
     - **Allowed Logout URLs**: `http://localhost:8000/`
     - **Allowed Web Origins**: `http://localhost:8000`

2. **Configure as permissões:**
   - Ative "Allow Offline Access" para refresh tokens
   - Configure os escopos: `openid profile email`

#### 4️⃣ Execute a aplicação

```bash
# Build da imagem PostgreSQL customizada
./build-postgresql-test.sh

# Inicie todos os serviços (aplicação + PostgreSQL)
docker-compose -f docker-compose.dev.yml up -d

# Execute as migrations
export DATABASE_URL="postgresql+asyncpg://pet_control_user:dev_password@localhost:5432/pet_control_dev"
uv run alembic upgrade head

# Execute os seeds (dados iniciais)
uv run python -m app.database.seeds.run_seeds

# Verificar se está funcionando
curl http://localhost:8000/health
```

#### 5️⃣ Acesse a aplicação

- **Aplicação Web**: [http://localhost:8000](http://localhost:8000)
- **Documentação API**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### 🔧 Comandos Úteis do Docker

```bash
# Ver logs da aplicação
docker-compose -f docker-compose.dev.yml logs -f app

# Ver status dos containers
docker-compose -f docker-compose.dev.yml ps

# Parar todos os serviços
docker-compose -f docker-compose.dev.yml down

# Rebuild da aplicação (após mudanças no código)
docker-compose -f docker-compose.dev.yml up -d --build

# Executar tasks de notificação dentro do container
docker exec pet-control-app-dev uv run python daily_check.py --dry-run --verbose
docker exec pet-control-app-dev uv run python monthly_check.py --dry-run --verbose

# Acessar o container da aplicação
docker exec -it pet-control-app-dev bash

# Acessar PostgreSQL
docker exec -it pet-control-postgresql-dev psql -U pet_control_user -d pet_control_dev
```

---

## 🔧 Instalação Local (Alternativa)

### Para desenvolvedores que preferem setup local sem Docker:

#### 1️⃣ Clone e configure dependências
```bash
git clone <url-do-repositorio>
cd pet-app

# Instalar UV (se não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
# ou: pip install uv

# Instalar dependências
uv sync
```

#### 2️⃣ Configure PostgreSQL local

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS (Homebrew)
brew install postgresql@15
brew services start postgresql@15

# Criar banco de dados
sudo -u postgres psql
CREATE USER pet_control_user WITH PASSWORD 'pet_control_pass';
CREATE DATABASE pet_control OWNER pet_control_user;
GRANT ALL PRIVILEGES ON DATABASE pet_control TO pet_control_user;
\q
```

#### 3️⃣ Configure variáveis de ambiente
```bash
cp env.example .env
nano .env  # Configure suas variáveis
```

#### 4️⃣ Execute migrations e seeds
```bash
export DATABASE_URL="postgresql+asyncpg://pet_control_user:pet_control_pass@localhost:5432/pet_control"

# Criar tabelas
uv run alembic upgrade head

# Popular dados iniciais
uv run python -m app.database.seeds.run_seeds
```

#### 5️⃣ Execute a aplicação
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🗄️ Banco de Dados PostgreSQL

### Estrutura das Tabelas

| Tabela | Descrição |
|--------|-----------|
| `profiles` | Usuários do sistema |
| `pets` | Pets cadastrados |
| `pet_owners` | Relacionamento entre pets e proprietários |
| `treatments` | Tratamentos veterinários |
| `vaccines` | Informações sobre vacinas |
| `ectoparasites` | Informações sobre ectoparasitas |
| `vermifugos` | Informações sobre vermífugos |

### Migrations

```bash
# Criar nova migration
uv run alembic revision --autogenerate -m "Descrição da mudança"

# Aplicar migrations
uv run alembic upgrade head

# Reverter última migration
uv run alembic downgrade -1

# Ver histórico de migrations
uv run alembic history
```

### Conexão via DBeaver

| Campo | Valor |
|-------|-------|
| **Host** | `localhost` |
| **Port** | `5432` |
| **Database** | `pet_control` |
| **Username** | `pet_control_user` |
| **Password** | `pet_control_pass` |

---

## 📧 Sistema de Notificações

### Configuração do Gmail

1. Ative a verificação em duas etapas na sua conta Google
2. Gere uma "Senha de App" em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Use essa senha de app no `GMAIL_PASSWORD`

### Executar Notificações

```bash
# Notificação diária (tratamentos do dia seguinte)
uv run python daily_check.py --dry-run --verbose

# Relatório mensal
uv run python monthly_check.py --dry-run --verbose
```

---

## 🧪 Testes

```bash
# Executar todos os testes
uv run pytest

# Com cobertura
uv run pytest --cov=app --cov-report=html

# Testes específicos
uv run pytest tests/test_auth.py -v
```

---

## 📁 Estrutura do Projeto

```
pet-app/
├── app/
│   ├── database/
│   │   ├── migrations/      # Migrations Alembic
│   │   ├── models/          # SQLAlchemy Models
│   │   ├── seeds/           # Dados iniciais
│   │   ├── base.py          # Base do SQLAlchemy
│   │   └── connection.py    # Configuração de conexão
│   ├── repositories/        # Camada de acesso a dados
│   ├── routes/              # Endpoints da API
│   ├── services/            # Lógica de negócio
│   ├── config.py            # Configurações
│   └── main.py              # Ponto de entrada
├── templates/               # Templates Jinja2
├── static/                  # Arquivos estáticos
├── tests/                   # Testes
├── postgresql/              # Configurações PostgreSQL
│   ├── config/              # postgresql.conf
│   ├── init/                # Scripts de inicialização
│   └── scripts/             # Scripts auxiliares
├── alembic.ini              # Configuração Alembic
├── docker-compose.yml       # Docker Compose (produção)
├── docker-compose.dev.yml   # Docker Compose (desenvolvimento)
├── Dockerfile               # Dockerfile da aplicação
├── Dockerfile.postgresql    # Dockerfile do PostgreSQL
├── pyproject.toml           # Dependências do projeto
└── env.example              # Exemplo de variáveis de ambiente
```

---

## 🔒 Segurança

- Autenticação via Auth0 (OAuth 2.0)
- Sessões seguras com cookies HTTPOnly
- CORS configurado
- Soft delete para dados sensíveis
- Validação de entrada com Pydantic

---

## 📝 Licença

Este projeto está sob a licença MIT.

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request
