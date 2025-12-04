"""
Repository para operações com pets usando SQLAlchemy
"""

import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.models.pet import Pet
from app.database.models.pet_owner import PetOwner
from app.database.models.treatment import Treatment
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PetRepository(BaseRepository[Pet]):
    """Repository para operações com pets"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Pet, session)
    
    async def get_pets_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Busca pets de um usuário (não deletados)"""
        query = (
            select(Pet)
            .join(PetOwner)
            .where(
                PetOwner.profile_id == user_id,
                PetOwner.deleted_at == None,  # noqa: E711
                Pet.deleted_at == None  # noqa: E711
            )
            .options(
                selectinload(Pet.owners),
                selectinload(Pet.treatments)
            )
        )
        
        result = await self.session.execute(query)
        pets = result.unique().scalars().all()
        return [pet.to_dict() for pet in pets]
    
    async def get_pet_by_id(self, pet_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca pet por ID (verificando acesso do usuário)"""
        try:
            query = (
                select(Pet)
                .join(PetOwner)
                .where(
                    Pet.id == pet_id,
                    PetOwner.profile_id == user_id,
                    PetOwner.deleted_at == None,  # noqa: E711
                    Pet.deleted_at == None  # noqa: E711
                )
                .options(
                    selectinload(Pet.owners),
                    selectinload(Pet.treatments)
                )
            )
            
            result = await self.session.execute(query)
            pet = result.unique().scalar_one_or_none()
            return pet.to_dict() if pet else None
        except Exception as e:
            logger.error(f"Error fetching pet by id: {e}")
            return None
    
    async def get_pet_by_nickname(self, nickname: str) -> Optional[Dict[str, Any]]:
        """Busca pet por nickname"""
        query = (
            select(Pet)
            .where(
                Pet.nickname == nickname,
                Pet.deleted_at == None  # noqa: E711
            )
            .options(
                selectinload(Pet.owners),
                selectinload(Pet.treatments)
            )
        )
        
        result = await self.session.execute(query)
        pet = result.unique().scalar_one_or_none()
        return pet.to_dict() if pet else None
    
    async def create_pet(self, pet_data: Dict[str, Any]) -> str:
        """Cria um novo pet"""
        users = pet_data.pop("users", [])
        pet_data.pop("treatments", None)
        pet_data.pop("deleted_at", None)
        
        # Gerar ID único
        pet_id = str(uuid.uuid4())
        pet_data["id"] = pet_id
        
        pet = Pet(**pet_data)
        self.session.add(pet)
        await self.session.flush()
        
        # Adicionar owners
        for user_id in users:
            owner = PetOwner(pet_id=pet_id, profile_id=user_id)
            self.session.add(owner)
        
        await self.session.flush()
        return pet_id
    
    async def update_pet(self, pet_id: str, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Atualiza um pet"""
        try:
            # Verificar acesso
            query = (
                select(Pet)
                .join(PetOwner)
                .where(
                    Pet.id == pet_id,
                    PetOwner.profile_id == user_id,
                    PetOwner.deleted_at == None,  # noqa: E711
                    Pet.deleted_at == None  # noqa: E711
                )
            )
            
            result = await self.session.execute(query)
            pet = result.scalar_one_or_none()
            
            if not pet:
                return False
            
            # Remover campos que não devem ser atualizados
            update_data.pop("_id", None)
            update_data.pop("users", None)
            update_data.pop("treatments", None)
            update_data.pop("deleted_at", None)
            
            for key, value in update_data.items():
                if hasattr(pet, key):
                    setattr(pet, key, value)
            
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error updating pet: {e}")
            return False
    
    async def soft_delete_pet(self, pet_id: str, user_id: str) -> bool:
        """Faz soft delete do pet"""
        try:
            query = (
                select(Pet)
                .join(PetOwner)
                .where(
                    Pet.id == pet_id,
                    PetOwner.profile_id == user_id,
                    PetOwner.deleted_at == None,  # noqa: E711
                    Pet.deleted_at == None  # noqa: E711
                )
            )
            
            result = await self.session.execute(query)
            pet = result.scalar_one_or_none()
            
            if not pet:
                return False
            
            pet.soft_delete()
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error soft deleting pet: {e}")
            return False
    
    async def check_nickname_exists(self, nickname: str) -> bool:
        """Verifica se nickname já existe"""
        query = select(Pet).where(Pet.nickname == nickname)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def grant_vet_access(self, pet_id: str, vet_id: str) -> bool:
        """Concede acesso de veterinário ao pet"""
        try:
            # Verificar se já tem acesso
            query = (
                select(PetOwner)
                .where(
                    PetOwner.pet_id == pet_id,
                    PetOwner.profile_id == vet_id
                )
            )
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                if existing.deleted_at:
                    existing.restore()
                    await self.session.flush()
                    return True
                return False  # Já tem acesso
            
            # Criar novo acesso
            owner = PetOwner(pet_id=pet_id, profile_id=vet_id)
            self.session.add(owner)
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error granting vet access: {e}")
            return False
    
    async def revoke_vet_access(self, pet_id: str, vet_id: str) -> bool:
        """Remove acesso de veterinário ao pet"""
        try:
            query = (
                select(PetOwner)
                .where(
                    PetOwner.pet_id == pet_id,
                    PetOwner.profile_id == vet_id,
                    PetOwner.deleted_at == None  # noqa: E711
                )
            )
            
            result = await self.session.execute(query)
            owner = result.scalar_one_or_none()
            
            if not owner:
                return False
            
            owner.soft_delete()
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error revoking vet access: {e}")
            return False
    
    async def add_treatment(self, pet_id: str, user_id: str, treatment_data: Dict[str, Any]) -> bool:
        """Adiciona tratamento ao pet"""
        try:
            # Verificar acesso
            query = (
                select(Pet)
                .join(PetOwner)
                .where(
                    Pet.id == pet_id,
                    PetOwner.profile_id == user_id,
                    PetOwner.deleted_at == None,  # noqa: E711
                    Pet.deleted_at == None  # noqa: E711
                )
            )
            
            result = await self.session.execute(query)
            pet = result.scalar_one_or_none()
            
            if not pet:
                return False
            
            # Criar tratamento
            treatment_id = str(uuid.uuid4())
            treatment = Treatment(
                id=treatment_id,
                pet_id=pet_id,
                category=treatment_data.get("category"),
                name=treatment_data.get("name"),
                description=treatment_data.get("description"),
                date=treatment_data.get("date"),
                time=treatment_data.get("time"),
                done=treatment_data.get("done", False),
                applier_type=treatment_data.get("applier_type"),
                applier_name=treatment_data.get("applier_name"),
                applier_id=treatment_data.get("applier_id"),
            )
            
            self.session.add(treatment)
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error adding treatment: {e}")
            return False
    
    async def update_treatment(
        self,
        pet_id: str,
        user_id: str,
        treatment_id: str,
        treatment_data: Dict[str, Any]
    ) -> bool:
        """Atualiza tratamento do pet"""
        try:
            # Verificar acesso
            query = (
                select(Treatment)
                .join(Pet)
                .join(PetOwner)
                .where(
                    Treatment.id == treatment_id,
                    Treatment.pet_id == pet_id,
                    PetOwner.profile_id == user_id,
                    PetOwner.deleted_at == None,  # noqa: E711
                    Pet.deleted_at == None  # noqa: E711
                )
            )
            
            result = await self.session.execute(query)
            treatment = result.scalar_one_or_none()
            
            if not treatment:
                return False
            
            # Atualizar campos
            for key, value in treatment_data.items():
                if key != "_id" and hasattr(treatment, key):
                    setattr(treatment, key, value)
            
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error updating treatment: {e}")
            return False
    
    async def delete_treatment(self, pet_id: str, user_id: str, treatment_id: str) -> bool:
        """Remove tratamento do pet"""
        try:
            # Verificar acesso
            query = (
                select(Treatment)
                .join(Pet)
                .join(PetOwner)
                .where(
                    Treatment.id == treatment_id,
                    Treatment.pet_id == pet_id,
                    PetOwner.profile_id == user_id,
                    PetOwner.deleted_at == None,  # noqa: E711
                    Pet.deleted_at == None  # noqa: E711
                )
            )
            
            result = await self.session.execute(query)
            treatment = result.scalar_one_or_none()
            
            if not treatment:
                return False
            
            await self.session.delete(treatment)
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error deleting treatment: {e}")
            return False
    
    async def get_scheduled_treatments_for_date(self, target_date: str) -> List[Dict[str, Any]]:
        """
        Busca todos os tratamentos agendados para uma data específica
        target_date: data no formato "YYYY-MM-DD"
        """
        try:
            query = (
                select(Pet)
                .join(Treatment)
                .where(
                    Pet.deleted_at == None,  # noqa: E711
                    Treatment.date == target_date,
                    Treatment.done == False  # noqa: E712
                )
                .options(
                    selectinload(Pet.owners),
                    selectinload(Pet.treatments)
                )
            )
            
            result = await self.session.execute(query)
            pets = result.unique().scalars().all()
            
            results = []
            for pet in pets:
                pet_dict = {
                    "_id": pet.id,
                    "name": pet.name,
                    "nickname": pet.nickname,
                    "users": [owner.profile_id for owner in pet.owners if not owner.deleted_at],
                    "treatments": [
                        t.to_dict() for t in pet.treatments
                        if t.date == target_date and not t.done
                    ]
                }
                results.append(pet_dict)
            
            return results
        except Exception as e:
            logger.error(f"Error fetching scheduled treatments: {e}")
            return []
    
    async def get_tomorrow_scheduled_treatments(self) -> List[Dict[str, Any]]:
        """Busca todos os tratamentos agendados para amanhã"""
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")
        return await self.get_scheduled_treatments_for_date(tomorrow_str)
    
    async def get_current_month_treatments(self) -> List[Dict[str, Any]]:
        """Busca todos os tratamentos agendados para o mês atual"""
        try:
            now = datetime.now()
            first_day = now.replace(day=1).strftime("%Y-%m-%d")
            if now.month == 12:
                last_day = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
            last_day_str = last_day.strftime("%Y-%m-%d")
            
            query = (
                select(Pet)
                .join(Treatment)
                .where(
                    Pet.deleted_at == None,  # noqa: E711
                    Treatment.date >= first_day,
                    Treatment.date <= last_day_str,
                    Treatment.done == False  # noqa: E712
                )
                .options(
                    selectinload(Pet.owners),
                    selectinload(Pet.treatments)
                )
            )
            
            result = await self.session.execute(query)
            pets = result.unique().scalars().all()
            
            results = []
            for pet in pets:
                pet_dict = {
                    "_id": pet.id,
                    "name": pet.name,
                    "nickname": pet.nickname,
                    "users": [owner.profile_id for owner in pet.owners if not owner.deleted_at],
                    "treatments": [
                        t.to_dict() for t in pet.treatments
                        if first_day <= t.date <= last_day_str and not t.done
                    ]
                }
                if pet_dict["treatments"]:
                    results.append(pet_dict)
            
            return results
        except Exception as e:
            logger.error(f"Error fetching current month treatments: {e}")
            return []
    
    async def get_expired_treatments(self) -> List[Dict[str, Any]]:
        """Busca todos os tratamentos expirados"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            query = (
                select(Pet)
                .join(Treatment)
                .where(
                    Pet.deleted_at == None,  # noqa: E711
                    Treatment.date < today,
                    Treatment.done == False  # noqa: E712
                )
                .options(
                    selectinload(Pet.owners),
                    selectinload(Pet.treatments)
                )
            )
            
            result = await self.session.execute(query)
            pets = result.unique().scalars().all()
            
            results = []
            for pet in pets:
                pet_dict = {
                    "_id": pet.id,
                    "name": pet.name,
                    "nickname": pet.nickname,
                    "users": [owner.profile_id for owner in pet.owners if not owner.deleted_at],
                    "treatments": [
                        t.to_dict() for t in pet.treatments
                        if t.date < today and not t.done
                    ]
                }
                if pet_dict["treatments"]:
                    results.append(pet_dict)
            
            return results
        except Exception as e:
            logger.error(f"Error fetching expired treatments: {e}")
            return []

