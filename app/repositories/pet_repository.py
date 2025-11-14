from typing import Dict, Any, Optional, List
import logging
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timedelta
from .base_repository import BaseRepository
from ..database import database

logger = logging.getLogger(__name__)


class PetRepository(BaseRepository):
    """Repository para operações com pets"""
    
    def __init__(self):
        super().__init__(database.pets_collection)
    
    def get_pets_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Busca pets de um usuário (não deletados)"""
        pets = self.find({"users": user_id, "deleted_at": None})
        for pet in pets:
            pet["_id"] = str(pet["_id"])
            if "treatments" in pet:
                for treatment in pet["treatments"]:
                    treatment["_id"] = str(treatment["_id"])
        return pets
    
    def get_pet_by_id(self, pet_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca pet por ID (verificando acesso do usuário)"""
        try:
            if not ObjectId.is_valid(pet_id):
                logger.warning(f"Invalid ObjectId format: {pet_id}")
                return None
            
            pet = self.find_one({
                "_id": ObjectId(pet_id),
                "users": user_id,
                "deleted_at": None
            })
            if pet:
                pet["_id"] = str(pet["_id"])
                if "treatments" in pet:
                    for treatment in pet["treatments"]:
                        treatment["_id"] = str(treatment["_id"])
            return pet
        except InvalidId as e:
            logger.error(f"InvalidId error for pet_id {pet_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching pet by id: {e}")
            return None
    
    def get_pet_by_nickname(self, nickname: str) -> Optional[Dict[str, Any]]:
        """Busca pet por nickname"""
        pet = self.find_one({"nickname": nickname, "deleted_at": None})
        if pet:
            pet["_id"] = str(pet["_id"])
            if "users" in pet:
                pet["users"] = [str(uid) for uid in pet["users"]]
            if "treatments" in pet:
                for treatment in pet["treatments"]:
                    treatment["_id"] = str(treatment["_id"])
        return pet
    
    def create_pet(self, pet_data: Dict[str, Any]) -> str:
        """Cria um novo pet"""
        result = self.collection.insert_one(pet_data)
        return str(result.inserted_id)
    
    def update_pet(self, pet_id: str, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Atualiza um pet"""
        try:
            if not ObjectId.is_valid(pet_id):
                logger.warning(f"Invalid ObjectId format: {pet_id}")
                return False
            
            filter_query = {
                "_id": ObjectId(pet_id),
                "users": user_id,
                "deleted_at": None
            }
            return self.update_one(filter_query, {"$set": update_data})
        except InvalidId as e:
            logger.error(f"InvalidId error for pet_id {pet_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating pet: {e}")
            return False
    
    def soft_delete_pet(self, pet_id: str, user_id: str) -> bool:
        """Faz soft delete do pet"""
        try:
            if not ObjectId.is_valid(pet_id):
                logger.warning(f"Invalid ObjectId format: {pet_id}")
                return False
            
            filter_query = {
                "_id": ObjectId(pet_id),
                "users": user_id,
                "deleted_at": None
            }
            return self.update_one(filter_query, {"$set": {"deleted_at": datetime.now()}})
        except InvalidId as e:
            logger.error(f"InvalidId error for pet_id {pet_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error soft deleting pet: {e}")
            return False
    
    def check_nickname_exists(self, nickname: str) -> bool:
        """Verifica se nickname já existe"""
        return self.find_one({"nickname": nickname}) is not None
    
    def grant_vet_access(self, pet_id: str, vet_id: str) -> bool:
        """Concede acesso de veterinário ao pet"""
        try:
            if not ObjectId.is_valid(pet_id):
                logger.warning(f"Invalid ObjectId format: {pet_id}")
                return False
            
            result = self.collection.update_one(
                {"_id": ObjectId(pet_id)},
                {"$addToSet": {"users": vet_id}}
            )
            return result.modified_count > 0
        except InvalidId as e:
            logger.error(f"InvalidId error for pet_id {pet_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error granting vet access: {e}")
            return False
    
    def revoke_vet_access(self, pet_id: str, vet_id: str) -> bool:
        """Remove acesso de veterinário ao pet"""
        try:
            if not ObjectId.is_valid(pet_id):
                logger.warning(f"Invalid ObjectId format: {pet_id}")
                return False
            
            result = self.collection.update_one(
                {"_id": ObjectId(pet_id)},
                {"$pull": {"users": vet_id}}
            )
            return result.modified_count > 0
        except InvalidId as e:
            logger.error(f"InvalidId error for pet_id {pet_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error revoking vet access: {e}")
            return False
    
    def add_treatment(self, pet_id: str, user_id: str, treatment_data: Dict[str, Any]) -> bool:
        """Adiciona tratamento ao pet"""
        try:
            if not ObjectId.is_valid(pet_id):
                logger.warning(f"Invalid ObjectId format: {pet_id}")
                return False
            
            treatment_data["_id"] = ObjectId()
            result = self.collection.update_one(
                {
                    "_id": ObjectId(pet_id),
                    "users": user_id,
                    "deleted_at": None
                },
                {"$push": {"treatments": treatment_data}}
            )
            return result.matched_count > 0
        except InvalidId as e:
            logger.error(f"InvalidId error for pet_id {pet_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding treatment: {e}")
            return False
    
    def update_treatment(self, pet_id: str, user_id: str, treatment_id: str, treatment_data: Dict[str, Any]) -> bool:
        """Atualiza tratamento do pet"""
        try:
            if not ObjectId.is_valid(pet_id):
                logger.warning(f"Invalid ObjectId format for pet_id: {pet_id}")
                return False
            if not ObjectId.is_valid(treatment_id):
                logger.warning(f"Invalid ObjectId format for treatment_id: {treatment_id}")
                return False
            
            treatment_data["_id"] = ObjectId(treatment_id)
            result = self.collection.update_one(
                {
                    "_id": ObjectId(pet_id),
                    "users": user_id,
                    "deleted_at": None,
                    "treatments._id": ObjectId(treatment_id)
                },
                {"$set": {"treatments.$": treatment_data}}
            )
            return result.matched_count > 0
        except InvalidId as e:
            logger.error(f"InvalidId error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating treatment: {e}")
            return False
    
    def delete_treatment(self, pet_id: str, user_id: str, treatment_id: str) -> bool:
        """Remove tratamento do pet"""
        try:
            if not ObjectId.is_valid(pet_id):
                logger.warning(f"Invalid ObjectId format for pet_id: {pet_id}")
                return False
            if not ObjectId.is_valid(treatment_id):
                logger.warning(f"Invalid ObjectId format for treatment_id: {treatment_id}")
                return False
            
            result = self.collection.update_one(
                {
                    "_id": ObjectId(pet_id),
                    "users": user_id,
                    "deleted_at": None
                },
                {"$pull": {"treatments": {"_id": ObjectId(treatment_id)}}}
            )
            return result.matched_count > 0 and result.modified_count > 0
        except InvalidId as e:
            logger.error(f"InvalidId error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting treatment: {e}")
            return False
    
    def get_scheduled_treatments_for_date(self, target_date: str) -> List[Dict[str, Any]]:
        """
        Busca todos os tratamentos agendados para uma data específica
        target_date: data no formato "YYYY-MM-DD"
        Retorna lista de pets com seus tratamentos agendados
        """
        try:
            # Busca pets não deletados que têm tratamentos na data alvo
            pipeline = [
                {"$match": {"deleted_at": None}},
                {"$unwind": {"path": "$treatments", "preserveNullAndEmptyArrays": False}},
                {"$match": {
                    "treatments.date": target_date,
                    "treatments.done": False
                }},
                {"$group": {
                    "_id": "$_id",
                    "name": {"$first": "$name"},
                    "nickname": {"$first": "$nickname"},
                    "users": {"$first": "$users"},
                    "treatments": {"$push": "$treatments"}
                }}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            # Converte ObjectIds para strings
            for result in results:
                result["_id"] = str(result["_id"])
                result["users"] = [str(user_id) for user_id in result["users"]]
                for treatment in result["treatments"]:
                    treatment["_id"] = str(treatment["_id"])
            
            return results
        except Exception as e:
            logger.error(f"Error fetching scheduled treatments: {e}")
            return []
    
    def get_tomorrow_scheduled_treatments(self) -> List[Dict[str, Any]]:
        """
        Busca todos os tratamentos agendados para amanhã
        Retorna lista de pets com seus tratamentos agendados
        """
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")
        return self.get_scheduled_treatments_for_date(tomorrow_str)
    
    def get_current_month_treatments(self) -> List[Dict[str, Any]]:
        """
        Busca todos os tratamentos agendados para o mês atual
        Retorna lista de pets com seus tratamentos agendados
        """
        try:
            # Primeiro e último dia do mês atual
            now = datetime.now()
            first_day = now.replace(day=1).strftime("%Y-%m-%d")
            if now.month == 12:
                last_day = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
            last_day_str = last_day.strftime("%Y-%m-%d")
            
            # Pipeline para buscar tratamentos do mês
            pipeline = [
                {"$match": {"deleted_at": None}},
                {"$unwind": {"path": "$treatments", "preserveNullAndEmptyArrays": False}},
                {"$match": {
                    "treatments.date": {"$gte": first_day, "$lte": last_day_str},
                    "treatments.done": False
                }},
                {"$group": {
                    "_id": "$_id",
                    "name": {"$first": "$name"},
                    "nickname": {"$first": "$nickname"},
                    "users": {"$first": "$users"},
                    "treatments": {"$push": "$treatments"}
                }}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            # Converte ObjectIds para strings
            for result in results:
                result["_id"] = str(result["_id"])
                result["users"] = [str(user_id) for user_id in result["users"]]
                for treatment in result["treatments"]:
                    treatment["_id"] = str(treatment["_id"])
            
            return results
        except Exception as e:
            logger.error(f"Error fetching current month treatments: {e}")
            return []
    
    def get_expired_treatments(self) -> List[Dict[str, Any]]:
        """
        Busca todos os tratamentos expirados (data anterior a hoje e não concluídos)
        Retorna lista de pets com seus tratamentos expirados
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Pipeline para buscar tratamentos expirados
            pipeline = [
                {"$match": {"deleted_at": None}},
                {"$unwind": {"path": "$treatments", "preserveNullAndEmptyArrays": False}},
                {"$match": {
                    "treatments.date": {"$lt": today},
                    "treatments.done": False
                }},
                {"$group": {
                    "_id": "$_id",
                    "name": {"$first": "$name"},
                    "nickname": {"$first": "$nickname"},
                    "users": {"$first": "$users"},
                    "treatments": {"$push": "$treatments"}
                }}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            # Converte ObjectIds para strings
            for result in results:
                result["_id"] = str(result["_id"])
                result["users"] = [str(user_id) for user_id in result["users"]]
                for treatment in result["treatments"]:
                    treatment["_id"] = str(treatment["_id"])
            
            return results
        except Exception as e:
            logger.error(f"Error fetching expired treatments: {e}")
            return []
