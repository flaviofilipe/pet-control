# Pet App - Sistema de Gerenciamento de Pets

## 📋 Resumo

O **Pet App** é uma aplicação web completa desenvolvida em Python com FastAPI para o gerenciamento abrangente de pets domésticos. O sistema oferece autenticação segura, cadastro de pets com upload de fotos, controle de tratamentos veterinários (vacinas, ectoparasitas e vermífugos), além de um dashboard intuitivo para acompanhamento da saúde dos animais.

A aplicação é ideal para tutores de pets que desejam manter um histórico organizado dos cuidados veterinários, veterinários que precisam acompanhar seus pacientes, e qualquer pessoa que queira ter controle total sobre a saúde e bem-estar de seus animais de estimação.

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

## 🚀 Instalação e Configuração

### Pré-requisitos
- **Python 3.8+** - Linguagem de programação principal
- **MongoDB** - Banco de dados (local ou remoto)
- **UV** - Gerenciador de dependências (recomendado)
- **Conta Auth0** - Para autenticação

### 🔧 Instalação Rápida

#### 1️⃣ Clone o repositório
```bash
git clone <url-do-repositorio>
cd pet-app
```

#### 2️⃣ Instale o UV (se não tiver)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Ou via pip
pip install uv
```

#### 3️⃣ Instale as dependências
```bash
# Método recomendado - UV (cria ambiente virtual automaticamente)
uv sync

# Método alternativo - pip
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### 4️⃣ Configure o banco de dados MongoDB

**Opção A: MongoDB local**
```bash
# Instalar MongoDB localmente
# Ubuntu/Debian
sudo apt-get install mongodb

# macOS (Homebrew)
brew install mongodb/brew/mongodb-community

# Iniciar serviço
sudo systemctl start mongodb  # Linux
brew services start mongodb/brew/mongodb-community  # macOS
```

**Opção B: MongoDB Atlas (Nuvem)**
1. Crie uma conta gratuita em [MongoDB Atlas](https://cloud.mongodb.com)
2. Crie um cluster gratuito
3. Configure as credenciais de acesso
4. Copie a string de conexão

**Opção C: Docker (Recomendado para desenvolvimento)**
```bash
# O docker-compose já está configurado
docker-compose up mongodb -d
```

#### 5️⃣ Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# ========== Auth0 Configuration ==========
# Obtenha essas informações em https://manage.auth0.com
AUTH0_DOMAIN=seu-dominio.auth0.com
AUTH0_API_AUDIENCE=seu-audience  
AUTH0_CLIENT_ID=seu-client-id
AUTH0_CLIENT_SECRET=seu-client-secret
AUTH0_CALLBACK_URI=http://localhost:8000/callback

# ========== MongoDB Configuration ==========
# Local
MONGO_URI=mongodb://localhost:27017/
# Docker
# MONGO_URI=mongodb://root:root@localhost:27017/
# Atlas (substitua por sua string de conexão)
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/

# ========== Session Configuration ==========
# Gere uma chave segura: python -c "import secrets; print(secrets.token_urlsafe(32))"
SESSION_SECRET_KEY=sua-chave-secreta-super-segura-aqui
```

#### 6️⃣ Configure o Auth0

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

#### 7️⃣ Popular dados iniciais (Opcional)

```bash
# Executar script para popular catálogo de vermífugos
uv run python create_vermifugos_collection.py
```

#### 8️⃣ Execute a aplicação

```bash
# Usando UV (recomendado)
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Ou com ambiente virtual ativado
source .venv/bin/activate  # Linux/Mac
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 9️⃣ Acesse a aplicação

Abra seu navegador e acesse: [http://localhost:8000](http://localhost:8000)

### 🐳 Instalação com Docker

Para uma instalação ainda mais simples usando Docker:

```bash
# Clone e acesse o diretório
git clone <url-do-repositorio>
cd pet-app

# Configure o arquivo .env conforme instruções acima

# Execute com Docker Compose
docker-compose up -d

# A aplicação estará disponível em http://localhost:8000
```

### 🔍 Verificação da Instalação

1. **Teste da aplicação**: Acesse `http://localhost:8000`
2. **Teste de autenticação**: Clique em "Login" e faça login via Auth0
3. **Teste do banco**: Vá para o dashboard e tente cadastrar um pet
4. **Teste de upload**: Adicione uma foto a um pet

### ⚠️ Solução de Problemas Comuns

**Erro de conexão com MongoDB:**
```bash
# Verifique se o MongoDB está rodando
sudo systemctl status mongodb  # Linux
brew services list | grep mongodb  # macOS

# Teste a conexão
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('Conexão OK')"
```

**Erro de autenticação Auth0:**
- Verifique se as URLs de callback estão corretas
- Confirme se o CLIENT_SECRET está correto
- Verifique se todos os escopos estão configurados

**Erro de dependências:**
```bash
# Limpe o cache e reinstale
uv cache clean
uv sync --refresh
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

## API Endpoints

### Pets
- `GET /pets/form` - Formulário de cadastro
- `POST /pets` - Criar/atualizar pet (com foto)
- `GET /pets/{id}/edit` - Formulário de edição
- `GET /pets/{id}/profile` - Perfil do pet
- `POST /pets/{id}/delete` - Excluir pet

### Autenticação
- `GET /login` - Login via Auth0
- `GET /callback` - Callback do Auth0
- `GET /logout` - Logout
- `GET /dashboard` - Dashboard principal

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
├── 📄 docker-compose.yml               # Orquestração de containers
├── 📄 dockerfile                       # Imagem Docker da aplicação
├── 📄 create_vermifugos_collection.py  # Script para popular dados de vermífugos
├── 📄 README.md                        # Documentação do projeto
├── 📄 uv.lock                          # Lock file de dependências (UV)
├── 📁 templates/                       # Templates HTML (Jinja2)
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
├── 📁 static/                          # Arquivos estáticos
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

## Segurança

- Validação de tipos de arquivo
- Limite de tamanho de upload
- Autenticação obrigatória para todas as rotas
- Sanitização de nomes de arquivo
- Armazenamento isolado por usuário

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT.
