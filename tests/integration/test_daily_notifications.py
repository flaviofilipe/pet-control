import pytest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from pathlib import Path

from app.database import Database
from app.services.notification_service import NotificationService
from app.repositories.pet_repository import PetRepository
from app.repositories.user_repository import UserRepository


class TestDailyNotificationsIntegration:
    """Testes de integração para o sistema completo de notificações diárias"""
    
    @pytest.fixture
    def db_with_test_data(self, db_collections):
        """Fixture que cria dados de teste no banco"""
        # Limpa collections
        db_collections["pets"].delete_many({})
        db_collections["profiles"].delete_many({})
        
        # Data de amanhã
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")
        
        # Cria usuários/tutores
        tutors_data = [
            {
                "_id": "tutor1",
                "name": "João Silva",
                "email": "joao.silva@email.com",
                "is_vet": False
            },
            {
                "_id": "tutor2", 
                "name": "Maria Santos",
                "email": "maria.santos@email.com",
                "is_vet": False
            },
            {
                "_id": "vet1",
                "name": "Dr. Carlos Veterinário",
                "email": "dr.carlos@veterinaria.com",
                "is_vet": True
            },
            {
                "_id": "tutor_sem_email",
                "name": "Pedro Sem Email",
                "email": "",  # Sem email válido
                "is_vet": False
            }
        ]
        
        # Insere tutores
        db_collections["profiles"].insert_many(tutors_data)
        
        # Cria pets com tratamentos
        pets_data = [
            {
                "_id": "pet1",
                "name": "Rex",
                "nickname": "rex_1234",
                "breed": "Golden Retriever",
                "pet_type": "dog",
                "users": ["tutor1", "vet1"],  # Dois tutores com email
                "deleted_at": None,
                "treatments": [
                    {
                        "_id": "treatment1",
                        "name": "Vacina Antirrábica",
                        "category": "Vacina",
                        "description": "Vacina anual obrigatória contra raiva",
                        "date": tomorrow_str,
                        "time": "14:00",
                        "applier_type": "Veterinarian",
                        "applier_name": "Dr. Carlos",
                        "done": False
                    },
                    {
                        "_id": "treatment2",
                        "name": "Vermífugo",
                        "category": "Medicamento",
                        "description": "Controle preventivo de vermes",
                        "date": tomorrow_str,
                        "time": "14:30",
                        "applier_type": "Tutor",
                        "applier_name": "",
                        "done": False
                    }
                ]
            },
            {
                "_id": "pet2",
                "name": "Miau",
                "nickname": "miau_5678",
                "breed": "Persa",
                "pet_type": "cat",
                "users": ["tutor2"],  # Um tutor com email
                "deleted_at": None,
                "treatments": [
                    {
                        "_id": "treatment3",
                        "name": "Vacina V4",
                        "category": "Vacina",
                        "description": "Vacina múltipla para gatos",
                        "date": tomorrow_str,
                        "time": "10:00",
                        "applier_type": "Veterinarian",
                        "applier_name": "Dr. Carlos",
                        "done": False
                    }
                ]
            },
            {
                "_id": "pet3",
                "name": "Buddy",
                "nickname": "buddy_9999",
                "breed": "Vira-lata",
                "pet_type": "dog",
                "users": ["tutor_sem_email"],  # Tutor sem email válido
                "deleted_at": None,
                "treatments": [
                    {
                        "_id": "treatment4",
                        "name": "Medicamento",
                        "category": "Medicamento",
                        "description": "Antibiótico",
                        "date": tomorrow_str,
                        "time": "16:00",
                        "applier_type": "Tutor",
                        "applier_name": "",
                        "done": False
                    }
                ]
            },
            {
                "_id": "pet4",
                "name": "Deletado",
                "nickname": "deletado_0000",
                "breed": "Teste",
                "pet_type": "dog",
                "users": ["tutor1"],
                "deleted_at": datetime.now(),  # Pet deletado - não deve aparecer
                "treatments": [
                    {
                        "_id": "treatment5",
                        "name": "Tratamento Deletado",
                        "category": "Teste",
                        "description": "Não deve aparecer",
                        "date": tomorrow_str,
                        "time": "18:00",
                        "applier_type": "Tutor",
                        "applier_name": "",
                        "done": False
                    }
                ]
            },
            {
                "_id": "pet5",
                "name": "Tratamento Concluído",
                "nickname": "concluido_1111",
                "breed": "Teste",
                "pet_type": "dog", 
                "users": ["tutor1"],
                "deleted_at": None,
                "treatments": [
                    {
                        "_id": "treatment6",
                        "name": "Tratamento Concluído",
                        "category": "Teste",
                        "description": "Já foi feito",
                        "date": tomorrow_str,
                        "time": "19:00",
                        "applier_type": "Tutor",
                        "applier_name": "",
                        "done": True  # Tratamento já concluído - não deve aparecer
                    }
                ]
            }
        ]
        
        # Insere pets
        db_collections["pets"].insert_many(pets_data)
        
        return {
            "tomorrow_str": tomorrow_str,
            "expected_pets_with_treatments": 2,  # pet1 e pet2 (pet3 sem email válido)
            "expected_total_emails": 3  # tutor1 + vet1 + tutor2
        }
    
    def test_get_tomorrow_treatments_integration(self, db_with_test_data):
        """Testa busca de tratamentos de amanhã com dados reais"""
        pet_repo = PetRepository()
        
        treatments = pet_repo.get_tomorrow_scheduled_treatments()
        
        # Deve encontrar 2 pets (pet1 e pet2)
        # pet3 tem tutor sem email válido mas ainda aparecerá na busca do repository
        # pet4 está deletado - não aparece
        # pet5 tem tratamento concluído - não aparece
        assert len(treatments) == 3  # pet1, pet2, pet3 (repository não filtra por email)
        
        # Verifica pet1 (Rex)
        pet1_data = next((p for p in treatments if p["name"] == "Rex"), None)
        assert pet1_data is not None
        assert pet1_data["nickname"] == "rex_1234"
        assert len(pet1_data["treatments"]) == 2  # Dois tratamentos
        assert len(pet1_data["users"]) == 2  # tutor1 e vet1
        
        # Verifica pet2 (Miau)
        pet2_data = next((p for p in treatments if p["name"] == "Miau"), None)
        assert pet2_data is not None
        assert pet2_data["nickname"] == "miau_5678"
        assert len(pet2_data["treatments"]) == 1  # Um tratamento
        assert len(pet2_data["users"]) == 1  # tutor2
    
    def test_get_user_emails_integration(self, db_with_test_data):
        """Testa busca de emails de tutores com dados reais"""
        user_repo = UserRepository()
        
        # Busca emails de todos os tutores
        all_user_ids = ["tutor1", "tutor2", "vet1", "tutor_sem_email"]
        emails = user_repo.get_user_emails_by_ids(all_user_ids)
        
        # Deve retornar apenas tutores com email válido
        assert len(emails) == 3  # tutor1, tutor2, vet1 (tutor_sem_email não tem email)
        
        emails_dict = {email["id"]: email for email in emails}
        
        # Verifica tutor1
        assert "tutor1" in emails_dict
        assert emails_dict["tutor1"]["name"] == "João Silva"
        assert emails_dict["tutor1"]["email"] == "joao.silva@email.com"
        
        # Verifica tutor2
        assert "tutor2" in emails_dict
        assert emails_dict["tutor2"]["name"] == "Maria Santos"
        assert emails_dict["tutor2"]["email"] == "maria.santos@email.com"
        
        # Verifica vet1
        assert "vet1" in emails_dict
        assert emails_dict["vet1"]["name"] == "Dr. Carlos Veterinário"
        assert emails_dict["vet1"]["email"] == "dr.carlos@veterinaria.com"
        
        # Verifica que tutor_sem_email não está presente
        assert "tutor_sem_email" not in emails_dict
    
    def test_notification_service_integration_dry_run(self, db_with_test_data):
        """Testa o serviço completo de notificações em modo dry-run"""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            
            # Cria template simples para teste
            template_content = """
            <html><body>
            <h1>Lembrete para {{ tutor_name }}</h1>
            <p>Pet: {{ pet_name }}</p>
            <p>Tratamentos: {{ total_treatments }}</p>
            </body></html>
            """
            
            template_file = template_dir / "treatment_reminder.html"
            template_file.write_text(template_content)
            
            # Cria serviço e reconfigura o jinja_env
            notification_service = NotificationService()
            
            # Reconfigura o template engine para usar o diretório temporário
            from jinja2 import Environment, FileSystemLoader
            notification_service.jinja_env = Environment(loader=FileSystemLoader(template_dir))
            
            # Processa notificações em modo dry-run
            result = notification_service.process_daily_notifications(dry_run=True)
            
            # Verifica resultado
            assert result["success"] is True
            assert result["dry_run"] is True
            assert result["total_pets"] == 2  # pet1 e pet2 (pet3 não tem email válido)
            assert result["emails_sent"] == 3  # tutor1 + vet1 + tutor2
            assert len(result["errors"]) == 0
            
            assert "3 emails enviados para 2 pets" in result["message"]
    
    def test_notification_service_get_tomorrow_treatments_with_tutors(self, db_with_test_data):
        """Testa método específico que combina pets e tutores"""
        notification_service = NotificationService()
        
        success, data, message = notification_service.get_tomorrow_treatments_with_tutors()
        
        assert success is True
        assert len(data) == 2  # Apenas pets com tutores que têm email válido
        assert "2 pets com tratamentos agendados" in message
        
        # Verifica estrutura dos dados
        for pet_data in data:
            assert "pet" in pet_data
            assert "treatments" in pet_data
            assert "tutors" in pet_data
            
            # Todos os tutores devem ter email
            for tutor in pet_data["tutors"]:
                assert tutor["email"] != ""
                assert "@" in tutor["email"]
    
    def test_notification_service_format_treatments_for_email(self, db_with_test_data):
        """Testa formatação de dados para email"""
        notification_service = NotificationService()
        
        # Busca dados reais
        success, data, _ = notification_service.get_tomorrow_treatments_with_tutors()
        assert success is True
        assert len(data) > 0
        
        # Testa formatação do primeiro pet
        formatted = notification_service.format_treatments_for_email(data[0])
        
        # Verifica estrutura
        assert "pet_name" in formatted
        assert "pet_nickname" in formatted
        assert "date" in formatted
        assert "treatments" in formatted
        assert "total_treatments" in formatted
        
        # Verifica data de amanhã
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        assert formatted["date"] == tomorrow
        
        # Verifica tratamentos
        assert formatted["total_treatments"] > 0
        assert len(formatted["treatments"]) == formatted["total_treatments"]
        
        # Verifica estrutura de cada tratamento
        for treatment in formatted["treatments"]:
            assert "name" in treatment
            assert "category" in treatment
            assert "time" in treatment
            assert "applier_type" in treatment
    
    @patch('app.services.notification_service.validate_gmail_config')
    def test_notification_service_email_sending_without_gmail(self, mock_validate, db_with_test_data):
        """Testa comportamento quando Gmail não está configurado"""
        mock_validate.return_value = (False, "Gmail não configurado")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            template_content = "<html><body>Test</body></html>"
            template_file = template_dir / "treatment_reminder.html"
            template_file.write_text(template_content)
            
            # Cria serviço e reconfigura o jinja_env
            notification_service = NotificationService()
            
            # Reconfigura o template engine para usar o diretório temporário
            from jinja2 import Environment, FileSystemLoader
            notification_service.jinja_env = Environment(loader=FileSystemLoader(template_dir))
            
            # Tenta processar notificações sem Gmail configurado
            result = notification_service.process_daily_notifications(dry_run=False)
            
            # Deve ter sucessos (processamento) mas erros no envio
            assert result["success"] is True
            assert result["total_pets"] == 2
            assert result["emails_sent"] == 0  # Nenhum email enviado
            assert len(result["errors"]) > 0  # Erros de configuração
            
            # Todos os erros devem ser sobre Gmail não configurado
            for error in result["errors"]:
                assert "Gmail não configurado" in error
    
    def test_edge_case_no_treatments_tomorrow(self, db_collections):
        """Testa comportamento quando não há tratamentos para amanhã"""
        # Limpa todas as collections
        db_collections["pets"].delete_many({})
        db_collections["profiles"].delete_many({})
        
        notification_service = NotificationService()
        
        # Busca tratamentos (deve estar vazio)
        success, data, message = notification_service.get_tomorrow_treatments_with_tutors()
        
        assert success is True
        assert len(data) == 0
        assert message == "Nenhum tratamento agendado para amanhã."
        
        # Processa notificações
        result = notification_service.process_daily_notifications(dry_run=True)
        
        assert result["success"] is True
        assert result["total_pets"] == 0
        assert result["emails_sent"] == 0
        assert len(result["errors"]) == 0
        assert "Nenhum tratamento agendado para amanhã" in result["message"]
    
    def test_edge_case_treatments_for_different_dates(self, db_collections):
        """Testa que apenas tratamentos de amanhã são capturados"""
        # Limpa collections
        db_collections["pets"].delete_many({})
        db_collections["profiles"].delete_many({})
        
        # Datas de teste
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after_tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Cria tutor
        db_collections["profiles"].insert_one({
            "_id": "tutor1",
            "name": "João Silva", 
            "email": "joao@email.com"
        })
        
        # Cria pet com tratamentos em diferentes datas
        db_collections["pets"].insert_one({
            "_id": "pet1",
            "name": "Rex",
            "nickname": "rex_1234",
            "users": ["tutor1"],
            "deleted_at": None,
            "treatments": [
                {
                    "_id": "treatment_today",
                    "name": "Tratamento Hoje",
                    "date": today,
                    "done": False
                },
                {
                    "_id": "treatment_tomorrow",
                    "name": "Tratamento Amanhã",
                    "date": tomorrow,
                    "done": False
                },
                {
                    "_id": "treatment_day_after",
                    "name": "Tratamento Depois de Amanhã",
                    "date": day_after_tomorrow,
                    "done": False
                }
            ]
        })
        
        pet_repo = PetRepository()
        treatments = pet_repo.get_tomorrow_scheduled_treatments()
        
        # Deve encontrar apenas 1 pet com 1 tratamento (de amanhã)
        assert len(treatments) == 1
        assert treatments[0]["name"] == "Rex"
        assert len(treatments[0]["treatments"]) == 1
        assert treatments[0]["treatments"][0]["name"] == "Tratamento Amanhã"
