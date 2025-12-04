"""
Service para regras de negócio relacionadas a pets
"""

import random
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker
from faker_food import FoodProvider
from app.repositories import PetRepository, UserRepository

logger = logging.getLogger(__name__)

# Inicializa Faker e adiciona provedor de alimentos
fake = Faker("pt_BR")
fake.add_provider(FoodProvider)


class PetService:
    """Serviço para regras de negócio relacionadas a pets"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.pet_repo = PetRepository(session)
        self.user_repo = UserRepository(session)
    
    async def get_user_pets(self, user_id: str) -> List[Dict[str, Any]]:
        """Busca pets do usuário"""
        return await self.pet_repo.get_pets_by_user(user_id)
    
    async def get_pet_details(self, pet_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca detalhes de um pet específico"""
        return await self.pet_repo.get_pet_by_id(pet_id, user_id)
    
    async def search_pet_by_nickname(
        self,
        nickname: str,
        requesting_user_id: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Busca pet por nickname e verifica acesso do usuário
        Retorna: (sucesso, pet_data, mensagem)
        """
        pet = await self.pet_repo.get_pet_by_nickname(nickname)
        
        if not pet:
            return False, None, "Pet não encontrado."
        
        # Verifica se o usuário tem acesso
        has_access = requesting_user_id in pet.get("users", [])
        
        if not has_access:
            # Remove informações detalhadas se não tem acesso
            limited_pet = {
                "_id": pet["_id"],
                "name": pet.get("name"),
                "nickname": pet.get("nickname"),
                "breed": pet.get("breed"),
                "pet_type": pet.get("pet_type"),
                "gender": pet.get("gender"),
                "birth_date": pet.get("birth_date"),
                "has_access": False,
                "message": "Você não tem acesso ao histórico completo deste pet.",
            }
            return True, limited_pet, "Pet encontrado, mas acesso limitado."
        else:
            pet["has_access"] = True
            return True, pet, "Pet encontrado com acesso completo."
    
    async def create_pet(
        self,
        pet_data: Dict[str, Any],
        user_id: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Cria um novo pet
        Retorna: (sucesso, mensagem, pet_id)
        """
        # Gera nickname único
        base_name = pet_data["name"].split()[0].lower()
        nickname = await self._generate_unique_nickname(base_name)
        
        # Prepara dados do pet
        pet_document = {
            "name": pet_data["name"],
            "breed": pet_data["breed"],
            "pedigree_number": pet_data.get("pedigree_number"),
            "birth_date": pet_data["birth_date"],
            "pet_type": pet_data["pet_type"],
            "gender": pet_data.get("gender"),
            "users": [user_id],
            "treatments": [],
            "deleted_at": None,
            "nickname": nickname,
        }
        
        # Adiciona foto se fornecida
        if "photo" in pet_data:
            pet_document["photo"] = pet_data["photo"]
        
        try:
            pet_id = await self.pet_repo.create_pet(pet_document)
            return True, "Pet criado com sucesso!", pet_id
        except Exception as e:
            return False, f"Erro ao criar pet: {str(e)}", None
    
    async def update_pet(
        self,
        pet_id: str,
        pet_data: Dict[str, Any],
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Atualiza dados de um pet
        Retorna: (sucesso, mensagem)
        """
        try:
            logger.info(f"Attempting to update pet: pet_id={pet_id}, user_id={user_id}")
            success = await self.pet_repo.update_pet(pet_id, user_id, pet_data)
            if success:
                return True, "Pet atualizado com sucesso!"
            else:
                logger.warning(f"Failed to update pet: pet_id={pet_id}, user_id={user_id}")
                return False, "Pet não encontrado ou sem permissão para editar."
        except Exception as e:
            logger.error(f"Error updating pet: {str(e)}", exc_info=True)
            return False, f"Erro ao atualizar pet: {str(e)}"
    
    async def delete_pet(self, pet_id: str, user_id: str) -> Tuple[bool, str]:
        """
        Remove um pet (soft delete)
        Retorna: (sucesso, mensagem)
        """
        try:
            success = await self.pet_repo.soft_delete_pet(pet_id, user_id)
            if success:
                return True, "Pet removido com sucesso!"
            else:
                return False, "Pet não encontrado ou sem permissão para excluir."
        except Exception as e:
            return False, f"Erro ao remover pet: {str(e)}"
    
    async def grant_veterinarian_access(
        self,
        pet_id: str,
        vet_id: str,
        owner_id: str
    ) -> Tuple[bool, str]:
        """
        Concede acesso de veterinário ao pet
        Retorna: (sucesso, mensagem)
        """
        # Verifica se o pet existe e se o usuário é o dono
        pet = await self.pet_repo.get_pet_by_id(pet_id, owner_id)
        if not pet:
            return False, "Pet não encontrado ou sem permissão."
        
        # Verifica se o veterinário existe
        vet = await self.user_repo.get_veterinarian_by_id(vet_id)
        if not vet:
            return False, "Veterinário não encontrado."
        
        try:
            was_granted = await self.pet_repo.grant_vet_access(pet_id, vet_id)
            if was_granted:
                return True, f"Acesso concedido ao veterinário {vet.get('name', 'Sem nome')} com sucesso!"
            else:
                return True, "O veterinário já tinha acesso a este pet."
        except Exception as e:
            return False, f"Erro ao conceder acesso: {str(e)}"
    
    async def revoke_veterinarian_access(
        self,
        pet_id: str,
        vet_id: str,
        owner_id: str
    ) -> Tuple[bool, str]:
        """
        Remove acesso de veterinário ao pet
        Retorna: (sucesso, mensagem)
        """
        # Verifica se o pet existe e se o usuário é o dono
        pet = await self.pet_repo.get_pet_by_id(pet_id, owner_id)
        if not pet:
            return False, "Pet não encontrado ou sem permissão."
        
        # Não permite remover o próprio dono
        if vet_id == owner_id:
            return False, "Você não pode remover seu próprio acesso."
        
        try:
            was_revoked = await self.pet_repo.revoke_vet_access(pet_id, vet_id)
            if was_revoked:
                return True, "Acesso do veterinário removido com sucesso!"
            else:
                return False, "Veterinário não tinha acesso a este pet."
        except Exception as e:
            return False, f"Erro ao remover acesso: {str(e)}"
    
    async def get_pet_veterinarians(
        self,
        pet_id: str,
        owner_id: str
    ) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Lista veterinários que têm acesso ao pet
        Retorna: (sucesso, lista_veterinarios, mensagem)
        """
        # Verifica se o pet existe e se o usuário é o dono
        pet = await self.pet_repo.get_pet_by_id(pet_id, owner_id)
        if not pet:
            return False, [], "Pet não encontrado ou sem permissão."
        
        # Busca todos os veterinários que têm acesso (exceto o dono)
        veterinarian_ids = [uid for uid in pet.get("users", []) if uid != owner_id]
        
        if not veterinarian_ids:
            return True, [], "Nenhum veterinário tem acesso a este pet."
        
        try:
            veterinarians = await self.user_repo.get_veterinarians_by_ids(veterinarian_ids)
            
            # Formata dados dos veterinários
            formatted_vets = []
            for vet in veterinarians:
                formatted_vets.append({
                    "id": str(vet["_id"]),
                    "name": vet.get("name", "Sem nome"),
                    "email": vet.get("email", ""),
                })
            
            return True, formatted_vets, "Veterinários listados com sucesso."
        except Exception as e:
            return False, [], f"Erro ao buscar veterinários: {str(e)}"
    
    async def add_treatment(
        self,
        pet_id: str,
        user_id: str,
        treatment_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Adiciona tratamento ao pet
        Retorna: (sucesso, mensagem)
        """
        # Se o usuário logado é um veterinário e applier_type é "Veterinarian",
        # adiciona automaticamente o veterinário à lista de usuários do pet
        if treatment_data.get("applier_type") == "Veterinarian":
            await self.pet_repo.grant_vet_access(pet_id, user_id)
        
        try:
            success = await self.pet_repo.add_treatment(pet_id, user_id, treatment_data)
            if success:
                return True, "Tratamento adicionado com sucesso!"
            else:
                return False, "Pet não encontrado ou sem permissão."
        except Exception as e:
            return False, f"Erro ao adicionar tratamento: {str(e)}"
    
    async def update_treatment(
        self,
        pet_id: str,
        treatment_id: str,
        user_id: str,
        treatment_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Atualiza tratamento do pet
        Retorna: (sucesso, mensagem)
        """
        try:
            success = await self.pet_repo.update_treatment(
                pet_id, user_id, treatment_id, treatment_data
            )
            if success:
                return True, "Tratamento atualizado com sucesso!"
            else:
                return False, "Tratamento não encontrado ou sem permissão."
        except Exception as e:
            return False, f"Erro ao atualizar tratamento: {str(e)}"
    
    async def delete_treatment(
        self,
        pet_id: str,
        treatment_id: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Remove tratamento do pet
        Retorna: (sucesso, mensagem)
        """
        try:
            success = await self.pet_repo.delete_treatment(pet_id, user_id, treatment_id)
            if success:
                return True, "Tratamento removido com sucesso!"
            else:
                return False, "Tratamento não encontrado ou sem permissão."
        except Exception as e:
            return False, f"Erro ao remover tratamento: {str(e)}"
    
    def generate_pet_names(self, gender: str) -> Dict[str, List[str]]:
        """
        Gera uma lista de nomes de pet ou comidas baseada no gênero.
        """
        if gender not in ["male", "female"]:
            return {"names": ["Selecione um gênero válido."]}

        nomes_comuns_unissex = ["Pingo", "Bolinha", "Mel", "Pipoca", "Amora", "Jade", "Max"]
        nomes = []

        # 50% de chance de gerar nomes de pet ou de comida
        if random.choice([True, False]):
            # Nomes de pet
            if gender == "male":
                nomes.extend([fake.first_name_male() for _ in range(5)])
            else:
                nomes.extend([fake.first_name_female() for _ in range(5)])

            # Adiciona alguns nomes unissex
            nomes.extend(random.sample(nomes_comuns_unissex, 5))
        else:
            # Nomes de comida
            nomes.extend([fake.dish() for _ in range(10)])

        # Remove duplicatas e retorna a lista
        return {"names": list(set(nomes))}
    
    async def _generate_unique_nickname(self, base_name: str) -> str:
        """Gera um nickname único para o pet"""
        attempts = 0
        max_attempts = 100

        while attempts < max_attempts:
            random_code = "".join(random.choices("0123456789", k=4))
            candidate_nickname = f"{base_name}_{random_code}"

            # Verifica se o nickname já existe
            if not await self.pet_repo.check_nickname_exists(candidate_nickname):
                return candidate_nickname
            
            attempts += 1

        # Se não conseguiu gerar um nickname único, usa timestamp
        import time
        timestamp = str(int(time.time()))[-6:]  # Últimos 6 dígitos do timestamp
        return f"{base_name}_{timestamp}"
