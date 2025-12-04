# 🚀 Guia Completo de Deploy - Pet Control API

Este guia fornece um passo a passo detalhado para fazer o deploy da aplicação **Pet Control** em produção usando AWS ECR e EC2.

---

## 📋 Índice

1. [Preparação Local](#-1-preparação-local)
2. [Build da Imagem para Produção](#-2-build-da-imagem-para-produção)
3. [Envio para AWS ECR](#-3-envio-para-aws-ecr)
4. [Configuração do IAM Role](#-4-configuração-do-iam-role)
5. [Deploy no EC2](#-5-deploy-no-ec2)
6. [Configuração do NGINX](#-6-configuração-do-nginx)
7. [Monitoramento e Manutenção](#-7-monitoramento-e-manutenção)
8. [Tarefas Automatizadas (Cron)](#-8-tarefas-automatizadas-cron)

---

## 🛠️ 1. Preparação Local

### Passo 1.1: Verificar Pré-requisitos

Certifique-se de ter instalado localmente:

- **Docker** (versão 20.10+)
- **AWS CLI** (versão 2.x)
- **Git** (para controle de versão)

```bash
# Verificar versões
docker --version
aws --version
git --version
```

### Passo 1.2: Listar Imagens Docker Locais

Para visualizar as imagens já construídas:

```bash
docker images
```

**Saída Exemplo:**

```
REPOSITORY       TAG       IMAGE ID       CREATED         SIZE
pet-control      dev       d1a2b3c4d5e6   2 minutes ago   250MB
postgres         15        a8b9c0d1e2f3   3 weeks ago     380MB
```

---

## 🏗️ 2. Build da Imagem para Produção

### Passo 2.1: Build da Imagem de Produção

A aplicação usa um **Dockerfile inteligente** que detecta o ambiente. Para produção:

```bash
# Build da imagem de produção
docker build \
  --build-arg ENV=production \
  --no-cache \
  -t pet-control:latest \
  -t pet-control:v2.0.0 \
  .
```

**Flags explicadas:**
- `--build-arg ENV=production`: Define o ambiente como produção
- `--no-cache`: Força rebuild completo (recomendado para produção)
- `-t pet-control:latest`: Tag "latest" para referência rápida
- `-t pet-control:v2.0.0`: Tag versionada para controle

**⚙️ Tecnologias em Produção:**
- **Gunicorn**: Gerenciador de processos robusto
- **Uvicorn Workers**: 4 workers assíncronos para alta performance
- **PostgreSQL**: Banco de dados relacional
- **SQLAlchemy 2.0**: ORM assíncrono
- **Alembic**: Migrations de banco de dados

### Passo 2.2: Testar a Imagem Localmente (Opcional)

Antes de fazer deploy, teste a imagem localmente:

```bash
# Criar arquivo .env temporário para teste
cp env.example .env
# Edite o .env com suas credenciais de teste

# Executar container de teste
docker run -d \
  --name pet-control-test \
  -p 8000:8000 \
  --env-file .env \
  pet-control:latest

# Testar health check
curl http://localhost:8000/health

# Remover container de teste
docker stop pet-control-test && docker rm pet-control-test
```

---

## 🚢 3. Envio para AWS ECR

### Passo 3.1: Criar Repositório no ECR (Primeira Vez)

No console da AWS ou via CLI:

```bash
# Criar repositório ECR
aws ecr create-repository \
  --repository-name pet-control \
  --region us-east-1 \
  --image-scanning-configuration scanOnPush=true
```

### Passo 3.2: Autenticar no ECR

```bash
# Substitua pelos seus valores:
# us-east-1: ex: us-east-1, sa-east-1
# [ID_DA_CONTA]: seu ID da conta AWS (12 dígitos)

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com
```

### Passo 3.3: Taguear e Fazer Push

```bash
# Tag para o ECR
docker tag pet-control:latest \
  [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest

# Push das imagens
docker push [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest
```

---

## ⬇️ 5. Deploy no EC2

### Passo 5.1: Configuração do PostgreSQL

Para produção, recomendamos usar **Amazon RDS** para PostgreSQL:

```bash
# Criar instância RDS PostgreSQL via console AWS ou CLI
aws rds create-db-instance \
  --db-instance-identifier pet-control-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15 \
  --master-username pet_control_user \
  --master-user-password SUA_SENHA_SEGURA \
  --allocated-storage 20
```

### Passo 5.2: Criar Arquivo de Variáveis de Ambiente

```bash
nano ~/.env-pet-control
```

**Conteúdo do arquivo `.env-pet-control`:**

```bash
# =============================================================================
# Pet Control - Production Environment Variables
# =============================================================================

# Environment Configuration
ENVIRONMENT=production

# PostgreSQL Database Configuration (REQUIRED)
DATABASE_URL=postgresql+asyncpg://pet_control_user:SUA_SENHA@seu-rds-endpoint:5432/pet_control
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Auth0 Configuration (REQUIRED)
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_API_AUDIENCE=your-api-audience
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_CALLBACK_URI=https://yourdomain.com/callback

# Session Security (REQUIRED)
SESSION_SECRET_KEY=your-super-secure-session-secret-key-here
FRONTEND_URL=https://yourdomain.com

# Email Notifications (OPTIONAL)
GMAIL_EMAIL=your-notifications@gmail.com
GMAIL_PASSWORD=your-gmail-app-password
GMAIL_SMTP_SERVER=smtp.gmail.com
GMAIL_SMTP_PORT=587

# Migrations
AUTO_RUN_MIGRATIONS=false
AUTO_RUN_SEEDS=false
```

### Passo 5.3: Executar o Container

```bash
# Pull da imagem
docker pull [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest

# Executar container
docker run -d \
  --name pet-control \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file ~/.env-pet-control \
  [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest
```

### Passo 5.4: Executar Migrations

```bash
# Executar migrations dentro do container
docker exec pet-control uv run alembic upgrade head

# Executar seeds (primeira vez apenas)
docker exec pet-control uv run python -m app.database.seeds.run_seeds
```

### Passo 5.5: Verificar Status

```bash
# Ver logs do container
docker logs pet-control

# Verificar health check
curl http://localhost:8000/health
```

**Saída esperada do health check:**

```json
{
  "status": "healthy",
  "service": "pet-control-api",
  "timestamp": "2025-12-03T12:00:00.000000",
  "version": "2.0.0",
  "database": "connected"
}
```

---

## 🌐 6. Configuração do NGINX

### Passo 6.1: Configuração Básica

```nginx
# /etc/nginx/conf.d/pet-control.conf
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

### Passo 6.2: Configurar SSL com Let's Encrypt

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 📊 7. Monitoramento e Manutenção

### Atualizar a Aplicação

```bash
# 1. Pull da nova versão
docker pull [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest

# 2. Parar container antigo
docker stop pet-control && docker rm pet-control

# 3. Iniciar novo container
docker run -d \
  --name pet-control \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file ~/.env-pet-control \
  [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest

# 4. Executar migrations (se necessário)
docker exec pet-control uv run alembic upgrade head
```

### Backup do Banco de Dados

```bash
# Backup via pg_dump
pg_dump -h seu-rds-endpoint -U pet_control_user -d pet_control > backup_$(date +%Y%m%d).sql

# Restore
psql -h seu-rds-endpoint -U pet_control_user -d pet_control < backup.sql
```

---

## ⏰ 8. Tarefas Automatizadas (Cron)

```cron
# Pet Control - Notificação Diária (todos os dias às 18h)
0 18 * * * docker exec pet-control uv run python daily_check.py >> /var/log/pet-control-daily.log 2>&1

# Pet Control - Relatório Mensal (dia 1 de cada mês às 8h)
0 8 1 * * docker exec pet-control uv run python monthly_check.py >> /var/log/pet-control-monthly.log 2>&1

# Pet Control - Health Check (a cada 5 minutos)
*/5 * * * * curl -f http://localhost:8000/health > /dev/null 2>&1 || echo "Pet Control API is down!"
```

---

## 🔒 Checklist Final de Segurança

- [ ] ✅ Variáveis de ambiente configuradas corretamente
- [ ] ✅ `SESSION_SECRET_KEY` é uma chave forte e única
- [ ] ✅ Auth0 configurado com domínio de produção
- [ ] ✅ PostgreSQL com autenticação habilitada
- [ ] ✅ HTTPS configurado com certificado válido
- [ ] ✅ Firewall configurado
- [ ] ✅ Container com `--restart unless-stopped`
- [ ] ✅ Logs sendo monitorados
- [ ] ✅ Backups automatizados configurados

---

**🎉 Deploy Concluído!**

Sua aplicação Pet Control está agora rodando em produção com PostgreSQL!
