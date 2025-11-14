"""Configurações globais e fixtures para os testes."""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from mongomock import MongoClient as MockMongoClient
from PIL import Image
import io
import json

# Define variáveis de ambiente para teste antes de importar main
os.environ.update({
    "ENVIRONMENT": "testing",  # Define ambiente de testes
    "AUTH0_DOMAIN": "test-domain.auth0.com",
    "AUTH0_API_AUDIENCE": "test-audience",
    "AUTH0_CLIENT_ID": "test-client-id",
    "AUTH0_CLIENT_SECRET": "test-client-secret",
    "AUTH0_CALLBACK_URI": "http://localhost:8000/callback",
    "MONGO_URI": "mongodb://test:27017/",
    "SESSION_SECRET_KEY": "test-secret-key-for-testing",
})

# Patch do MongoDB antes de importar main
mock_mongo_client = MockMongoClient()

# Cria diretórios necessários para o app
from pathlib import Path
Path("templates").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)
Path("uploads").mkdir(exist_ok=True)

# Patch global que persiste durante toda a sessão de teste  
_mongo_patch = patch("pymongo.MongoClient", return_value=mock_mongo_client)
_mongo_patch.start()

# Força limpeza de qualquer importação prévia do main
import sys
if 'main' in sys.modules:
    del sys.modules['main']

@pytest.fixture(scope="session", autouse=True) 
def patch_mongo():
    """Patch global do MongoDB para usar MockMongoDB."""
    yield mock_mongo_client


@pytest.fixture(scope="function")
def clean_db():
    """Limpa o banco de dados antes de cada teste."""
    # Limpa todas as collections
    mock_mongo_client.drop_database("pet_control")
    yield
    # Limpa novamente após o teste
    mock_mongo_client.drop_database("pet_control")


@pytest.fixture
def temp_upload_dir():
    """Cria um diretório temporário para uploads de teste."""
    temp_dir = tempfile.mkdtemp()
    original_upload_dir = None
    
    # Importa o FileService da nova estrutura
    from app.services.file_service import UPLOAD_DIR
    import app.services.file_service as file_service_module
    
    original_upload_dir = UPLOAD_DIR
    file_service_module.UPLOAD_DIR = Path(temp_dir)
    
    yield Path(temp_dir)
    
    # Limpa o diretório temporário
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)
    
    # Restaura o diretório original
    if original_upload_dir:
        file_service_module.UPLOAD_DIR = original_upload_dir


@pytest.fixture
def mock_auth0_responses():
    """Mock das respostas do Auth0."""
    return {
        "token_response": {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "id_token": "test-id-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        "userinfo_response": {
            "sub": "auth0|test-user-id",
            "name": "Test User",
            "email": "test@example.com",
            "email_verified": True,
            "picture": "https://example.com/avatar.jpg",
        },
        "refresh_response": {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
    }


@pytest.fixture
def mock_external_apis():
    """Mock das APIs externas (Dog API, Cat API)."""
    dog_breeds_response = {
        "message": {
            "retriever": ["golden", "labrador"],
            "bulldog": ["english", "french"],
            "terrier": ["boston", "bull"],
        },
        "status": "success",
    }
    
    cat_breeds_response = [
        {"id": "abys", "name": "Abyssinian"},
        {"id": "aege", "name": "Aegean"},
        {"id": "abob", "name": "American Bobtail"},
    ]
    
    return {
        "dog_breeds": dog_breeds_response,
        "cat_breeds": cat_breeds_response,
    }


@pytest.fixture
def authenticated_user():
    """Dados de um usuário autenticado para testes."""
    return {
        "id": "auth0|test-user-id",
        "info": {
            "sub": "auth0|test-user-id",
            "name": "Test User",
            "email": "test@example.com",
            "email_verified": True,
        }
    }


@pytest.fixture
def veterinarian_user():
    """Dados de um usuário veterinário para testes."""
    return {
        "id": "auth0|vet-user-id",
        "info": {
            "sub": "auth0|vet-user-id",
            "name": "Dr. Vet Test",
            "email": "vet@example.com",
            "email_verified": True,
            "is_vet": True,
        }
    }


@pytest.fixture
def sample_pet_data():
    """Dados de exemplo para criar um pet."""
    return {
        "name": "Rex",
        "breed": "Golden Retriever",
        "pedigree_number": "ABC123",
        "birth_date": "2020-01-15",
        "pet_type": "dog",
        "gender": "male",
        "nickname": "rex_1234",
        "users": ["auth0|test-user-id"],
        "treatments": [],
        "deleted_at": None,
    }


@pytest.fixture
def sample_treatment_data():
    """Dados de exemplo para criar um tratamento."""
    return {
        "category": "Vacinas",
        "name": "V8",
        "description": "Vacina óctupla",
        "date": "2024-12-01",
        "time": "14:00",
        "applier_type": "Veterinarian",
        "applier_name": "Dr. Test",
        "applier_id": "auth0|vet-user-id",
        "done": False,
    }


@pytest.fixture
def sample_profile_data():
    """Dados de exemplo para perfil de usuário."""
    return {
        "_id": "auth0|test-user-id",
        "name": "Test User",
        "email": "test@example.com",
        "bio": "Test bio",
        "address": {
            "street": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345",
        },
        "is_vet": False,
    }


@pytest.fixture
def test_image():
    """Cria uma imagem de teste para upload."""
    # Cria uma imagem RGB simples
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def client(clean_db, temp_upload_dir, patch_mongo):
    """Cliente de teste para a aplicação FastAPI."""
    # Importa main depois do patch do mongo
    from main import app
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def authenticated_client(client, authenticated_user, mock_auth0_responses):
    """Cliente de teste com usuário autenticado."""
    from app.routes.auth_routes import get_current_user_from_session
    import main
    
    app = main.app
    
    # Store the original override (if any)
    original_override = app.dependency_overrides.get(get_current_user_from_session)
    
    # Override the dependency directly in the app
    def mock_get_user():
        return authenticated_user
    
    app.dependency_overrides[get_current_user_from_session] = mock_get_user
    
    try:
        # Simula sessão autenticada
        with client:
            # Define session data
            client.cookies.set("session", "test-session")
            yield client
    finally:
        # Restore original override or remove it
        if original_override is not None:
            app.dependency_overrides[get_current_user_from_session] = original_override
        else:
            app.dependency_overrides.pop(get_current_user_from_session, None)


@pytest.fixture
def vet_client(client, veterinarian_user):
    """Cliente de teste com veterinário autenticado."""
    from app.routes.auth_routes import get_current_user_from_session
    import main
    
    app = main.app
    
    # Store the original override (if any)
    original_override = app.dependency_overrides.get(get_current_user_from_session)
    
    # Override the dependency directly in the app
    def mock_get_user():
        return veterinarian_user
    
    app.dependency_overrides[get_current_user_from_session] = mock_get_user
    
    try:
        with client:
            client.cookies.set("session", "vet-session")
            yield client
    finally:
        # Restore original override or remove it
        if original_override is not None:
            app.dependency_overrides[get_current_user_from_session] = original_override
        else:
            app.dependency_overrides.pop(get_current_user_from_session, None)


# Fixtures para dados do banco
@pytest.fixture
def db_collections():
    """Retorna as collections do banco de dados mockado."""
    from app.database import database
    return {
        "profiles": database.profiles_collection,
        "pets": database.pets_collection,
        "vaccines": database.vaccines_collection,
        "ectoparasites": database.ectoparasites_collection,
        "vermifugos": database.vermifugos_collection,
    }


@pytest.fixture
def populated_vaccines(db_collections):
    """Popula a collection de vacinas com dados de teste."""
    vaccines_data = [
        {
            "nome_vacina": "V8",
            "descricao": "Vacina óctupla para cães",
            "especie_alvo": "Cão",
            "tipo_vacina": "Múltipla",
            "protege_contra": ["Cinomose", "Hepatite", "Parainfluenza"],
            "cronograma_vacinal": {
                "filhote": "Primeira dose aos 45 dias, segunda aos 75 dias",
                "adulto": "Anual"
            }
        },
        {
            "nome_vacina": "Antirrábica",
            "descricao": "Vacina contra raiva",
            "especie_alvo": "Cão",
            "tipo_vacina": "Única",
            "protege_contra": ["Raiva"],
            "cronograma_vacinal": {
                "filhote": "A partir dos 4 meses",
                "adulto": "Anual"
            }
        },
    ]
    
    result = db_collections["vaccines"].insert_many(vaccines_data)
    return result.inserted_ids


@pytest.fixture
def populated_ectoparasites(db_collections):
    """Popula a collection de ectoparasitas com dados de teste."""
    ectoparasites_data = [
        {
            "nome_praga": "Pulga",
            "tipo_praga": "Inseto",
            "especies_alvo": ["Cão", "Gato"],
            "transmissor_de_doencas": ["Dermatite alérgica"],
            "sintomas_no_animal": ["Coceira", "Irritação da pele"],
            "medicamentos_de_combate": [
                {
                    "descricao": "Fipronil",
                    "principios_ativos": ["Fipronil"],
                }
            ],
            "observacoes_adicionais": "Tratamento mensal recomendado",
        }
    ]
    
    result = db_collections["ectoparasites"].insert_many(ectoparasites_data)
    return result.inserted_ids


@pytest.fixture
def populated_vermifugos(db_collections):
    """Popula a collection de vermífugos com dados de teste."""
    vermifugos_data = {
        "parasitas_e_tratamentos": [
            {
                "nome_praga": "Áscaris",
                "tipo_praga": "Nematódeo",
                "especies_alvo": ["Cão", "Gato"],
                "sintomas_no_animal": ["Vômito", "Diarreia"],
                "medicamentos_de_combate": [
                    {
                        "descricao": "Pamoato de Pirantel",
                        "principios_ativos": ["Pamoato de Pirantel"],
                    }
                ],
                "observacoes_adicionais": "Repetir a cada 3 meses",
            }
        ]
    }
    
    result = db_collections["vermifugos"].insert_one(vermifugos_data)
    return result.inserted_id


# Configurações do pytest
def pytest_configure(config):
    """Configuração global do pytest."""
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )
    config.addinivalue_line(
        "markers", "auth: marca testes de autenticação"
    )
    config.addinivalue_line(
        "markers", "slow: marca testes que demoram mais para executar"
    )
