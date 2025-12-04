"""Configurações globais e fixtures para os testes."""

import os
import sys
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from PIL import Image
import io

# Define variáveis de ambiente para teste antes de importar main
os.environ.update({
    "ENVIRONMENT": "testing",
    "DATABASE_URL": "sqlite+aiosqlite:///:memory:",  # SQLite em memória para testes
    "AUTH0_DOMAIN": "test-domain.auth0.com",
    "AUTH0_API_AUDIENCE": "test-audience",
    "AUTH0_CLIENT_ID": "test-client-id",
    "AUTH0_CLIENT_SECRET": "test-client-secret",
    "AUTH0_CALLBACK_URI": "http://localhost:8000/callback",
    "SESSION_SECRET_KEY": "test-secret-key-for-testing",
    "FRONTEND_URL": "http://localhost:8000",
})

# Cria diretórios necessários para o app
Path("templates").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)
Path("uploads").mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """Create fresh database for each test"""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from app.database.base import Base
    
    # Engine de teste com SQLite
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    # Session factory de teste
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Criar todas as tabelas
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Criar sessão
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Limpar após o teste
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


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
def client(temp_upload_dir):
    """Cliente de teste para a aplicação FastAPI."""
    # Patch do database para usar SQLite em memória
    from unittest.mock import AsyncMock
    
    # Importa main depois de configurar o ambiente
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
