# Sistema de Notificações - Pet Control

Este módulo implementa sistemas de notificações automáticas por email para lembrar os tutores sobre tratamentos de seus pets.

## 📋 Tasks Disponíveis

### 🗓️ **Notificação Diária** (`daily_check.py`)
Envia lembretes sobre tratamentos agendados para **amanhã**.

### 📊 **Relatório Mensal** (`monthly_check.py`)
Envia relatório completo sobre:
- Tratamentos agendados para o **mês atual**
- Tratamentos **expirados** que precisam de atenção

## 📋 Funcionalidades

- ✅ Busca tratamentos agendados para o dia seguinte
- ✅ Envia emails personalizados para cada tutor
- ✅ Template HTML responsivo e elegante
- ✅ Modo dry-run para testes sem envio real
- ✅ Logs detalhados de execução
- ✅ Suporte a múltiplos tutores por pet
- ✅ Tratamento de erros robusto

## 🚀 Como usar

### 🗓️ **Notificação Diária**

#### Execução básica (envia emails)
```bash
uv run python daily_check.py
```

#### Execução em modo teste (não envia emails)
```bash
uv run python daily_check.py --dry-run
```

#### Execução com logs detalhados
```bash
uv run python daily_check.py --verbose
```

#### Combinando opções
```bash
uv run python daily_check.py --dry-run --verbose
```

#### Execução direta do script principal
```bash
uv run python app/tasks/daily_check.py --dry-run --verbose
```

### 📊 **Relatório Mensal**

#### Execução básica (envia emails)
```bash
uv run python monthly_check.py
```

#### Execução em modo teste (não envia emails)
```bash
uv run python monthly_check.py --dry-run
```

#### Execução com logs detalhados
```bash
uv run python monthly_check.py --verbose
```

#### Combinando opções
```bash
uv run python monthly_check.py --dry-run --verbose
```

#### Execução direta do script principal
```bash
uv run python app/tasks/monthly_check.py --dry-run --verbose
```

## ⚙️ Configuração necessária no .env

Para que o sistema funcione, adicione as seguintes variáveis ao seu arquivo `.env`:

```env
# Gmail Configuration para notificações diárias
GMAIL_EMAIL=seu-email@gmail.com
GMAIL_PASSWORD=sua-senha-de-app-gmail
GMAIL_SMTP_SERVER=smtp.gmail.com
GMAIL_SMTP_PORT=587
```

### 🔑 Configurando o Gmail

1. **Ative a verificação em duas etapas** na sua conta Google
2. **Gere uma senha de app** específica:
   - Acesse: https://support.google.com/accounts/answer/185833
   - Selecione o app: "Email"
   - Selecione o dispositivo: "Outro (nome personalizado)"
   - Use a senha gerada no `GMAIL_PASSWORD`

## 📧 Templates de Email

### 🗓️ **Notificação Diária**
Template HTML responsivo: `app/services/templates/treatment_reminder.html`

O email inclui:
- 🐾 Nome e apelido do pet
- 📅 Data dos tratamentos (amanhã)
- 🏥 Lista detalhada de tratamentos
- ⏰ Horários e responsáveis
- 📞 Informações de contato

### 📊 **Relatório Mensal**
Template HTML responsivo: `app/services/templates/monthly_treatment_report.html`

O email inclui:
- 🐾 Nome e apelido do pet
- 📊 Resumo estatístico (agendados vs expirados)
- 📅 Tratamentos do mês atual
- ⚠️ Tratamentos expirados com dias de atraso
- 🎯 Alertas para tratamentos que precisam de atenção
- 📞 Informações de contato e próximos passos

## 🏗️ Arquitetura

### Componentes principais

1. **PetRepository** (`app/repositories/pet_repository.py`)
   - `get_tomorrow_scheduled_treatments()`: Busca tratamentos de amanhã
   - `get_scheduled_treatments_for_date()`: Busca tratamentos para data específica

2. **UserRepository** (`app/repositories/user_repository.py`)
   - `get_user_emails_by_ids()`: Busca emails dos tutores

3. **NotificationService** (`app/services/notification_service.py`)
   - `process_daily_notifications()`: Processa todas as notificações
   - `send_email_notification()`: Envia email individual
   - `format_treatments_for_email()`: Formata dados para template

4. **Task Principal** (`app/tasks/daily_check.py`)
   - Interface de linha de comando
   - Logging e relatórios
   - Tratamento de erros

### Fluxo de execução

1. 🔌 **Conecta ao banco de dados PostgreSQL**
2. 📊 **Busca tratamentos de amanhã** usando SQLAlchemy
3. 👥 **Busca dados dos tutores** com emails válidos
4. 📧 **Para cada pet com tratamentos:**
   - Formata dados para email
   - Renderiza template HTML
   - Envia email para cada tutor
5. 📈 **Gera relatório final** com estatísticas

## 📊 Exemplo de saída

```
🐾 PET CONTROL - VERIFICAÇÃO DIÁRIA DE TRATAMENTOS
==================================================
Início da execução: 08/11/2024 09:00:00
⚠️  MODO DRY-RUN ATIVADO - Emails não serão enviados

📋 DETALHES DOS TRATAMENTOS ENCONTRADOS:
--------------------------------------------------

1. Pet: Rex (Apelido: rex_1234)
   ID: 507f1f77bcf86cd799439011
   Tratamentos (2):
     1. Vacina Antirrábica - Vacina
        Horário: 14:00
     2. Vermífugo - Medicamento
        Horário: 14:30
   Tutores com email (1):
     - João Silva (joao@email.com)

============================================================
           RESUMO DA EXECUÇÃO - NOTIFICAÇÕES DIÁRIAS
============================================================
Status: ✅ SUCESSO
Modo: 🔍 DRY RUN (Simulação)
Total de pets com tratamentos: 1
Emails enviados/simulados: 1
Erros encontrados: 0
Data alvo: 09/11/2024

Mensagem: Processamento concluído: 1 emails enviados para 1 pets
============================================================
```

## 🔧 Automação

### 🗓️ **Automação da Notificação Diária**

#### Usando cron (Linux/macOS)
```bash
# Adicione estas linhas ao crontab (crontab -e)
# Executa todos os dias às 9:00
0 9 * * * cd /caminho/para/projeto && uv run python daily_check.py
```

#### Usando Task Scheduler (Windows)
1. Abra o Task Scheduler
2. Crie uma nova tarefa básica: "Pet Control - Diário"
3. Configure para executar diariamente
4. Programa: `uv`
5. Argumentos: `run python daily_check.py`
6. Inicie em: caminho do projeto

### 📊 **Automação do Relatório Mensal**

#### Usando cron (Linux/macOS)
```bash
# Adicione estas linhas ao crontab (crontab -e)
# Executa no primeiro dia de cada mês às 10:00
0 10 1 * * cd /caminho/para/projeto && uv run python monthly_check.py
```

#### Usando Task Scheduler (Windows)
1. Abra o Task Scheduler
2. Crie uma nova tarefa básica: "Pet Control - Mensal"
3. Configure para executar mensalmente (dia 1)
4. Programa: `uv`
5. Argumentos: `run python monthly_check.py`
6. Inicie em: caminho do projeto

### 💡 **Sugestões de Automação**
- **Diária**: Execute às 9:00 da manhã para lembrar tratamentos do dia seguinte
- **Mensal**: Execute no primeiro dia útil do mês às 10:00
- **Teste**: Execute primeiro em modo `--dry-run` para validar configurações
- **Logs**: Redirecione saída para arquivos de log para monitoramento

## 🧪 Testes

### 🗓️ **Teste da Notificação Diária**

1. **Teste básico (dry-run):**
   ```bash
   uv run python daily_check.py --dry-run --verbose
   ```

2. **Teste com dados reais:**
   - Crie um pet no sistema
   - Adicione um tratamento para amanhã
   - Execute em modo dry-run
   - Verifique os logs

3. **Teste de envio real:**
   - Configure suas credenciais Gmail
   - Execute sem --dry-run
   - Verifique se o email foi recebido

### 📊 **Teste do Relatório Mensal**

1. **Teste básico (dry-run):**
   ```bash
   uv run python monthly_check.py --dry-run --verbose
   ```

2. **Teste com dados reais:**
   - Crie pets no sistema
   - Adicione tratamentos para o mês atual
   - Adicione tratamentos expirados (datas passadas)
   - Execute em modo dry-run
   - Verifique os logs detalhados

3. **Teste de envio real:**
   - Configure suas credenciais Gmail
   - Execute sem --dry-run
   - Verifique se o relatório foi recebido

### ✅ **Validação dos Templates**
- Verifique se os dados aparecem corretamente
- Confirme formatação de datas e horários
- Teste com pets que têm/não têm tratamentos expirados
- Valide cálculo de dias em atraso

## 🚨 Resolução de problemas

### Email não é enviado
- ✅ Verifique se `GMAIL_EMAIL` e `GMAIL_PASSWORD` estão corretos
- ✅ Confirme que está usando senha de app, não senha normal
- ✅ Verifique se a verificação em duas etapas está ativa
- ✅ Teste com `--dry-run` primeiro

### Nenhum tratamento encontrado
- ✅ **Daily**: Verifique se há tratamentos agendados para amanhã
- ✅ **Monthly**: Verifique se há tratamentos do mês atual ou expirados  
- ✅ Confirme se há pets cadastrados
- ✅ Verifique se os tratamentos não estão marcados como concluídos
- ✅ Confirme se os tutores têm email cadastrado no perfil

### Erros de conexão com banco
- ✅ Verifique se o PostgreSQL está rodando
- ✅ Confirme a variável `DATABASE_URL` no .env
- ✅ Teste a conectividade manual

## 📝 Logs

O sistema gera logs detalhados quando executado com `--verbose`:

- 🔍 **DEBUG**: Detalhes técnicos da execução
- ℹ️ **INFO**: Informações gerais do processo
- ⚠️ **WARNING**: Avisos não críticos
- ❌ **ERROR**: Erros que impedem o funcionamento

Os logs ajudam a diagnosticar problemas e monitorar o funcionamento do sistema.
