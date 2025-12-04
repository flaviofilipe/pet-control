import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path
import smtplib
import tempfile
from email.mime.multipart import MIMEMultipart

from app.services.notification_service import NotificationService


class TestNotificationService:
    """Testes para o serviço de notificações"""
    
    @pytest.fixture
    def notification_service(self):
        """Fixture para instanciar o serviço de notificações"""
        with patch('app.services.notification_service.PetRepository'), \
             patch('app.services.notification_service.UserRepository'):
            service = NotificationService(Mock())
            return service
    
    @pytest.fixture
    def mock_pet_data(self):
        """Dados de teste para pets com tratamentos"""
        return [
            {
                "_id": "507f1f77-bcf8-6cd7-9943-9011abcdef01",
                "name": "Rex",
                "nickname": "rex_1234",
                "users": ["user1", "user2"],
                "treatments": [
                    {
                        "_id": "treatment1",
                        "name": "Vacina Antirrábica",
                        "category": "Vacinas",
                        "description": "Vacina anual obrigatória",
                        "date": "2025-11-09",
                        "time": "14:00",
                        "applier_type": "Veterinarian",
                        "applier_name": "Dr. Silva",
                        "done": False
                    },
                    {
                        "_id": "treatment2",
                        "name": "Vermífugo",
                        "category": "Vermífugo",
                        "description": "Controle de vermes",
                        "date": "2025-11-09",
                        "time": "14:30",
                        "applier_type": "Tutor",
                        "applier_name": "",
                        "done": False
                    }
                ]
            }
        ]
    
    @pytest.fixture
    def mock_tutor_data(self):
        """Dados de teste para tutores"""
        return [
            {
                "id": "user1",
                "name": "João Silva",
                "email": "joao@email.com"
            },
            {
                "id": "user2", 
                "name": "Maria Santos",
                "email": "maria@email.com"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_tomorrow_treatments_with_tutors_success(self, notification_service, mock_pet_data, mock_tutor_data):
        """Testa busca de tratamentos de amanhã com sucesso"""
        # Mock dos repositories
        notification_service.pet_repo.get_tomorrow_scheduled_treatments = AsyncMock(return_value=mock_pet_data)
        notification_service.user_repo.get_user_emails_by_ids = AsyncMock(return_value=mock_tutor_data)
        
        success, data, message = await notification_service.get_tomorrow_treatments_with_tutors()
        
        assert success is True
        assert len(data) == 1
        assert data[0]["pet"]["name"] == "Rex"
        assert data[0]["pet"]["nickname"] == "rex_1234"
        assert len(data[0]["treatments"]) == 2
        assert len(data[0]["tutors"]) == 2
        assert "1 pets com tratamentos agendados" in message
    
    @pytest.mark.asyncio
    async def test_get_tomorrow_treatments_no_treatments(self, notification_service):
        """Testa quando não há tratamentos para amanhã"""
        notification_service.pet_repo.get_tomorrow_scheduled_treatments = AsyncMock(return_value=[])
        
        success, data, message = await notification_service.get_tomorrow_treatments_with_tutors()
        
        assert success is True
        assert len(data) == 0
        assert message == "Nenhum tratamento agendado para amanhã."
    
    @pytest.mark.asyncio
    async def test_get_tomorrow_treatments_no_tutors_with_email(self, notification_service, mock_pet_data):
        """Testa quando não há tutores com email válido"""
        notification_service.pet_repo.get_tomorrow_scheduled_treatments = AsyncMock(return_value=mock_pet_data)
        notification_service.user_repo.get_user_emails_by_ids = AsyncMock(return_value=[])  # Sem emails
        
        success, data, message = await notification_service.get_tomorrow_treatments_with_tutors()
        
        assert success is True
        assert len(data) == 0  # Sem pets para notificar
    
    @pytest.mark.asyncio
    async def test_get_tomorrow_treatments_exception(self, notification_service):
        """Testa tratamento de exceção na busca"""
        notification_service.pet_repo.get_tomorrow_scheduled_treatments = AsyncMock(side_effect=Exception("DB Error"))
        
        success, data, message = await notification_service.get_tomorrow_treatments_with_tutors()
        
        assert success is False
        assert len(data) == 0
        assert "Erro ao buscar tratamentos: DB Error" in message
    
    def test_format_treatments_for_email(self, notification_service):
        """Testa formatação de dados para email"""
        pet_data = {
            "pet": {
                "name": "Rex",
                "nickname": "rex_1234"
            },
            "treatments": [
                {
                    "name": "Vacina Antirrábica",
                    "category": "Vacinas",
                    "description": "Vacina anual",
                    "time": "14:00",
                    "applier_type": "Veterinarian",
                    "applier_name": "Dr. Silva"
                }
            ]
        }
        
        formatted = notification_service.format_treatments_for_email(pet_data)
        
        assert formatted["pet_name"] == "Rex"
        assert formatted["pet_nickname"] == "rex_1234"
        assert formatted["total_treatments"] == 1
        assert len(formatted["treatments"]) == 1
        assert formatted["treatments"][0]["name"] == "Vacina Antirrábica"
        assert formatted["treatments"][0]["category"] == "Vacinas"
        # Verifica se a data é de amanhã
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        assert formatted["date"] == tomorrow
    
    def test_send_email_notification_dry_run(self, notification_service):
        """Testa envio de email em modo dry-run"""
        email_data = {
            "pet_name": "Rex",
            "pet_nickname": "rex_1234",
            "date": "09/11/2025",
            "treatments": [],
            "total_treatments": 0
        }
        
        # Mock do template
        with patch.object(notification_service.jinja_env, 'get_template') as mock_template:
            mock_template.return_value.render.return_value = "<html>Test</html>"
            
            success, message = notification_service.send_email_notification(
                "test@email.com", "Teste", email_data, dry_run=True
            )
        
        assert success is True
        assert "[DRY RUN]" in message
        assert "test@email.com" in message
    
    @patch('app.services.notification_service.validate_gmail_config')
    @patch('app.services.notification_service.smtplib.SMTP')
    def test_send_email_notification_real_success(self, mock_smtp, mock_validate, notification_service):
        """Testa envio real de email com sucesso"""
        # Mock da validação
        mock_validate.return_value = (True, "Gmail configurado")
        
        # Mock do SMTP
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Mock do template
        with patch.object(notification_service.jinja_env, 'get_template') as mock_template:
            mock_template.return_value.render.return_value = "<html>Test</html>"
            
            email_data = {
                "pet_name": "Rex",
                "pet_nickname": "rex_1234", 
                "date": "09/11/2025",
                "treatments": [],
                "total_treatments": 0
            }
            
            success, message = notification_service.send_email_notification(
                "test@email.com", "Teste", email_data, dry_run=False
            )
        
        assert success is True
        assert "Email enviado para test@email.com" in message
        mock_server.starttls.assert_called_once()
        mock_server.send_message.assert_called_once()
    
    @patch('app.services.notification_service.validate_gmail_config')
    def test_send_email_notification_invalid_config(self, mock_validate, notification_service):
        """Testa envio com configuração inválida do Gmail"""
        mock_validate.return_value = (False, "Gmail não configurado")
        
        with patch.object(notification_service.jinja_env, 'get_template') as mock_template:
            mock_template.return_value.render.return_value = "<html>Test</html>"
            
            success, message = notification_service.send_email_notification(
                "test@email.com", "Teste", {}, dry_run=False
            )
        
        assert success is False
        assert message == "Gmail não configurado"
    
    @patch('app.services.notification_service.validate_gmail_config')
    @patch('app.services.notification_service.smtplib.SMTP')
    def test_send_email_notification_smtp_error(self, mock_smtp, mock_validate, notification_service):
        """Testa erro no SMTP"""
        mock_validate.return_value = (True, "Gmail configurado")
        mock_smtp.side_effect = Exception("SMTP Error")
        
        # Dados completos para evitar KeyError
        email_data = {
            "pet_name": "Rex",
            "pet_nickname": "rex_1234",
            "date": "09/11/2025", 
            "treatments": [],
            "total_treatments": 0
        }
        
        with patch.object(notification_service.jinja_env, 'get_template') as mock_template:
            mock_template.return_value.render.return_value = "<html>Test</html>"
            
            success, message = notification_service.send_email_notification(
                "test@email.com", "Teste", email_data, dry_run=False
            )
        
        assert success is False
        assert "SMTP Error" in message
    
    @pytest.mark.asyncio
    async def test_process_daily_notifications_no_treatments(self, notification_service):
        """Testa processamento quando não há tratamentos"""
        with patch.object(notification_service, 'get_tomorrow_treatments_with_tutors', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (True, [], "Nenhum tratamento agendado para amanhã.")
            
            result = await notification_service.process_daily_notifications(dry_run=True)
        
        assert result["success"] is True
        assert result["total_pets"] == 0
        assert result["emails_sent"] == 0
        assert result["dry_run"] is True
        assert "Nenhum tratamento agendado" in result["message"]
    
    @pytest.mark.asyncio
    async def test_process_daily_notifications_error_getting_treatments(self, notification_service):
        """Testa processamento quando há erro ao buscar tratamentos"""
        with patch.object(notification_service, 'get_tomorrow_treatments_with_tutors', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (False, [], "Erro no banco")
            
            result = await notification_service.process_daily_notifications(dry_run=True)
        
        assert result["success"] is False
        assert result["total_pets"] == 0
        assert result["emails_sent"] == 0
        assert result["dry_run"] is True
        assert result["message"] == "Erro no banco"
    
    @pytest.mark.asyncio
    async def test_process_daily_notifications_success(self, notification_service):
        """Testa processamento completo com sucesso"""
        # Mock dos dados
        treatments_data = [{
            "pet": {"name": "Rex", "nickname": "rex_1234"},
            "treatments": [{"name": "Vacina", "category": "Vacinas"}],
            "tutors": [{"email": "test@email.com", "name": "Teste"}]
        }]
        
        with patch.object(notification_service, 'get_tomorrow_treatments_with_tutors', new_callable=AsyncMock) as mock_get, \
             patch.object(notification_service, 'format_treatments_for_email') as mock_format, \
             patch.object(notification_service, 'send_email_notification') as mock_send:
            
            mock_get.return_value = (True, treatments_data, "Tratamentos encontrados")
            mock_format.return_value = {"formatted": "data"}
            mock_send.return_value = (True, "Email enviado")
            
            result = await notification_service.process_daily_notifications(dry_run=True)
        
        assert result["success"] is True
        assert result["total_pets"] == 1
        assert result["emails_sent"] == 1
        assert result["dry_run"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_process_daily_notifications_partial_errors(self, notification_service):
        """Testa processamento com erros parciais"""
        treatments_data = [{
            "pet": {"name": "Rex", "nickname": "rex_1234"},
            "treatments": [{"name": "Vacina"}],
            "tutors": [
                {"email": "success@email.com", "name": "Success"},
                {"email": "error@email.com", "name": "Error"}
            ]
        }]
        
        def mock_send_side_effect(email, name, data, dry_run):
            if "success" in email:
                return (True, "Email enviado")
            else:
                return (False, "Erro no envio")
        
        with patch.object(notification_service, 'get_tomorrow_treatments_with_tutors', new_callable=AsyncMock) as mock_get, \
             patch.object(notification_service, 'format_treatments_for_email') as mock_format, \
             patch.object(notification_service, 'send_email_notification') as mock_send:
            
            mock_get.return_value = (True, treatments_data, "Tratamentos encontrados")
            mock_format.return_value = {"formatted": "data"}
            mock_send.side_effect = mock_send_side_effect
            
            result = await notification_service.process_daily_notifications(dry_run=True)
        
        assert result["success"] is True
        assert result["total_pets"] == 1
        assert result["emails_sent"] == 1  # Só um sucesso
        assert len(result["errors"]) == 1  # Um erro
        assert "Erro no envio" in result["errors"][0]


class TestNotificationTemplate:
    """Testes para o template de notificação"""
    
    @pytest.fixture
    def template_service(self):
        """Fixture para testar templates"""
        with patch('app.services.notification_service.PetRepository'), \
             patch('app.services.notification_service.UserRepository'):
            
            service = NotificationService(Mock())
            return service
    
    def test_template_rendering(self, template_service):
        """Testa renderização do template"""
        email_data = {
            "pet_name": "Rex",
            "pet_nickname": "rex_1234",
            "date": "09/11/2025",
            "total_treatments": 2,
            "treatments": [
                {"name": "Vacina", "category": "Vacinas"},
                {"name": "Vermífugo", "category": "Vermífugo"}
            ]
        }
        
        # Cria template temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            
            # Criar template simples para teste
            template_content = """
            <html>
            <body>
                <h1>Lembrete para {{ tutor_name }}</h1>
                <p>Pet: {{ pet_name }} ({{ pet_nickname }})</p>
                <p>Data: {{ date }}</p>
                <p>Total de tratamentos: {{ total_treatments }}</p>
                {% for treatment in treatments %}
                <div>{{ treatment.name }} - {{ treatment.category }}</div>
                {% endfor %}
            </body>
            </html>
            """
            
            template_file = template_dir / "treatment_reminder.html"
            template_file.write_text(template_content)
            
            # Mock do diretório de templates
            with patch('app.services.notification_service.Path') as mock_path:
                mock_path.return_value.parent = template_dir
                
                # Recria o serviço com o novo diretório
                from jinja2 import Environment, FileSystemLoader
                template_service.jinja_env = Environment(loader=FileSystemLoader(template_dir))
                
                template = template_service.jinja_env.get_template("treatment_reminder.html")
                rendered = template.render(tutor_name="João", **email_data)
                
                assert "Lembrete para João" in rendered
                assert "Pet: Rex (rex_1234)" in rendered
                assert "Data: 09/11/2025" in rendered
                assert "Total de tratamentos: 2" in rendered
                assert "Vacina - Vacinas" in rendered
                assert "Vermífugo - Vermífugo" in rendered


class TestConfigValidation:
    """Testes para validação de configurações"""
    
    @patch('app.config.GMAIL_EMAIL', 'test@gmail.com')
    @patch('app.config.GMAIL_PASSWORD', 'senha123')
    def test_validate_gmail_config_success(self):
        """Testa validação bem-sucedida do Gmail"""
        from app.config import validate_gmail_config
        
        is_valid, message = validate_gmail_config()
        
        assert is_valid is True
        assert "Gmail configurado corretamente" in message
    
    @patch('app.config.GMAIL_EMAIL', '')
    @patch('app.config.GMAIL_PASSWORD', 'senha123')
    def test_validate_gmail_config_missing_email(self):
        """Testa validação com email faltando"""
        from app.config import validate_gmail_config
        
        is_valid, message = validate_gmail_config()
        
        assert is_valid is False
        assert "GMAIL_EMAIL e GMAIL_PASSWORD devem ser configurados" in message
    
    @patch('app.config.GMAIL_EMAIL', 'test@gmail.com')
    @patch('app.config.GMAIL_PASSWORD', '')
    def test_validate_gmail_config_missing_password(self):
        """Testa validação com senha faltando"""
        from app.config import validate_gmail_config
        
        is_valid, message = validate_gmail_config()
        
        assert is_valid is False
        assert "GMAIL_EMAIL e GMAIL_PASSWORD devem ser configurados" in message
