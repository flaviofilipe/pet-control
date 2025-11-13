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
mongo            7         a8b9c0d1e2f3   3 weeks ago     695MB
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
  -t pet-control:v1.0.0 \
  .
```

**Flags explicadas:**
- `--build-arg ENV=production`: Define o ambiente como produção
- `--no-cache`: Força rebuild completo (recomendado para produção)
- `-t pet-control:latest`: Tag "latest" para referência rápida
- `-t pet-control:v1.0.0`: Tag versionada para controle

**⚙️ Tecnologias em Produção:**
- **Gunicorn**: Gerenciador de processos robusto
- **Uvicorn Workers**: 4 workers assíncronos para alta performance
- **Graceful Shutdown**: Encerramento seguro de requisições em andamento
- **Health Checks**: Monitoramento automático da aplicação

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

**Exemplo prático:**

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com
```

### Passo 3.3: Taguear a Imagem para o ECR

```bash
# Tag para o ECR
docker tag pet-control:latest \
  [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest

docker tag pet-control:v1.0.0 \
  [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:v1.0.0
```

**Exemplo prático:**

```bash
docker tag pet-control:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/pet-control:latest

docker tag pet-control:v1.0.0 \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/pet-control:v1.0.0
```

### Passo 3.4: Fazer Push para o ECR

```bash
# Push das imagens
docker push [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest
docker push [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:v1.0.0
```

**Exemplo prático:**

```bash
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/pet-control:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/pet-control:v1.0.0
```

✅ **Após este passo, sua imagem está no ECR!**

---

## 🛡️ 4. Configuração do IAM Role

Para que o EC2 possa fazer pull de imagens do ECR sem expor credenciais, configure um IAM Role.

### Passo 4.1: Criar Política IAM

1. Acesse o console **IAM** → **Policies** → **Create policy**
2. Selecione a aba **JSON**
3. Cole a política abaixo:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowECRPull",
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:DescribeRepositories",
                "ecr:ListImages"
            ],
            "Resource": "*"
        }
    ]
}
```

4. Clique em **Next: Tags** → **Next: Review**
5. Nome da política: **`ECR-PetControl-ReadOnly-Policy`**
6. Clique em **Create policy**

### Passo 4.2: Criar IAM Role

1. Acesse **IAM** → **Roles** → **Create role**
2. **Trusted entity type**: **AWS service**
3. **Use case**: **EC2**
4. Clique em **Next**
5. Anexe as políticas:
   - ✅ **`ECR-PetControl-ReadOnly-Policy`** (criada acima)
   - ✅ **`AmazonSSMManagedInstanceCore`** (opcional, para gerenciamento remoto)
6. Clique em **Next**
7. Nome do role: **`EC2-PetControl-Role`**
8. Clique em **Create role**

### Passo 4.3: Anexar Role à Instância EC2

#### Se a instância já existe:
1. Console **EC2** → **Instances**
2. Selecione sua instância
3. **Actions** → **Security** → **Modify IAM role**
4. Selecione: **`EC2-PetControl-Role`**
5. Clique em **Save**

#### Se for criar uma nova instância:
1. Durante o lançamento, em **Advanced details**
2. **IAM instance profile**: Selecione **`EC2-PetControl-Role`**

---

## ⬇️ 5. Deploy no EC2

### Passo 5.1: Conectar ao EC2

```bash
ssh -i sua-chave.pem ec2-user@seu-ec2-ip
```

### Passo 5.2: Instalar Docker (se necessário)

```bash
# Atualizar sistema
sudo yum update -y

# Instalar Docker
sudo yum install docker -y

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Adicionar usuário ao grupo docker (evita usar sudo)
sudo usermod -aG docker $USER

# Aplicar mudança de grupo (ou faça logout/login)
newgrp docker

# Verificar instalação
docker --version
```

### Passo 5.3: Instalar AWS CLI (se necessário)

```bash
# Instalar AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verificar instalação
aws --version

# Limpar arquivos de instalação
rm -rf aws awscliv2.zip
```

### Passo 5.4: Autenticar no ECR

```bash
# Autenticar Docker no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com
```

**Exemplo:**

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com
```

### Passo 5.5: Fazer Pull da Imagem

```bash
# Pull da imagem do ECR
docker pull [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest
```

**Exemplo:**

```bash
docker pull 123456789012.dkr.ecr.us-east-1.amazonaws.com/pet-control:latest
```

### Passo 5.6: Criar Arquivo de Variáveis de Ambiente

Crie o arquivo `.env-pet-control` com todas as variáveis de ambiente necessárias:

```bash
# Criar arquivo .env-pet-control
nano ~/.env-pet-control
```

**Conteúdo do arquivo `.env-pet-control`:**

```bash
# =============================================================================
# Pet Control - Production Environment Variables
# =============================================================================

# Environment Configuration
ENV=production
LOG_LEVEL=INFO

# Auth0 Configuration (REQUIRED)
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_API_AUDIENCE=your-api-audience
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_CALLBACK_URI=https://yourdomain.com/callback

# Database Configuration (REQUIRED)
# Para MongoDB Atlas
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
# Para MongoDB local/Docker
# MONGO_URI=mongodb://username:password@mongodb:27017/
DB_NAME=pet_control

# Collection Names (Optional - defaults provided)
COLLECTION_NAME=profiles
PETS_COLLECTION_NAME=pets
VACCINES_COLLECTION_NAME=vacinas
ECTOPARASITES_COLLECTION_NAME=ectoparasitas
VERMIFUGOS_COLLECTION_NAME=vermifugos

# Session Security (REQUIRED)
# Generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SESSION_SECRET_KEY=your-super-secure-session-secret-key-here

# Email Notifications (OPTIONAL - only if using notifications)
GMAIL_EMAIL=your-notifications@gmail.com
GMAIL_PASSWORD=your-gmail-app-password
GMAIL_SMTP_SERVER=smtp.gmail.com
GMAIL_SMTP_PORT=587
```

**Salvar e sair:** `Ctrl+O` → `Enter` → `Ctrl+X`

**⚠️ IMPORTANTE:** Proteja o arquivo de variáveis sensíveis:

```bash
chmod 600 ~/.env-pet-control
```

### Passo 5.7: Parar Container Antigo (se existir)

```bash
# Verificar containers em execução
docker ps -a | grep pet-control

# Parar e remover container antigo
docker stop pet-control 2>/dev/null || true
docker rm pet-control 2>/dev/null || true
```

### Passo 5.8: Executar o Container

```bash
# Executar container com arquivo .env
docker run -d \
  --name pet-control \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file ~/.env-pet-control \
  [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest
```

**Exemplo completo:**

```bash
docker run -d \
  --name pet-control \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file ~/.env-pet-control \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/pet-control:latest
```

**Flags explicadas:**
- `-d`: Executa em background (daemon)
- `--name pet-control`: Nome do container
- `--restart unless-stopped`: Reinicia automaticamente (exceto se parado manualmente)
- `-p 8000:8000`: Mapeia porta 8000 do container para 8000 do host
- `--env-file`: Carrega variáveis de ambiente do arquivo

### Passo 5.9: Verificar Status do Container

```bash
# Ver logs do container
docker logs pet-control

# Ver logs em tempo real
docker logs -f pet-control

# Verificar status
docker ps | grep pet-control

# Verificar health check
curl http://localhost:8000/health
```

**Saída esperada do health check:**

```json
{
  "status": "healthy",
  "service": "pet-control-api",
  "timestamp": "2025-11-10T12:00:00.000000",
  "version": "1.0.0",
  "database": "connected"
}
```

---

## 🌐 6. Configuração do NGINX

A aplicação roda na **porta 8000** internamente. O NGINX atuará como **proxy reverso** para:
- Permitir múltiplas aplicações no mesmo servidor
- Fornecer HTTPS/SSL
- Balanceamento de carga (se necessário)

### Passo 6.1: Instalar NGINX (se necessário)

```bash
# Amazon Linux 2
sudo amazon-linux-extras install nginx1 -y

# Ubuntu/Debian
sudo apt update && sudo apt install nginx -y

# Iniciar e habilitar NGINX
sudo systemctl start nginx
sudo systemctl enable nginx

# Verificar status
sudo systemctl status nginx
```

### Passo 6.2: Configurar Site para Pet Control

Crie um arquivo de configuração para a aplicação:

```bash
# Criar arquivo de configuração
sudo nano /etc/nginx/conf.d/pet-control.conf
```

**Conteúdo para HTTP (básico):**

```nginx
# Pet Control API - HTTP Configuration
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Logs
    access_log /var/log/nginx/pet-control-access.log;
    error_log /var/log/nginx/pet-control-error.log;

    # Client upload size limit
    client_max_body_size 10M;

    # Proxy para a aplicação FastAPI (porta 8000)
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        
        # Headers essenciais
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (se necessário no futuro)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (sem logs desnecessários)
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    # Static files (uploads)
    location /uploads/ {
        proxy_pass http://localhost:8000/uploads/;
    }
}
```

**Conteúdo para HTTPS (recomendado para produção):**

```nginx
# Pet Control API - HTTPS Configuration
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirecionar HTTP para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # Certificados SSL (use Certbot para Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Configurações SSL recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # SSL session cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Logs
    access_log /var/log/nginx/pet-control-access.log;
    error_log /var/log/nginx/pet-control-error.log;

    # Client upload size limit
    client_max_body_size 10M;

    # Proxy para a aplicação FastAPI (porta 8000)
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        
        # Headers essenciais
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    # Static files
    location /uploads/ {
        proxy_pass http://localhost:8000/uploads/;
    }
}
```

### Passo 6.3: Configurar SSL com Let's Encrypt (Recomendado)

```bash
# Instalar Certbot
sudo yum install certbot python3-certbot-nginx -y
# ou no Ubuntu/Debian:
# sudo apt install certbot python3-certbot-nginx -y

# Obter certificado SSL (certbot configura NGINX automaticamente)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Renovação automática (certbot já configura cron automaticamente)
sudo certbot renew --dry-run
```

### Passo 6.4: Testar e Aplicar Configuração

```bash
# Testar configuração do NGINX
sudo nginx -t

# Se o teste passar, recarregar NGINX
sudo systemctl reload nginx

# Verificar status
sudo systemctl status nginx
```

### Passo 6.5: Configurar Firewall (se necessário)

```bash
# Se usando firewalld (Amazon Linux 2)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Se usando ufw (Ubuntu)
sudo ufw allow 'Nginx Full'
sudo ufw reload
```

### Passo 6.6: Testar Acesso

```bash
# Testar localmente
curl http://yourdomain.com/health

# Testar HTTPS (se configurado)
curl https://yourdomain.com/health
```

---

## 📊 7. Monitoramento e Manutenção

### Monitorar Logs

```bash
# Logs do container em tempo real
docker logs -f pet-control

# Logs do NGINX
sudo tail -f /var/log/nginx/pet-control-access.log
sudo tail -f /var/log/nginx/pet-control-error.log

# Logs de erro do sistema
sudo journalctl -u docker -f
```

### Verificar Recursos do Container

```bash
# Uso de recursos
docker stats pet-control

# Informações detalhadas
docker inspect pet-control
```

### Backup do Container

```bash
# Criar imagem do container em execução
docker commit pet-control pet-control-backup:$(date +%Y%m%d)

# Exportar imagem
docker save pet-control-backup:$(date +%Y%m%d) | gzip > pet-control-backup-$(date +%Y%m%d).tar.gz
```

### Atualizar a Aplicação

```bash
# 1. Pull da nova versão
docker pull [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest

# 2. Parar container antigo
docker stop pet-control

# 3. Remover container antigo (imagem e dados persistem)
docker rm pet-control

# 4. Iniciar novo container
docker run -d \
  --name pet-control \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file ~/.env-pet-control \
  [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com/pet-control:latest

# 5. Verificar logs
docker logs -f pet-control
```

### Reiniciar Aplicação

```bash
# Reinício rápido
docker restart pet-control

# Reinício completo (para mudanças no .env)
docker stop pet-control && docker start pet-control
```

---

## ⏰ 8. Tarefas Automatizadas (Cron)

A aplicação possui tarefas automatizadas para notificações:
- **daily_check.py**: Notificações diárias de tratamentos do dia seguinte
- **monthly_check.py**: Relatórios mensais de tratamentos

### Passo 8.1: Configurar Cron Jobs

```bash
# Editar crontab
crontab -e
```

**Adicionar as seguintes linhas:**

```cron
# Pet Control - Notificação Diária (todos os dias às 18h)
0 18 * * * docker exec pet-control uv run python daily_check.py >> /var/log/pet-control-daily.log 2>&1

# Pet Control - Relatório Mensal (dia 1 de cada mês às 8h)
0 8 1 * * docker exec pet-control uv run python monthly_check.py >> /var/log/pet-control-monthly.log 2>&1

# Pet Control - Health Check (a cada 5 minutos)
*/5 * * * * curl -f http://localhost:8000/health > /dev/null 2>&1 || echo "Pet Control API is down!" | mail -s "Pet Control Alert" admin@yourdomain.com
```

### Passo 8.2: Criar Arquivos de Log

```bash
# Criar arquivos de log
sudo touch /var/log/pet-control-daily.log
sudo touch /var/log/pet-control-monthly.log

# Permissões
sudo chown $USER:$USER /var/log/pet-control-*.log
sudo chmod 644 /var/log/pet-control-*.log
```

### Passo 8.3: Testar Tarefas Manualmente

```bash
# Testar notificação diária (modo dry-run)
docker exec pet-control uv run python daily_check.py --dry-run --verbose

# Testar relatório mensal (modo dry-run)
docker exec pet-control uv run python monthly_check.py --dry-run --verbose

# Executar envio real
docker exec pet-control uv run python daily_check.py
docker exec pet-control uv run python monthly_check.py
```

### Passo 8.4: Verificar Logs das Tarefas

```bash
# Ver logs das tarefas
tail -f /var/log/pet-control-daily.log
tail -f /var/log/pet-control-monthly.log

# Ver logs do cron
sudo grep CRON /var/log/syslog  # Ubuntu/Debian
sudo journalctl -u crond         # Amazon Linux/CentOS
```

---

## 🔒 Checklist Final de Segurança

Antes de colocar em produção, verifique:

- [ ] ✅ Variáveis de ambiente configuradas corretamente (`.env-pet-control`)
- [ ] ✅ `SESSION_SECRET_KEY` é uma chave forte e única
- [ ] ✅ Auth0 configurado com domínio de produção
- [ ] ✅ MongoDB com autenticação habilitada
- [ ] ✅ HTTPS configurado com certificado válido
- [ ] ✅ Firewall configurado (apenas portas 80, 443 e SSH abertas)
- [ ] ✅ Container com `--restart unless-stopped`
- [ ] ✅ Logs sendo monitorados
- [ ] ✅ Backups automatizados configurados
- [ ] ✅ IAM Role configurado (sem credenciais expostas)
- [ ] ✅ Security Groups do EC2 configurados corretamente
- [ ] ✅ Permissões do arquivo `.env-pet-control` (600)

---

## 🆘 Troubleshooting

### Erro: "No such option: --worker-class"

**Causa**: Versão antiga da imagem sem Gunicorn ou build incorreto.

**Solução**:
```bash
# 1. Fazer pull da versão corrigida
docker pull [ID_DA_CONTA].dkr.ecr.[REGIAO].amazonaws.com/pet-control:latest

# 2. Parar e remover container antigo
docker stop pet-control && docker rm pet-control

# 3. Executar nova versão
docker run -d \
  --name pet-control \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file ~/.env-pet-control \
  [ID_DA_CONTA].dkr.ecr.[REGIAO].amazonaws.com/pet-control:latest

# 4. Verificar logs
docker logs -f pet-control
```

**Mensagem esperada nos logs:**
```
🚀 Starting in PRODUCTION mode with Gunicorn + 4 Uvicorn workers...
```

### Container não inicia

```bash
# Ver logs detalhados
docker logs pet-control

# Verificar variáveis de ambiente
docker exec pet-control env | grep -E "AUTH0|MONGO|SESSION"

# Testar conexão com MongoDB
docker exec pet-control uv run python -c "from app.database import Database; db = Database(); db.connect(); print('MongoDB OK')"
```

### NGINX não responde

```bash
# Verificar status
sudo systemctl status nginx

# Testar configuração
sudo nginx -t

# Ver logs de erro
sudo tail -f /var/log/nginx/error.log
```

### Erros de autenticação ECR

```bash
# Re-autenticar
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  [ID_DA_CONTA].dkr.ecr.us-east-1.amazonaws.com

# Verificar IAM Role
aws sts get-caller-identity
```

### Health check falha

```bash
# Verificar se a aplicação está respondendo
curl -v http://localhost:8000/health

# Verificar se o MongoDB está acessível
docker exec pet-control uv run python -c "from app.database import Database; Database().connect()"
```

---

## 📚 Recursos Adicionais

- **Documentação da API**: https://yourdomain.com/docs
- **AWS ECR Documentation**: https://docs.aws.amazon.com/ecr/
- **NGINX Documentation**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/
- **Auth0 Documentation**: https://auth0.com/docs

---

## 📝 Notas Importantes

1. **Porta da Aplicação**: A aplicação sempre roda na porta **8000** dentro do container
2. **NGINX**: Atua como proxy reverso, permitindo múltiplas aplicações no mesmo servidor
3. **Variáveis de Ambiente**: Sempre use arquivo `.env-pet-control` separado no EC2
4. **Atualizações**: Use tags versionadas (`v1.0.0`, `v1.0.1`) para controle de versões
5. **Backups**: Configure backups automáticos do MongoDB regularmente
6. **Monitoramento**: Configure alertas para quando a aplicação ficar indisponível

---

**🎉 Deploy Concluído!**

Sua aplicação Pet Control está agora rodando em produção de forma segura e escalável!
