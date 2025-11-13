# 🗄️ MongoDB Custom Image - Pet Control System

Imagem Docker customizada do MongoDB com scripts de inicialização, configurações otimizadas e dados de exemplo.

## 📋 Estrutura de Arquivos

```
mongodb/
├── init/                           # Scripts de inicialização
│   ├── 01-init-db.js              # Cria banco, usuários e coleções
│   ├── 02-create-indexes.js       # Cria índices otimizados
│   ├── 03-seed-data.js            # Insere dados de exemplo
│   └── 04-seed-info-data.js       # Insere dados informativos (vacinas, etc)
├── config/
│   └── mongod.conf                # Configuração customizada do MongoDB
├── scripts/                       # Scripts utilitários
│   ├── backup.sh                  # Script de backup
│   ├── restore.sh                 # Script de restore
│   └── health-check.sh            # Health check
└── README.md                      # Este arquivo
```

## 🚀 Como Usar

### Build da Imagem

```bash
# Build simples
docker build -f Dockerfile.mongodb -t pet-control-mongodb:latest .

# Build com tag versionada
docker build -f Dockerfile.mongodb -t pet-control-mongodb:1.0.0 .
```

### Executar Container

```bash
# Básico (sem autenticação)
docker run -d \
  --name pet-mongodb \
  -p 27017:27017 \
  pet-control-mongodb:latest

# Com autenticação (recomendado)
docker run -d \
  --name pet-mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=senha_segura \
  -e MONGO_APP_PASSWORD=senha_app_segura \
  -v pet-mongodb-data:/data/db \
  -v pet-mongodb-backup:/backup \
  pet-control-mongodb:latest

# Com autenticação habilitada (produção)
docker run -d \
  --name pet-mongodb \
  -p 127.0.0.1:27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=senha_segura \
  -e MONGO_APP_PASSWORD=senha_app_segura \
  -v pet-mongodb-data:/data/db \
  -v pet-mongodb-backup:/backup \
  pet-control-mongodb:latest \
  mongod --auth
```

## 📊 Scripts de Inicialização

### 01-init-db.js

Executado automaticamente na primeira inicialização:

- ✅ Cria usuário root (se credenciais fornecidas)
- ✅ Cria usuário da aplicação (`pet_control_user`)
- ✅ Cria banco `pet_control`
- ✅ Cria coleções com validações JSON Schema:
  - `profiles` (tutores/usuários)
  - `pets` (animais de estimação)
  - `vacinas` (informações sobre vacinas)
  - `ectoparasitas` (controle de ectoparasitas)
  - `vermifugos` (vermifugação)

### 02-create-indexes.js

Cria índices otimizados para:

- ✅ Busca rápida por email (profiles)
- ✅ Busca por tutores (pets)
- ✅ Filtros de soft delete
- ✅ Busca de tratamentos por data
- ✅ Busca textual (full-text search)
- ✅ Índices compostos para queries complexas

### 03-seed-data.js

Insere dados de exemplo:

- ✅ 3 perfis de tutores
- ✅ 3 pets com tratamentos de exemplo

### 04-seed-info-data.js

Insere dados informativos completos:

- ✅ **8 vacinas** com informações detalhadas:
  - Cronograma vacinal (filhote e adulto)
  - Efeitos colaterais
  - Doenças que protege
  - Espécie alvo (cães e gatos)
  - Indicação de obrigatoriedade legal
- ✅ **4 ectoparasitas** (pulgas, carrapatos, sarnas, piolhos)
- ✅ **5 parasitas internos** (vermífugos)

## 🛠️ Scripts Utilitários

### Backup

```bash
# Backup com timestamp automático
docker exec pet-mongodb backup-mongo

# Backup com nome customizado
docker exec pet-mongodb backup-mongo meu-backup-importante

# Copiar backup para host
docker cp pet-mongodb:/backup/backup_20251110_120000 ./backups/
```

### Restore

```bash
# Copiar backup do host para container
docker cp ./backups/backup_20251110_120000 pet-mongodb:/backup/

# Restaurar backup
docker exec pet-mongodb restore-mongo /backup/backup_20251110_120000
```

### Health Check

```bash
# Verificar saúde manualmente
docker exec pet-mongodb health-check
echo $?  # 0 = saudável, 1 = problema
```

## 🔐 Segurança

### Credenciais Padrão

**⚠️ IMPORTANTE: Altere em produção!**

- **Usuário da aplicação:** `pet_control_user`
- **Senha padrão:** `pet_control_password_change_me`

### Habilitar Autenticação

Para produção, sempre use autenticação:

```bash
docker run -d \
  --name pet-mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=sua_senha_super_segura \
  pet-control-mongodb:latest \
  mongod --auth
```

### String de Conexão

```bash
# Desenvolvimento (sem autenticação)
mongodb://localhost:27017/pet_control

# Produção (com autenticação)
mongodb://pet_control_user:senha@localhost:27017/pet_control?authSource=pet_control
```

## 📈 Monitoramento

### Ver Logs

```bash
docker logs pet-mongodb
docker logs -f pet-mongodb  # Tempo real
```

### Estatísticas

```bash
# Conectar ao MongoDB
docker exec -it pet-mongodb mongosh pet_control

# No shell do MongoDB
db.stats()
db.pets.stats()
db.pets.getIndexes()
```

### Uso de Recursos

```bash
docker stats pet-mongodb
```

## 🧪 Testes

### Verificar Inicialização

```bash
# Verificar coleções criadas
docker exec -it pet-mongodb mongosh pet_control --eval "db.getCollectionNames()"

# Verificar índices
docker exec -it pet-mongodb mongosh pet_control --eval "db.pets.getIndexes()"

# Contar documentos
docker exec -it pet-mongodb mongosh pet_control --eval "
    print('Profiles: ' + db.profiles.countDocuments());
    print('Pets: ' + db.pets.countDocuments());
    print('Vaccines: ' + db.vaccines.countDocuments());
"
```

### Verificar Health Check

```bash
docker inspect --format='{{.State.Health.Status}}' pet-mongodb
```

## 🔧 Configuração

### mongod.conf

Configurações customizadas:

- ✅ Cache: 1GB
- ✅ Compressão: snappy
- ✅ Logs rotativos
- ✅ Slow query profiling (>100ms)
- ✅ Conexões máximas: 1000

## 📦 Volumes

- `/data/db` - Dados do MongoDB
- `/backup` - Backups
- `/var/log/mongodb` - Logs

## 🐳 Docker Compose

```yaml
version: '3.8'
services:
  mongodb:
    build:
      context: .
      dockerfile: Dockerfile.mongodb
    container_name: pet-mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: senha_segura
      MONGO_INITDB_DATABASE: pet_control
      MONGO_APP_PASSWORD: senha_app_segura
    ports:
      - "27017:27017"
    volumes:
      - pet-mongodb-data:/data/db
      - pet-mongodb-backup:/backup
    restart: unless-stopped

volumes:
  pet-mongodb-data:
  pet-mongodb-backup:
```

## 📚 Comandos Úteis

```bash
# Acessar shell do MongoDB
docker exec -it pet-mongodb mongosh pet_control

# Acessar bash do container
docker exec -it pet-mongodb bash

# Ver tamanho do banco
docker exec pet-mongodb mongosh pet_control --eval "db.stats().dataSize"

# Exportar coleção específica
docker exec pet-mongodb mongoexport --db=pet_control --collection=pets --out=/backup/pets.json

# Importar coleção
docker exec pet-mongodb mongoimport --db=pet_control --collection=pets --file=/backup/pets.json
```

## 🆘 Troubleshooting

### Container não inicia

```bash
# Ver logs
docker logs pet-mongodb

# Verificar permissões
docker exec pet-mongodb ls -la /data/db
```

### Problemas de conexão

```bash
# Verificar se está rodando
docker ps | grep pet-mongodb

# Verificar porta
docker port pet-mongodb

# Testar conexão
docker exec pet-mongodb mongosh --eval "db.adminCommand('ping')"
```

### Resetar completamente

```bash
# ⚠️ CUIDADO: Remove todos os dados!
docker stop pet-mongodb
docker rm pet-mongodb
docker volume rm pet-mongodb-data pet-mongodb-backup

# Recriar
docker run -d --name pet-mongodb pet-control-mongodb:latest
```

## 📖 Documentação Adicional

- [MongoDB Official Documentation](https://docs.mongodb.com/)
- [MongoDB Docker Hub](https://hub.docker.com/_/mongo)
- [MongoDB Configuration Reference](https://docs.mongodb.com/manual/reference/configuration-options/)

---

**Versão:** 1.0.0  
**Última atualização:** 2025-11-13

