"""Testes para funcionalidades de gestão de tratamentos."""

import pytest
from bson import ObjectId
from datetime import datetime


@pytest.mark.integration
class TestTreatmentCRUD:
    """Testes para operações CRUD de tratamentos."""

    def test_add_treatment_page(
        self, authenticated_client, db_collections, sample_pet_data
    ):
        """Testa página para adicionar tratamento."""
        # Insere pet no banco
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        response = authenticated_client.get(f"/pets/{pet_id}/treatments/add")
        
        assert response.status_code == 200
        assert sample_pet_data["name"] in response.text
        # Deve ter campos do formulário
        assert "category" in response.text.lower()
        assert "name" in response.text.lower()

    def test_create_treatment_success(
        self, authenticated_client, db_collections, sample_pet_data
    ):
        """Testa criação de tratamento com sucesso."""
        # Insere pet
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        treatment_data = {
            "category": "Vacinas",
            "name": "V10",
            "description": "Vacina décupla",
            "date": "2024-12-15",
            "time": "10:30",
            "applier_type": "Veterinarian",
            "applier_name": "Dr. Test",
            "applier_id": "auth0|vet-user-id",
            "done": False,
        }
        
        response = authenticated_client.post(
            f"/pets/{pet_id}/treatments", data=treatment_data, follow_redirects=False
        )
        
        assert response.status_code == 303  # Redirect
        assert f"/pets/{pet_id}/profile" in response.headers["location"]
        
        # Verifica se foi salvo no banco
        updated_pet = db_collections["pets"].find_one({"_id": result.inserted_id})
        assert len(updated_pet["treatments"]) == 1
        
        treatment = updated_pet["treatments"][0]
        assert treatment["name"] == "V10"
        assert treatment["category"] == "Vacinas"
        assert treatment["done"] is False

    def test_update_treatment_success(
        self, authenticated_client, db_collections, sample_pet_data, sample_treatment_data
    ):
        """Testa atualização de tratamento existente."""
        # Adiciona tratamento ao pet
        treatment_id = ObjectId()
        sample_treatment_data["_id"] = treatment_id
        sample_pet_data["treatments"] = [sample_treatment_data]
        
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        updated_treatment_data = {
            "treatment_id": str(treatment_id),
            "category": "Ectoparasitas",
            "name": "Antipulgas Updated",
            "description": "Descrição atualizada",
            "date": "2024-12-20",
            "time": "15:00",
            "applier_type": "Tutor",
            "done": True,
        }
        
        response = authenticated_client.post(
            f"/pets/{pet_id}/treatments", data=updated_treatment_data, follow_redirects=False
        )
        
        assert response.status_code == 303
        
        # Verifica se foi atualizado
        updated_pet = db_collections["pets"].find_one({"_id": result.inserted_id})
        treatment = updated_pet["treatments"][0]
        assert treatment["name"] == "Antipulgas Updated"
        assert treatment["category"] == "Ectoparasitas"
        assert treatment["done"] is True

    def test_edit_treatment_page(
        self, authenticated_client, db_collections, sample_pet_data, sample_treatment_data
    ):
        """Testa página de edição de tratamento."""
        treatment_id = ObjectId()
        sample_treatment_data["_id"] = treatment_id
        sample_pet_data["treatments"] = [sample_treatment_data]
        
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        response = authenticated_client.get(
            f"/pets/{pet_id}/treatments/{str(treatment_id)}/edit"
        )
        
        assert response.status_code == 200
        assert sample_treatment_data["name"] in response.text
        assert sample_treatment_data["category"] in response.text

    def test_delete_treatment_success(
        self, authenticated_client, db_collections, sample_pet_data, sample_treatment_data
    ):
        """Testa remoção de tratamento."""
        treatment_id = ObjectId()
        sample_treatment_data["_id"] = treatment_id
        sample_pet_data["treatments"] = [sample_treatment_data]
        
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        response = authenticated_client.post(
            f"/pets/{pet_id}/treatments/{str(treatment_id)}/delete", follow_redirects=False
        )
        
        assert response.status_code == 303
        
        # Verifica se foi removido
        updated_pet = db_collections["pets"].find_one({"_id": result.inserted_id})
        assert len(updated_pet["treatments"]) == 0

    def test_treatment_not_found(
        self, authenticated_client, db_collections, sample_pet_data
    ):
        """Testa tentativa de editar tratamento inexistente."""
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        fake_treatment_id = str(ObjectId())
        
        response = authenticated_client.get(
            f"/pets/{pet_id}/treatments/{fake_treatment_id}/edit"
        )
        
        assert response.status_code == 404

    def test_treatment_unauthorized_pet(
        self, authenticated_client, db_collections, sample_pet_data, sample_treatment_data
    ):
        """Testa acesso a tratamento de pet não autorizado."""
        # Pet de outro usuário
        sample_pet_data["users"] = ["other-user-id"]
        treatment_id = ObjectId()
        sample_treatment_data["_id"] = treatment_id
        sample_pet_data["treatments"] = [sample_treatment_data]
        
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        response = authenticated_client.get(
            f"/pets/{pet_id}/treatments/{str(treatment_id)}/edit"
        )
        
        assert response.status_code == 404

    def test_veterinarian_adds_treatment_gets_access(
        self, vet_client, db_collections, sample_pet_data, veterinarian_user
    ):
        """Testa que veterinário ganha acesso ao pet ao adicionar tratamento."""
        # Pet inicialmente sem o veterinário
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        treatment_data = {
            "category": "Vacinas",
            "name": "Raiva",
            "date": "2024-12-01",
            "applier_type": "Veterinarian",
            "applier_name": veterinarian_user["info"]["name"],
            "applier_id": veterinarian_user["id"],
        }
        
        response = vet_client.post(f"/pets/{pet_id}/treatments", data=treatment_data, follow_redirects=False)
        
        assert response.status_code == 303
        
        # Verifica se o veterinário foi adicionado aos usuários do pet
        updated_pet = db_collections["pets"].find_one({"_id": result.inserted_id})
        assert veterinarian_user["id"] in updated_pet["users"]

    def test_treatment_categories(self, authenticated_client, db_collections, sample_pet_data):
        """Testa diferentes categorias de tratamento."""
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        categories = ["Vacinas", "Ectoparasitas", "Vermífugo", "Tratamentos"]
        
        for category in categories:
            treatment_data = {
                "category": category,
                "name": f"Tratamento {category}",
                "date": "2024-12-01",
                "applier_type": "Tutor",
            }
            
            response = authenticated_client.post(
                f"/pets/{pet_id}/treatments", data=treatment_data, follow_redirects=False
            )
            
            assert response.status_code == 303
        
        # Verifica se todos foram salvos
        updated_pet = db_collections["pets"].find_one({"_id": result.inserted_id})
        assert len(updated_pet["treatments"]) == len(categories)
        
        saved_categories = [t["category"] for t in updated_pet["treatments"]]
        for category in categories:
            assert category in saved_categories

    def test_treatment_applier_types(self, authenticated_client, db_collections, sample_pet_data):
        """Testa diferentes tipos de aplicador."""
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        # Tratamento por veterinário
        vet_treatment = {
            "category": "Vacinas",
            "name": "Tratamento Vet",
            "date": "2024-12-01",
            "applier_type": "Veterinarian",
            "applier_name": "Dr. Test",
            "applier_id": "vet-123",
        }
        
        response = authenticated_client.post(
            f"/pets/{pet_id}/treatments", data=vet_treatment, follow_redirects=False
        )
        assert response.status_code == 303
        
        # Tratamento por tutor
        tutor_treatment = {
            "category": "Vermífugo",
            "name": "Tratamento Tutor",
            "date": "2024-12-02",
            "applier_type": "Tutor",
        }
        
        response = authenticated_client.post(
            f"/pets/{pet_id}/treatments", data=tutor_treatment, follow_redirects=False
        )
        assert response.status_code == 303
        
        # Verifica ambos
        updated_pet = db_collections["pets"].find_one({"_id": result.inserted_id})
        applier_types = [t["applier_type"] for t in updated_pet["treatments"]]
        assert "Veterinarian" in applier_types
        assert "Tutor" in applier_types


@pytest.mark.unit
class TestTreatmentModels:
    """Testes unitários para modelos de tratamento."""

    def test_treatment_model_complete(self):
        """Testa modelo Treatment completo."""
        from main import Treatment
        from bson import ObjectId
        
        treatment_id = ObjectId()
        
        treatment = Treatment(
            _id=str(treatment_id),
            category="Vacinas",
            name="V8",
            description="Vacina óctupla",
            date="2024-12-01",
            time="14:30",
            applier_type="Veterinarian",
            applier_name="Dr. Test",
            applier_id="vet-123",
            done=True
        )
        
        assert treatment.id == str(treatment_id)
        assert treatment.category == "Vacinas"
        assert treatment.name == "V8"
        assert treatment.applier_type == "Veterinarian"
        assert treatment.done is True

    def test_treatment_model_minimal(self):
        """Testa modelo Treatment com campos mínimos."""
        from main import Treatment
        from bson import ObjectId
        
        treatment = Treatment(
            _id=str(ObjectId()),
            category="Vacinas",
            name="Teste",
            date="2024-12-01",
            applier_type="Tutor"
        )
        
        assert treatment.description is None
        assert treatment.time is None
        assert treatment.applier_name is None
        assert treatment.applier_id is None
        assert treatment.done is False  # Valor padrão

    def test_treatment_category_literal(self):
        """Testa valores válidos para categoria."""
        from main import Treatment
        from bson import ObjectId
        
        valid_categories = ["Vacinas", "Ectoparasitas", "Vermífugo", "Tratamentos"]
        
        for category in valid_categories:
            treatment = Treatment(
                _id=str(ObjectId()),
                category=category,
                name="Test",
                date="2024-12-01",
                applier_type="Tutor"
            )
            assert treatment.category == category

    def test_treatment_applier_type_literal(self):
        """Testa valores válidos para tipo de aplicador."""
        from main import Treatment
        from bson import ObjectId
        
        valid_applier_types = ["Veterinarian", "Tutor"]
        
        for applier_type in valid_applier_types:
            treatment = Treatment(
                _id=str(ObjectId()),
                category="Vacinas",
                name="Test",
                date="2024-12-01",
                applier_type=applier_type
            )
            assert treatment.applier_type == applier_type

    def test_treatment_serialization(self):
        """Testa serialização do modelo Treatment."""
        from main import Treatment
        from bson import ObjectId
        
        treatment = Treatment(
            _id=str(ObjectId()),
            category="Vacinas",
            name="V8",
            description="Vacina óctupla",
            date="2024-12-01",
            time="14:30",
            applier_type="Veterinarian",
            applier_name="Dr. Test",
            done=False
        )
        
        treatment_dict = treatment.model_dump()
        
        assert "category" in treatment_dict
        assert "name" in treatment_dict
        assert "date" in treatment_dict
        assert treatment_dict["done"] is False


@pytest.mark.integration
class TestTreatmentFiltering:
    """Testes para filtragem e organização de tratamentos."""

    def test_treatment_status_separation(
        self, authenticated_client, db_collections, sample_pet_data
    ):
        """Testa separação de tratamentos por status na página de perfil."""
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        past_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Tratamentos com diferentes status
        treatments = [
            {
                "_id": ObjectId(),
                "category": "Vacinas",
                "name": "Expirado",
                "date": past_date,
                "applier_type": "Tutor",
                "done": False,
            },
            {
                "_id": ObjectId(),
                "category": "Vacinas", 
                "name": "Agendado",
                "date": future_date,
                "applier_type": "Tutor",
                "done": False,
            },
            {
                "_id": ObjectId(),
                "category": "Vacinas",
                "name": "Concluído",
                "date": past_date,
                "applier_type": "Tutor",
                "done": True,
            },
        ]
        
        sample_pet_data["treatments"] = treatments
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        response = authenticated_client.get(f"/pets/{pet_id}/profile")
        
        assert response.status_code == 200
        
        # Todos os tratamentos devem aparecer na página
        assert "Expirado" in response.text
        assert "Agendado" in response.text
        assert "Concluído" in response.text

    def test_treatment_search_filter(
        self, authenticated_client, db_collections, sample_pet_data
    ):
        """Testa filtro de busca de tratamentos."""
        treatments = [
            {
                "_id": ObjectId(),
                "category": "Vacinas",
                "name": "V8 Canina",
                "date": "2024-12-01",
                "applier_type": "Tutor",
                "done": False,
            },
            {
                "_id": ObjectId(),
                "category": "Ectoparasitas",
                "name": "Antipulgas",
                "date": "2024-12-02",
                "applier_type": "Tutor",
                "done": False,
            },
        ]
        
        sample_pet_data["treatments"] = treatments
        result = db_collections["pets"].insert_one(sample_pet_data)
        pet_id = str(result.inserted_id)
        
        # Busca por "v8" deve retornar apenas a vacina
        response = authenticated_client.get(f"/pets/{pet_id}/profile?search=v8")
        
        assert response.status_code == 200
        assert "V8 Canina" in response.text
        assert "Antipulgas" not in response.text
