# Pet App - Sistema de Gerenciamento de Pets

Sistema completo para gerenciamento de pets com autenticação Auth0, banco de dados MongoDB e funcionalidade de upload de fotos.

## Funcionalidades

- ✅ Autenticação segura com Auth0
- ✅ Cadastro e gerenciamento de pets
- ✅ Upload de fotos com validação e crop
- ✅ Suporte a múltiplos formatos (JPG, PNG, GIF, WebP, HEIC)
- ✅ Criação automática de miniaturas
- ✅ Interface de crop intuitiva
- ✅ Dashboard responsivo com fotos
- ✅ Perfis de usuário
- ✅ Histórico de tratamentos

## Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd pet-app
```

### 2. Crie um ambiente virtual
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

### 3. Instale as dependências
```bash
# Usando UV (recomendado)
uv sync

# Para suporte a HEIC (opcional)
uv add pillow-heif

# Ou usando pip
pip install -r requirements.txt
pip install pillow-heif
```

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
# Auth0 Configuration
AUTH0_DOMAIN=seu-dominio.auth0.com
AUTH0_API_AUDIENCE=seu-audience
AUTH0_CLIENT_ID=seu-client-id
AUTH0_CLIENT_SECRET=seu-client-secret
AUTH0_CALLBACK_URI=http://localhost:8000/callback

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/

# Session Configuration
SESSION_SECRET_KEY=sua-chave-secreta-super-segura
```

### 5. Execute o servidor
```bash
# Usando UV (recomendado)
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Ou ative o ambiente virtual primeiro
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Teste o suporte a HEIC
```bash
# Execute o script de teste
uv run python test_heic.py

# Ou teste manualmente
uv run python -c "from main import HEIC_SUPPORT; print(f'HEIC suportado: {HEIC_SUPPORT}')"
```

## Funcionalidade de Upload de Fotos

### Características de Segurança
- ✅ Validação de tipos de arquivo (JPG, PNG, GIF, WebP, HEIC)
- ✅ Limite de tamanho (10MB máximo)
- ✅ Criação automática de miniaturas
- ✅ Interface de crop intuitiva
- ✅ Armazenamento seguro em diretórios separados por pet
- ✅ Limpeza automática de arquivos antigos
- ✅ Suporte nativo a HEIC com pillow-heif
- ✅ Fallback para conversão quando necessário

### Como Usar
1. **Cadastro de Pet**: Acesse `/pets/form` e selecione uma foto
2. **Crop da Imagem**: Use a interface de crop para ajustar a foto antes do upload
3. **Edição de Pet**: Acesse `/pets/{id}/edit` para atualizar a foto
4. **Visualização**: As fotos aparecem no dashboard e perfil do pet
5. **Formatos Suportados**: JPG, PNG, GIF, WebP e HEIC (convertido automaticamente)

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

## Tecnologias Utilizadas

- **Backend**: FastAPI
- **Autenticação**: Auth0
- **Banco de Dados**: MongoDB
- **Processamento de Imagens**: Pillow (PIL)
- **Frontend**: HTML + Tailwind CSS + JavaScript
- **Upload de Arquivos**: FastAPI UploadFile

## Suporte a HEIC

### Instalação
Para suporte completo a arquivos HEIC, instale a dependência adicional:

```bash
# Usando UV
uv add pillow-heif

# Ou usando pip
pip install pillow-heif
```

### Funcionamento
- **Com pillow-heif**: Suporte nativo completo a HEIC/HEIF
- **Sem pillow-heif**: Fallback para conversão automática
- **Conversão**: HEIC é convertido para JPEG de alta qualidade
- **Validação**: Verificação automática de suporte disponível

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
