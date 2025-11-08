"""Testes para funcionalidades de perfil de usuário."""

import pytest
from bson import ObjectId


@pytest.mark.integration
class TestUserProfiles:
    """Testes para gestão de perfis de usuário."""

    def test_get_user_profile_with_existing_profile(
        self, authenticated_client, db_collections, sample_profile_data
    ):
        """Testa visualização de perfil existente."""
        # Insere perfil no banco
        db_collections["profiles"].insert_one(sample_profile_data)
        
        response = authenticated_client.get("/profile")
        
        assert response.status_code == 200
        assert "Test User" in response.text
        assert "test@example.com" in response.text
        assert "Test bio" in response.text

    def test_get_user_profile_without_existing_profile(
        self, authenticated_client, authenticated_user
    ):
        """Testa visualização de perfil sem dados no banco (fallback Auth0)."""
        response = authenticated_client.get("/profile")
        
        assert response.status_code == 200
        # Deve usar dados do Auth0 como fallback
        assert authenticated_user["info"]["name"] in response.text
        # Check for profile page content instead of specific message
        assert "Editar Perfil" in response.text
        assert "Meu Perfil" in response.text

    def test_edit_profile_page_with_existing_data(
        self, authenticated_client, db_collections, sample_profile_data
    ):
        """Testa página de edição com dados existentes."""
        db_collections["profiles"].insert_one(sample_profile_data)
        
        response = authenticated_client.get("/profile/edit")
        
        assert response.status_code == 200
        assert "Test User" in response.text
        assert sample_profile_data["address"]["street"] in response.text

    def test_edit_profile_page_without_existing_data(
        self, authenticated_client, authenticated_user
    ):
        """Testa página de edição sem dados existentes."""
        response = authenticated_client.get("/profile/edit")
        
        assert response.status_code == 200
        # Deve usar dados do Auth0 como fallback
        assert authenticated_user["info"]["name"] in response.text

    def test_create_profile_success(
        self, authenticated_client, db_collections, authenticated_user
    ):
        """Testa criação de perfil com sucesso."""
        profile_data = {
            "name": "New User Name",
            "bio": "New bio text",
            "street": "123 New Street",
            "city": "New City",
            "state": "NS",
            "zip": "12345",
            "is_vet": False,
        }
        
        response = authenticated_client.post("/profile", data=profile_data, follow_redirects=False)
        
        assert response.status_code == 303  # Redirect
        assert "/profile" in response.headers["location"]
        
        # Verifica se foi salvo no banco
        saved_profile = db_collections["profiles"].find_one(
            {"_id": authenticated_user["id"]}
        )
        assert saved_profile is not None
        assert saved_profile["name"] == "New User Name"
        assert saved_profile["bio"] == "New bio text"
        assert saved_profile["address"]["street"] == "123 New Street"
        assert saved_profile["is_vet"] is False

    def test_update_existing_profile(
        self, authenticated_client, db_collections, sample_profile_data
    ):
        """Testa atualização de perfil existente."""
        # Insere perfil inicial
        db_collections["profiles"].insert_one(sample_profile_data)
        
        updated_data = {
            "name": "Updated Name",
            "bio": "Updated bio",
            "street": "Updated Street",
            "city": "Updated City",
            "state": "UC",
            "zip": "54321",
            "is_vet": True,
        }
        
        response = authenticated_client.post("/profile", data=updated_data, follow_redirects=False)
        
        assert response.status_code == 303  # Redirect
        
        # Verifica se foi atualizado no banco
        updated_profile = db_collections["profiles"].find_one(
            {"_id": sample_profile_data["_id"]}
        )
        assert updated_profile["name"] == "Updated Name"
        assert updated_profile["bio"] == "Updated bio"
        assert updated_profile["is_vet"] is True
        assert updated_profile["address"]["city"] == "Updated City"

    def test_create_veterinarian_profile(
        self, authenticated_client, db_collections, authenticated_user
    ):
        """Testa criação de perfil de veterinário."""
        profile_data = {
            "name": "Dr. Veterinarian",
            "bio": "Experienced veterinarian",
            "street": "Vet Clinic Street",
            "city": "Pet City",
            "state": "PC",
            "zip": "99999",
            "is_vet": True,  # Marca como veterinário
        }
        
        response = authenticated_client.post("/profile", data=profile_data, follow_redirects=False)
        
        assert response.status_code == 303
        
        # Verifica se foi marcado como veterinário
        saved_profile = db_collections["profiles"].find_one(
            {"_id": authenticated_user["id"]}
        )
        assert saved_profile["is_vet"] is True
        assert saved_profile["name"] == "Dr. Veterinarian"

    def test_profile_form_validation(self, authenticated_client):
        """Testa validação dos campos obrigatórios."""
        # Envia dados sem nome (campo obrigatório)
        response = authenticated_client.post("/profile", data={"bio": "Test bio"})
        
        # FastAPI deve retornar erro de validação
        assert response.status_code == 422

    def test_profile_with_partial_address(
        self, authenticated_client, db_collections, authenticated_user
    ):
        """Testa criação de perfil com endereço parcial."""
        profile_data = {
            "name": "Test User",
            "bio": "Test bio",
            "street": "123 Test St",
            "city": "Test City",
            # state e zip são None/vazios
        }
        
        response = authenticated_client.post("/profile", data=profile_data, follow_redirects=False)
        
        assert response.status_code == 303
        
        saved_profile = db_collections["profiles"].find_one(
            {"_id": authenticated_user["id"]}
        )
        assert saved_profile["address"]["street"] == "123 Test St"
        assert saved_profile["address"]["city"] == "Test City"
        assert saved_profile["address"]["state"] is None
        assert saved_profile["address"]["zip"] is None

    def test_profile_upsert_behavior(
        self, authenticated_client, db_collections, authenticated_user
    ):
        """Testa comportamento de upsert (create or update)."""
        user_id = authenticated_user["id"]
        
        # Primeira criação
        profile_data_1 = {
            "name": "First Name",
            "bio": "First bio",
        }
        
        response1 = authenticated_client.post("/profile", data=profile_data_1, follow_redirects=False)
        assert response1.status_code == 303
        
        # Verifica criação
        profile_count = db_collections["profiles"].count_documents({"_id": user_id})
        assert profile_count == 1
        
        # Segunda atualização
        profile_data_2 = {
            "name": "Second Name",
            "bio": "Second bio",
        }
        
        response2 = authenticated_client.post("/profile", data=profile_data_2, follow_redirects=False)
        assert response2.status_code == 303
        
        # Verifica que ainda há apenas 1 documento (atualização, não duplicação)
        profile_count = db_collections["profiles"].count_documents({"_id": user_id})
        assert profile_count == 1
        
        # Verifica se foi atualizado
        updated_profile = db_collections["profiles"].find_one({"_id": user_id})
        assert updated_profile["name"] == "Second Name"
        assert updated_profile["bio"] == "Second bio"

    def test_profile_email_from_auth0(
        self, authenticated_client, db_collections, authenticated_user
    ):
        """Testa se o email é obtido corretamente do Auth0."""
        profile_data = {
            "name": "Test User",
            "bio": "Test bio",
        }
        
        response = authenticated_client.post("/profile", data=profile_data, follow_redirects=False)
        assert response.status_code == 303
        
        saved_profile = db_collections["profiles"].find_one(
            {"_id": authenticated_user["id"]}
        )
        # Email deve vir do Auth0
        assert saved_profile["email"] == authenticated_user["info"]["email"]


@pytest.mark.unit
class TestProfileModels:
    """Testes unitários para modelos de perfil."""

    def test_user_address_model(self):
        """Testa o modelo UserAddress."""
        from main import UserAddress
        
        # Endereço completo
        address = UserAddress(
            street="123 Test St",
            city="Test City",
            state="TS",
            zip="12345"
        )
        
        assert address.street == "123 Test St"
        assert address.city == "Test City"
        assert address.state == "TS"
        assert address.zip == "12345"
        
        # Endereço com campos opcionais None
        address_partial = UserAddress()
        assert address_partial.street is None
        assert address_partial.city is None

    def test_user_profile_model(self):
        """Testa o modelo UserProfile."""
        from main import UserProfile, UserAddress
        
        address = UserAddress(
            street="123 Test St",
            city="Test City",
            state="TS",
            zip="12345"
        )
        
        profile = UserProfile(
            name="Test User",
            email="test@example.com",
            bio="Test bio",
            address=address,
            is_vet=True
        )
        
        assert profile.name == "Test User"
        assert profile.email == "test@example.com"
        assert profile.bio == "Test bio"
        assert profile.is_vet is True
        assert profile.address.street == "123 Test St"

    def test_user_profile_defaults(self):
        """Testa valores padrão do modelo UserProfile."""
        from main import UserProfile
        
        # Perfil mínimo (apenas nome obrigatório)
        profile = UserProfile(name="Minimal User")
        
        assert profile.name == "Minimal User"
        assert profile.email is None
        assert profile.bio is None
        assert profile.address is None
        assert profile.is_vet is False  # Padrão

    def test_profile_serialization(self):
        """Testa serialização do modelo de perfil."""
        from main import UserProfile, UserAddress
        
        address = UserAddress(
            street="123 Test St",
            city="Test City"
        )
        
        profile = UserProfile(
            name="Test User",
            email="test@example.com",
            address=address,
            is_vet=True
        )
        
        # Converte para dict
        profile_dict = profile.model_dump(exclude_unset=True)
        
        assert "name" in profile_dict
        assert "email" in profile_dict
        assert "address" in profile_dict
        assert profile_dict["address"]["street"] == "123 Test St"
        assert profile_dict["is_vet"] is True
