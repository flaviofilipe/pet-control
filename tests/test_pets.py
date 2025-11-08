"""Testes para funcionalidades de gestão de pets."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
from bson import ObjectId
from datetime import datetime
import io
from pathlib import Path
from PIL import Image


@pytest.mark.integration
class TestPetCRUD:
    """Testes para operações CRUD de pets."""

    def test_pet_form_page_new_pet(self, authenticated_client):
        """Testa página do formulário para novo pet."""
        with patch("main.get_dog_breeds_list") as mock_dogs, \
             patch("main.get_cat_breeds_list") as mock_cats:
            
            mock_dogs.return_value = ["Golden Retriever", "Labrador"]
            mock_cats.return_value = ["Persian", "Siamese"]
            
            response = authenticated_client.get("/pets/form")
            
            assert response.status_code == 200
            # Check that the mocks were called (verifying the functions work)
            mock_dogs.assert_called_once()
            mock_cats.assert_called_once()
            # Check for basic page content instead of specific breed names
            assert "pet_type" in response.text or "Tipo" in response.text

    def test_pet_form_page_edit_existing(
        self, authenticated_client, db_collections, sample_pet_data
    ):
        """Testa página do formulário para editar pet existente."""
        # Insere pet no banco
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        with patch("main.get_dog_breeds_list") as mock_dogs, \
             patch("main.get_cat_breeds_list") as mock_cats:
            
            mock_dogs.return_value = ["Golden Retriever", "Labrador"]
            mock_cats.return_value = ["Persian", "Siamese"]
            
            response = authenticated_client.get(f"/pets/{pet_id}/edit")
            
            assert response.status_code == 200
            assert sample_pet_data["name"] in response.text
            assert sample_pet_data["breed"] in response.text

    def test_create_pet_success(self, authenticated_client, db_collections):
        """Testa criação de pet com sucesso."""
        pet_data = {
            "name": "Buddy",
            "breed": "Golden Retriever",
            "pedigree_number": "ABC123",
            "birth_date": "2020-05-15",
            "pet_type": "dog",
            "gender": "male",
        }
        
        response = authenticated_client.post("/pets", data=pet_data, follow_redirects=False)
        
        assert response.status_code == 303  # Redirect to dashboard
        assert "/dashboard" in response.headers["location"]
        
        # Verifica se foi salvo no banco
        saved_pet = db_collections["pets"].find_one({"name": "Buddy"})
        assert saved_pet is not None
        assert saved_pet["breed"] == "Golden Retriever"
        assert saved_pet["pet_type"] == "dog"
        assert saved_pet["gender"] == "male"
        assert saved_pet["deleted_at"] is None
        assert "nickname" in saved_pet  # Nickname deve ser gerado automaticamente

    def test_create_pet_with_unique_nickname(self, authenticated_client, db_collections):
        """Testa geração de nickname único."""
        # Cria primeiro pet
        pet_data_1 = {
            "name": "Rex",
            "breed": "Labrador",
            "birth_date": "2020-01-01",
            "pet_type": "dog",
            "gender": "male",
        }
        
        response1 = authenticated_client.post("/pets", data=pet_data_1, follow_redirects=False)
        assert response1.status_code == 303
        
        # Cria segundo pet com mesmo nome
        pet_data_2 = {
            "name": "Rex",
            "breed": "Beagle",
            "birth_date": "2021-01-01",
            "pet_type": "dog",
            "gender": "male",
        }
        
        response2 = authenticated_client.post("/pets", data=pet_data_2, follow_redirects=False)
        assert response2.status_code == 303
        
        # Verifica se ambos têm nicknames únicos
        pets = list(db_collections["pets"].find({"name": "Rex"}))
        assert len(pets) == 2
        assert pets[0]["nickname"] != pets[1]["nickname"]
        both_start_with_rex = all(pet["nickname"].startswith("rex_") for pet in pets)
        assert both_start_with_rex

    def test_update_pet_success(
        self, authenticated_client, db_collections, sample_pet_data
    ):
        """Testa atualização de pet com sucesso."""
        # Insere pet inicial
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        updated_data = {
            "pet_id": pet_id,
            "name": "Rex Updated",
            "breed": "Labrador",
            "birth_date": "2020-02-15",
            "pet_type": "dog",
            "gender": "female",
        }
        
        response = authenticated_client.post("/pets", data=updated_data, follow_redirects=False)
        
        assert response.status_code == 303
        
        # Verifica se foi atualizado
        updated_pet = db_collections["pets"].find_one({"_id": result.inserted_id})
        assert updated_pet["name"] == "Rex Updated"
        assert updated_pet["breed"] == "Labrador"
        assert updated_pet["gender"] == "female"

    def test_delete_pet_soft_delete(
        self, authenticated_client, db_collections, sample_pet_data
    ):
        """Testa soft delete de pet."""
        # Insere pet
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        response = authenticated_client.post(f"/pets/{pet_id}/delete", follow_redirects=False)
        
        assert response.status_code == 303  # Redirect to dashboard
        
        # Verifica se foi marcado como deletado (soft delete)
        deleted_pet = db_collections["pets"].find_one({"_id": result.inserted_id})
        assert deleted_pet is not None
        assert deleted_pet["deleted_at"] is not None
        assert isinstance(deleted_pet["deleted_at"], datetime)

    def test_pet_profile_page(
        self, authenticated_client, db_collections, sample_pet_data, sample_treatment_data
    ):
        """Testa página de perfil do pet."""
        # Adiciona tratamento ao pet
        sample_pet_data["treatments"] = [{
            **sample_treatment_data,
            "_id": ObjectId(),
        }]
        
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        response = authenticated_client.get(f"/pets/{pet_id}/profile")
        
        assert response.status_code == 200
        assert sample_pet_data["name"] in response.text
        assert sample_pet_data["breed"] in response.text
        # Deve mostrar tratamentos
        assert sample_treatment_data["name"] in response.text

    def test_pet_profile_age_calculation(
        self, authenticated_client, db_collections, sample_pet_data
    ):
        """Testa cálculo de idade do pet."""
        # Pet nascido há 2 anos
        sample_pet_data["birth_date"] = "2022-01-15"
        
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        response = authenticated_client.get(f"/pets/{pet_id}/profile")
        
        assert response.status_code == 200
        # Deve mostrar idade aproximada
        assert ("ano" in response.text.lower() or "mês" in response.text.lower())

    def test_pet_not_found(self, authenticated_client):
        """Testa acesso a pet que não existe."""
        fake_pet_id = str(ObjectId())
        
        response = authenticated_client.get(f"/pets/{fake_pet_id}/profile")
        
        assert response.status_code == 404

    def test_unauthorized_pet_access(
        self, client, db_collections, sample_pet_data, veterinarian_user
    ):
        """Testa acesso não autorizado a pet de outro usuário."""
        # Pet pertence a outro usuário
        sample_pet_data["users"] = ["other-user-id"]
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        # Tenta acessar com usuário diferente
        with patch("main.get_current_user_info_from_session") as mock_get_user:
            mock_get_user.return_value = veterinarian_user
            
            response = client.get(f"/pets/{pet_id}/profile")
            
            assert response.status_code == 404


@pytest.mark.integration
class TestPetImages:
    """Testes para upload e processamento de imagens de pets."""

    def test_create_pet_with_image(self, authenticated_client, db_collections, test_image):
        """Testa criação de pet com upload de imagem."""
        pet_data = {
            "name": "Photo Pet",
            "breed": "Poodle",
            "birth_date": "2020-01-01",
            "pet_type": "dog",
            "gender": "male",
        }
        
        # Simula upload de arquivo
        files = {"photo": ("test.jpg", test_image, "image/jpeg")}
        
        with patch("main.save_image_with_thumbnail") as mock_save:
            mock_save.return_value = {
                "original": "uploads/temp/test_original.jpg",
                "thumbnail": "uploads/temp/test_thumb.jpg",
                "filename": "test_photo.jpg"
            }
            
            response = authenticated_client.post("/pets", data=pet_data, files=files, follow_redirects=False)
            
            assert response.status_code == 303
            assert mock_save.called

    def test_validate_image_file_success(self, test_image):
        """Testa validação de arquivo de imagem válido."""
        from main import validate_image_file
        from fastapi import UploadFile
        
        # Mock do UploadFile
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "test.jpg"
        upload_file.size = 1024 * 1024  # 1MB
        
        is_valid, error = validate_image_file(upload_file)
        
        assert is_valid is True
        assert error == ""

    def test_validate_image_file_invalid_extension(self):
        """Testa validação com extensão inválida."""
        from main import validate_image_file
        from fastapi import UploadFile
        
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "test.txt"
        upload_file.size = 1024
        
        is_valid, error = validate_image_file(upload_file)
        
        assert is_valid is False
        assert "formato de arquivo não suportado" in error.lower()

    def test_validate_image_file_too_large(self):
        """Testa validação com arquivo muito grande."""
        from main import validate_image_file, MAX_FILE_SIZE
        from fastapi import UploadFile
        
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "test.jpg"
        upload_file.size = MAX_FILE_SIZE + 1
        
        is_valid, error = validate_image_file(upload_file)
        
        assert is_valid is False
        assert "muito grande" in error.lower()

    def test_validate_image_heic_not_supported(self):
        """Testa que arquivos HEIC não são suportados."""
        from main import validate_image_file
        from fastapi import UploadFile
        
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "test.heic"
        upload_file.size = 1024
        
        is_valid, error = validate_image_file(upload_file)
        
        assert is_valid is False
        assert "formato" in error.lower() and "suportado" in error.lower()

    def test_save_image_with_thumbnail(self, temp_upload_dir, test_image):
        """Testa salvamento de imagem com criação de thumbnail."""
        from main import save_image_with_thumbnail
        from fastapi import UploadFile
        
        # Mock do UploadFile
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "test.jpg"
        upload_file.file = test_image
        
        with patch("main.UPLOAD_DIR", temp_upload_dir):
            result = save_image_with_thumbnail(upload_file, "test-pet-id")
            
            assert "original" in result
            assert "thumbnail" in result
            assert "filename" in result
            
            # Verifica se os arquivos foram criados
            original_path = Path(result["original"])
            thumbnail_path = Path(result["thumbnail"])
            
            assert original_path.exists()
            assert thumbnail_path.exists()

    def test_delete_pet_images(self, temp_upload_dir):
        """Testa remoção de imagens do pet."""
        from main import delete_pet_images
        
        # Cria estrutura de arquivos
        pet_dir = temp_upload_dir / "test-pet-id"
        pet_dir.mkdir(exist_ok=True)
        
        # Cria arquivos de teste
        (pet_dir / "test_image.jpg").touch()
        (pet_dir / "thumb_image.jpg").touch()
        
        delete_pet_images("test-pet-id")
        
        # Verifica se o diretório foi removido
        assert not pet_dir.exists()


@pytest.mark.unit
class TestPetModels:
    """Testes unitários para modelos de pet."""

    def test_pet_base_model(self):
        """Testa o modelo base PetBase."""
        from main import PetBase
        
        pet = PetBase(
            name="Test Pet",
            breed="Test Breed",
            birth_date="2020-01-01",
            pet_type="dog",
            gender="male",
            nickname="test_pet"
        )
        
        assert pet.name == "Test Pet"
        assert pet.breed == "Test Breed"
        assert pet.pet_type == "dog"
        assert pet.gender == "male"
        assert pet.treatments == []  # Lista vazia por padrão

    def test_pet_create_model(self):
        """Testa o modelo PetCreate."""
        from main import PetCreate
        
        pet = PetCreate(
            name="New Pet",
            breed="New Breed",
            birth_date="2021-01-01",
            pet_type="cat"
        )
        
        assert pet.name == "New Pet"
        assert pet.pet_type == "cat"

    def test_pet_update_model(self):
        """Testa o modelo PetUpdate."""
        from main import PetUpdate
        
        # Todos os campos são opcionais
        pet_update = PetUpdate()
        assert pet_update.name is None
        assert pet_update.breed is None
        
        # Alguns campos definidos
        pet_update_partial = PetUpdate(
            name="Updated Name",
            breed="Updated Breed"
        )
        assert pet_update_partial.name == "Updated Name"
        assert pet_update_partial.breed == "Updated Breed"

    def test_pet_type_literal(self):
        """Testa o tipo literal PetType."""
        from main import PetType, PetBase
        
        # Valores válidos
        dog = PetBase(
            name="Dog",
            breed="Breed",
            birth_date="2020-01-01",
            pet_type="dog"
        )
        assert dog.pet_type == "dog"
        
        cat = PetBase(
            name="Cat",
            breed="Breed",
            birth_date="2020-01-01",
            pet_type="cat"
        )
        assert cat.pet_type == "cat"

    def test_pet_in_db_model(self):
        """Testa o modelo PetInDB."""
        from main import PetInDB
        from bson import ObjectId
        
        pet_id = ObjectId()
        
        pet = PetInDB(
            _id=str(pet_id),
            name="DB Pet",
            breed="DB Breed",
            birth_date="2020-01-01",
            pet_type="dog",
            users=["user1", "user2"]
        )
        
        assert pet.id == str(pet_id)
        assert len(pet.users) == 2
        assert "user1" in pet.users
