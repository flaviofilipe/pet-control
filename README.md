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
docker build -t pet-control:dev .
docker-compose -f docker-compose.dev.yml up -d

# 4. Acesse a aplicação
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

## 🚀 Instalação e Configuração

### Pré-requisitos

#### **Opção 1: Desenvolvimento com Docker (Recomendado)**
- **Docker** - Para containerização
- **Docker Compose** - Para orquestração de serviços
- **Conta Auth0** - Para autenticação

#### **Opção 2: Desenvolvimento Local**
- **Python 3.12+** - Linguagem de programação principal
- **MongoDB** - Banco de dados (local ou remoto)
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

# ========== MongoDB Configuration ==========
# Para Docker (já configurado automaticamente)
MONGO_URI=mongodb://root:root@mongodb:27017/
DB_NAME=pet_control

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
# Build da imagem Docker (primeira vez)
docker build -t pet-control:dev .

# Inicie todos os serviços (aplicação + MongoDB)
docker-compose -f docker-compose.dev.yml up -d

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
docker exec pet-control-dev uv run python daily_check.py --dry-run --verbose
docker exec pet-control-dev uv run python monthly_check.py --dry-run --verbose

# Acessar o container da aplicação
docker exec -it pet-control-dev bash

# Acessar MongoDB
docker exec -it pet-control-mongodb-dev mongosh -u root -p root
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

#### 2️⃣ Configure MongoDB local
```bash
# Ubuntu/Debian
sudo apt-get install mongodb-server
sudo systemctl start mongodb

# macOS (Homebrew)
brew install mongodb/brew/mongodb-community
brew services start mongodb/brew/mongodb-community
```

#### 3️⃣ Configure variáveis de ambiente
```bash
# Copie e edite as configurações
cp env.example .env

# Configure MONGO_URI para local:
# MONGO_URI=mongodb://localhost:27017/
```

#### 4️⃣ Execute a aplicação
```bash
# Com UV (recomendado)
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Ou ativando ambiente virtual manualmente
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📧 Sistema de Notificações

O Pet Control inclui um sistema completo de notificações por email para lembretes de tratamentos.

### 🗓️ Notificação Diária (`daily_check.py`)
Envia lembretes sobre tratamentos agendados para **amanhã**.

### 📊 Relatório Mensal (`monthly_check.py`)
Envia relatório consolidado com:
- Tratamentos agendados para o **mês atual**
- Tratamentos **expirados** que precisam de atenção

### 🚀 Como usar as notificações

```bash
# Executar dentro do container Docker
docker exec pet-control-dev uv run python daily_check.py --dry-run --verbose
docker exec pet-control-dev uv run python monthly_check.py --dry-run --verbose

# Executar localmente (se instalação local)
uv run python daily_check.py --dry-run --verbose
uv run python monthly_check.py --dry-run --verbose

# Executar em produção (envia emails reais)
docker exec pet-control-dev uv run python daily_check.py
docker exec pet-control-dev uv run python monthly_check.py
```

### 📋 Configuração para Automação

Para automação via **cron** (Linux/macOS):
```bash
# Editar crontab
crontab -e

# Adicionar linhas para execução automática:
# Todos os dias às 09:00 - notificação diária
0 9 * * * cd /path/to/pet-app && docker exec pet-control-dev uv run python daily_check.py

# Todo primeiro dia do mês às 10:00 - relatório mensal
0 10 1 * * cd /path/to/pet-app && docker exec pet-control-dev uv run python monthly_check.py
```

Para mais detalhes, veja: `app/tasks/README.md`

---

### 🔍 Verificação da Instalação

1. **Teste da aplicação**: Acesse `http://localhost:8000`
2. **Teste de health check**: Acesse `http://localhost:8000/health`
3. **Teste de autenticação**: Clique em "Login" e faça login via Auth0
4. **Teste do banco**: Vá para o dashboard e tente cadastrar um pet
5. **Teste de upload**: Adicione uma foto a um pet
6. **Teste de notificações**: Execute `daily_check.py --dry-run --verbose`

### ⚠️ Solução de Problemas Comuns

#### **🐳 Problemas com Docker**

**Container não inicia ou falha no health check:**
```bash
# Verificar logs da aplicação
docker-compose -f docker-compose.dev.yml logs app

# Verificar se variáveis de ambiente estão corretas
docker exec pet-control-dev env | grep AUTH0

# Rebuild completo
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d --build
```

**Erro "Connection reset by peer" no curl:**
```bash
# Aguardar inicialização completa (10-15 segundos)
sleep 15 && curl http://localhost:8000/health

# Verificar se MongoDB está conectado
docker-compose -f docker-compose.dev.yml logs mongodb
```

**Porta 8000 já em uso:**
```bash
# Verificar o que está usando a porta
sudo lsof -i :8000

# Parar containers e tentar novamente
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

#### **🗃️ Problemas com MongoDB**

**Erro de conexão (instalação local):**
```bash
# Verificar se o MongoDB está rodando
sudo systemctl status mongodb  # Linux
brew services list | grep mongodb  # macOS

# Testar conexão
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('Conexão OK')"
```

#### **🔐 Problemas com Auth0**

**Erro "Auth0 environment variables must be set":**
- Verifique se o arquivo `.env` existe e está configurado
- Confirme se as variáveis AUTH0_* estão todas preenchidas
- Verifique se as URLs de callback estão corretas no Auth0 Dashboard

**Erro de autenticação:**
- **Allowed Callback URLs**: `http://localhost:8000/callback`
- **Allowed Logout URLs**: `http://localhost:8000/`
- **Allowed Web Origins**: `http://localhost:8000`
- Confirme se o CLIENT_SECRET está correto
- Verifique se todos os escopos estão configurados: `openid profile email`

#### **📧 Problemas com Notificações**

**Erro nas tasks de notificação:**
```bash
# Testar configuração do Gmail
docker exec pet-control-dev python -c "from app.config import validate_gmail_config; print(validate_gmail_config())"

# Executar em modo verbose para debug
docker exec pet-control-dev uv run python daily_check.py --dry-run --verbose
```

#### **🔧 Problemas Gerais**

**Erro de dependências:**
```bash
# Limpar cache e reinstalar
uv cache clean
uv sync --refresh

# Para Docker - rebuild da imagem
docker build -t pet-control:dev . --no-cache
```

**Erro de permissões (Linux):**
```bash
# Dar permissões corretas para uploads
sudo chown -R $USER:$USER uploads/
chmod 755 uploads/
```

## Funcionalidade de Upload de Fotos

### Características de Segurança
- ✅ Validação de tipos de arquivo (JPG, PNG, GIF, WebP, HEIC)
- ✅ Limite de tamanho (10MB máximo)
- ✅ Criação automática de miniaturas
- ✅ Interface de crop intuitiva
- ✅ Armazenamento seguro em diretórios separados por pet
- ✅ Limpeza automática de arquivos antigos
- ✅ Fallback para conversão quando necessário

### Como Usar
1. **Cadastro de Pet**: Acesse `/pets/form` e selecione uma foto
2. **Crop da Imagem**: Use a interface de crop para ajustar a foto antes do upload
3. **Edição de Pet**: Acesse `/pets/{id}/edit` para atualizar a foto
4. **Visualização**: As fotos aparecem no dashboard e perfil do pet
5. **Formatos Suportados**: JPG, PNG, GIFe WebP

### Estrutura de Arquivos
```
uploads/
├── pet_id_1/
│   ├── foto_original.jpg
│   └── thumb_foto_original.jpg
└── pet_id_2/
    ├── foto_original.png
    └── thumb_foto_original.png
```

## 🌐 API Endpoints

### 🏥 Health & Monitoring
- `GET /health` - Health check da aplicação (status, database, versão)

### 🔐 Autenticação
- `GET /login` - Login via Auth0
- `GET /callback` - Callback do Auth0 
- `GET /logout` - Logout e limpeza de sessão
- `GET /dashboard` - Dashboard principal (autenticado)

### 👤 Usuário
- `GET /user` - Perfil do usuário
- `GET /user/profile` - Página de perfil
- `POST /user/profile` - Atualizar perfil
- `GET /user/update` - Formulário de edição

### 🐕 Pets
- `GET /pets/form` - Formulário de cadastro
- `POST /pets` - Criar/atualizar pet (com upload de foto)
- `GET /pets/{id}/edit` - Formulário de edição
- `GET /pets/{id}/profile` - Perfil detalhado do pet
- `POST /pets/{id}/delete` - Excluir pet (soft delete)

### 💉 Tratamentos
- `GET /pets/{pet_id}/treatment/form` - Formulário de tratamento
- `POST /pets/{pet_id}/treatment` - Criar/atualizar tratamento
- `POST /pets/{pet_id}/treatment/{treatment_id}/toggle` - Marcar como concluído/pendente
- `POST /pets/{pet_id}/treatment/{treatment_id}/delete` - Excluir tratamento

### 📚 Informações Veterinárias
- `GET /info/vacinas` - Catálogo de vacinas
- `GET /info/ectoparasitas` - Catálogo de ectoparasitas
- `GET /autocomplete/vacinas` - API de busca em vacinas
- `GET /autocomplete/ectoparasitas` - API de busca em ectoparasitas

### 🩺 Veterinário (Rotas Especiais)
- `GET /vet/dashboard` - Dashboard especializado para veterinários
- `GET /vet/patients` - Lista de pacientes (pets)

### 📄 Documentação
- `GET /docs` - Documentação interativa Swagger UI
- `GET /redoc` - Documentação ReDoc alternativa

## 🛠️ Tecnologias Utilizadas

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno e rápido para construção de APIs com Python
- **[Uvicorn](https://www.uvicorn.org/)** - Servidor ASGI para aplicações Python assíncronas
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Validação de dados usando type hints do Python
- **[Jinja2](https://jinja.palletsprojects.com/)** - Engine de templates para renderização HTML

### Banco de Dados
- **[MongoDB](https://www.mongodb.com/)** - Banco de dados NoSQL orientado a documentos
- **[PyMongo](https://pymongo.readthedocs.io/)** - Driver oficial do MongoDB para Python

### Autenticação e Segurança
- **[Auth0](https://auth0.com/)** - Plataforma de identidade e autenticação
- **[Sessions Middleware](https://www.starlette.io/middleware/)** - Gerenciamento de sessões de usuário
- **[Python-dotenv](https://pypi.org/project/python-dotenv/)** - Carregamento de variáveis de ambiente

### Processamento de Imagens
- **[Pillow (PIL)](https://pillow.readthedocs.io/)** - Biblioteca para manipulação e processamento de imagens
- **[Pillow-HEIF](https://pypi.org/project/pillow-heif/)** - Suporte para formatos HEIC/HEIF

### Frontend
- **HTML5** - Estrutura das páginas web
- **[Tailwind CSS](https://tailwindcss.com/)** - Framework CSS utilitário para estilização
- **JavaScript** - Interatividade e funcionalidades dinâmicas
- **[Cropper.js](https://fengyuanchen.github.io/cropperjs/)** - Biblioteca para crop de imagens

### Ferramentas de Desenvolvimento
- **[UV](https://github.com/astral-sh/uv)** - Gerenciador de dependências Python ultrarrápido
- **[Docker](https://www.docker.com/)** - Containerização da aplicação
- **[Docker Compose](https://docs.docker.com/compose/)** - Orquestração de containers

### Sistema de Notificações
- **[smtplib](https://docs.python.org/3/library/smtplib.html)** - Envio de emails via SMTP
- **[Jinja2](https://jinja.palletsprojects.com/)** - Templates HTML para emails
- **Sistema de Tasks** - Notificações diárias e relatórios mensais automatizados

### Monitoramento e Saúde
- **Health Checks** - Endpoint `/health` para monitoramento
- **Logging Estruturado** - Sistema de logs detalhado para debugging
- **Environment Detection** - Detecção automática de ambiente (dev/prod)

### Bibliotecas Auxiliares
- **[Requests](https://requests.readthedocs.io/)** - Biblioteca para requisições HTTP
- **[Faker](https://faker.readthedocs.io/)** - Geração de dados fictícios para testes
- **[Faker-Food](https://pypi.org/project/faker-food/)** - Extensão do Faker para nomes de comidas

## 📁 Organização do Projeto

### Estrutura de Diretórios
```
pet-app/
├── 📄 main.py                          # Arquivo principal da aplicação
├── 📄 pyproject.toml                   # Configuração do projeto e dependências (UV)
├── 📄 dockerfile                       # Dockerfile inteligente (dev/prod)
├── 📄 docker-compose.dev.yml           # Docker Compose para desenvolvimento
├── 📄 docker-compose.production.yml    # Docker Compose para produção
├── 📄 .dockerignore                    # Arquivos ignorados no build Docker
├── 📄 env.example                      # Template de variáveis de ambiente
├── 📄 daily_check.py                   # Script de conveniência para task diária
├── 📄 monthly_check.py                 # Script de conveniência para task mensal
├── 📄 create_vermifugos_collection.py  # Script para popular dados de vermífugos
├── 📄 README.md                        # Documentação do projeto
├── 📄 uv.lock                          # Lock file de dependências (UV)
├── 📁 app/                             # Código principal da aplicação
│   ├── 📄 __init__.py
│   ├── 📄 main.py                      # Configuração principal FastAPI
│   ├── 📄 config.py                    # Configurações e variáveis de ambiente
│   ├── 📄 database.py                  # Conexão com MongoDB
│   ├── 📁 routes/                      # Rotas da API organizadas por módulo
│   │   ├── 📄 __init__.py
│   │   ├── 📄 auth_routes.py           # Rotas de autenticação
│   │   ├── 📄 dashboard_routes.py      # Rotas do dashboard
│   │   ├── 📄 user_routes.py           # Rotas de usuário
│   │   ├── 📄 pet_routes.py            # Rotas de pets
│   │   ├── 📄 treatment_routes.py      # Rotas de tratamentos
│   │   ├── 📄 info_routes.py           # Rotas informativas
│   │   └── 📄 vet_routes.py            # Rotas veterinárias
│   ├── 📁 services/                    # Regras de negócio e lógica da aplicação
│   │   ├── 📄 __init__.py
│   │   ├── 📄 file_service.py          # Serviço de upload/manipulação de arquivos
│   │   ├── 📄 pet_service.py           # Lógica de negócio de pets
│   │   ├── 📄 user_service.py          # Lógica de negócio de usuários
│   │   ├── 📄 notification_service.py  # Serviço de notificações diárias
│   │   ├── 📄 monthly_report_service.py # Serviço de relatórios mensais
│   │   └── 📁 templates/               # Templates HTML para emails
│   │       ├── 📄 treatment_reminder.html      # Template notificação diária
│   │       └── 📄 consolidated_monthly_report.html # Template relatório mensal
│   ├── 📁 repositories/                # Camada de acesso a dados (MongoDB)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base_repository.py       # Repositório base com operações comuns
│   │   ├── 📄 user_repository.py       # Repositório de usuários
│   │   └── 📄 pet_repository.py        # Repositório de pets
│   └── 📁 tasks/                       # Tasks de notificação e automação
│       ├── 📄 __init__.py
│       ├── 📄 README.md                # Documentação das tasks
│       ├── 📄 daily_check.py           # Task de verificação diária
│       └── 📄 monthly_check.py         # Task de relatório mensal
├── 📁 templates/                       # Templates HTML (Jinja2) da interface web
│   ├── 📄 index.html                   # Página inicial
│   ├── 📄 dashboard.html               # Dashboard principal
│   ├── 📄 profile.html                 # Perfil do usuário
│   ├── 📄 profile_update.html          # Edição de perfil
│   ├── 📄 pet_form.html                # Formulário de pets
│   ├── 📄 pet_profile.html             # Perfil do pet
│   ├── 📄 treatment_form.html          # Formulário de tratamentos
│   ├── 📄 error.html                   # Página de erro
│   └── 📁 pages/
│       ├── 📄 vacinas.html             # Catálogo de vacinas
│       └── 📄 ectoparasitas.html       # Catálogo de ectoparasitas
├── 📁 static/                          # Arquivos estáticos (CSS, JS, imagens)
│   ├── 📄 index.css                    # Estilos da página inicial
│   ├── 📄 landing-page.css             # Estilos da landing page
│   └── 📁 assets/                      # Assets diversos (imagens, ícones)
└── 📁 uploads/                         # Diretório de upload de fotos
    └── 📁 {pet_id}/                    # Fotos organizadas por pet
        ├── 📄 original.jpg             # Imagem original
        └── 📄 thumb_original.jpg       # Miniatura
```

### 🏗️ Módulos e Funcionalidades

#### 🔐 Sistema de Autenticação
- **Auth0 Integration**: Autenticação OAuth2 completa
- **Session Management**: Gerenciamento de sessões de usuário
- **Token Refresh**: Renovação automática de tokens
- **Cache de Usuários**: Sistema de cache para otimizar requisições

**Rotas principais:**
- `/login` - Login via Auth0
- `/callback` - Callback de autenticação
- `/logout` - Logout com limpeza completa

#### 👤 Gerenciamento de Usuários
- **Perfis de Usuário**: Cadastro e edição de informações pessoais
- **Suporte a Veterinários**: Flag especial para profissionais
- **Endereços**: Sistema de endereços completo
- **Integração Auth0**: Sincronização com dados do Auth0

**Funcionalidades:**
- Criação/atualização de perfis
- Diferenciação entre tutores e veterinários
- Fallback para dados do Auth0

#### 🐕 Sistema de Pets
- **Cadastro Completo**: Nome, raça, data de nascimento, pedigree
- **Suporte Multi-espécie**: Cães e gatos com raças específicas
- **Upload de Fotos**: Sistema robusto de upload com validação
- **Nicknames Únicos**: Geração automática de identificadores
- **Soft Delete**: Exclusão lógica mantendo histórico

**APIs externas integradas:**
- **Dog CEO API**: Lista de raças de cães
- **Cat API**: Lista de raças de gatos

#### 🏥 Sistema de Tratamentos
- **Categorias**: Vacinas, Ectoparasitas, Vermífugos, Tratamentos Gerais
- **Agendamento**: Sistema de datas com status (agendado/expirado/concluído)
- **Responsáveis**: Veterinário ou tutor aplicador
- **Histórico Completo**: Registro detalhado de todos os tratamentos
- **Pesquisa e Filtros**: Sistema de busca em tratamentos

#### 📸 Sistema de Upload de Imagens
- **Validação Robusta**: Tipos de arquivo, tamanho, integridade
- **Processamento Automático**: Redimensionamento e otimização
- **Miniaturas**: Geração automática de thumbnails
- **Organização**: Diretórios separados por pet
- **Formatos Suportados**: JPG, PNG, GIF, WebP
- **Interface de Crop**: Ferramenta intuitiva para ajuste de imagens

#### 📊 Base de Conhecimento Veterinário
- **Catálogo de Vacinas**: Base completa com descrições e indicações
- **Catálogo de Ectoparasitas**: Informações sobre pragas e tratamentos
- **Sistema de Busca**: Filtros por espécie, tipo e termos livres
- **Autocomplete**: Sugestões em tempo real para tratamentos

#### 🔍 APIs e Endpoints
- **RESTful Design**: Endpoints organizados e padronizados
- **Autocomplete APIs**: Sugestões para vacinas e ectoparasitas
- **Dashboard API**: Dados consolidados para visualização
- **CORS Configurado**: Suporte para integração com frontends

---

## 🚀 Deploy em Produção

### 🏭 Preparação para Produção

#### 1. Configuração de Variáveis de Ambiente
```bash
# Copie e configure para produção
cp env.example .env.production

# Edite com valores reais de produção
nano .env.production
```

**Configurações críticas para produção:**
```env
# Environment
ENV=production

# Auth0 (URLs de produção)
AUTH0_DOMAIN=seu-dominio.auth0.com
AUTH0_CALLBACK_URI=https://seudominio.com/callback

# MongoDB (Atlas recomendado para produção)
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/

# Session (chave forte)
SESSION_SECRET_KEY=chave-ultra-segura-de-64-caracteres-minimo

# Gmail (configuração real)
GMAIL_EMAIL=notifications@seudominio.com
GMAIL_PASSWORD=senha-de-app-real
```

#### 2. Build da Imagem de Produção
```bash
# Build otimizado para produção
docker build --build-arg ENV=production -t pet-control:latest .

# Tag para registry
docker tag pet-control:latest your-registry.com/pet-control:latest

# Push para registry
docker push your-registry.com/pet-control:latest
```

#### 3. Deploy com Docker Compose
```bash
# Deploy em produção
docker-compose -f docker-compose.production.yml up -d

# Verificar saúde da aplicação
curl https://seudominio.com/health

# Monitorar logs
docker-compose -f docker-compose.production.yml logs -f app
```

### 🔒 Configurações de Segurança Implementadas

#### **Aplicação**
- ✅ Autenticação obrigatória para todas as rotas protegidas
- ✅ Validação rigorosa de tipos de arquivo e tamanhos
- ✅ Sanitização de nomes de arquivo e inputs
- ✅ Armazenamento isolado por usuário/pet
- ✅ Sessions seguras com chaves criptográficas
- ✅ Usuário não-root em containers de produção

#### **Docker & Infraestrutura** 
- ✅ Multi-stage build para imagens menores
- ✅ Health checks automatizados
- ✅ Logs estruturados para auditoria
- ✅ Variáveis de ambiente externalizadas
- ✅ Containers com restart automático

#### **Banco de Dados**
- ✅ Conexões autenticadas com MongoDB
- ✅ Timeout configurado para operações
- ✅ Soft delete para preservar dados históricos

### 📊 Monitoramento em Produção

```bash
# Health check da aplicação
curl https://seudominio.com/health

# Logs da aplicação
docker logs pet-control-prod -f

# Status dos containers  
docker ps

# Usar com sistemas de monitoramento (Prometheus, etc.)
curl https://seudominio.com/health | jq .status
```

### 🔄 Automação das Tasks

#### **Cron para Notificações (Servidor Linux)**
```bash
# Editar crontab
sudo crontab -e

# Adicionar automações:
# Notificação diária às 09:00
0 9 * * * cd /path/to/pet-app && docker exec pet-control-prod python daily_check.py

# Relatório mensal no dia 1 às 10:00
0 10 1 * * cd /path/to/pet-app && docker exec pet-control-prod python monthly_check.py

# Verificar logs das execuções
tail -f /var/log/cron
```

---

## 🛡️ Segurança

- **Autenticação**: Auth0 OAuth2 com tokens seguros
- **Validação**: Tipos de arquivo, tamanhos e integridade
- **Sanitização**: Nomes de arquivo e inputs de usuário
- **Isolamento**: Armazenamento separado por usuário
- **Containers**: Usuário não-root em produção
- **Sessions**: Chaves criptográficas fortes
- **Logs**: Auditoria completa de ações

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT.
