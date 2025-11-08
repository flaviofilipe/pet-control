from typing import Dict, Any, Optional, List
from bson import ObjectId
from datetime import datetime
from .base_repository import BaseRepository
from ..database import database


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
        except:
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
            filter_query = {
                "_id": ObjectId(pet_id),
                "users": user_id,
                "deleted_at": None
            }
            return self.update_one(filter_query, {"$set": update_data})
        except:
            return False
    
    def soft_delete_pet(self, pet_id: str, user_id: str) -> bool:
        """Faz soft delete do pet"""
        try:
            filter_query = {
                "_id": ObjectId(pet_id),
                "users": user_id,
                "deleted_at": None
            }
            return self.update_one(filter_query, {"$set": {"deleted_at": datetime.now()}})
        except:
            return False
    
    def check_nickname_exists(self, nickname: str) -> bool:
        """Verifica se nickname já existe"""
        return self.find_one({"nickname": nickname}) is not None
    
    def grant_vet_access(self, pet_id: str, vet_id: str) -> bool:
        """Concede acesso de veterinário ao pet"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(pet_id)},
                {"$addToSet": {"users": vet_id}}
            )
            return result.modified_count > 0
        except:
            return False
    
    def revoke_vet_access(self, pet_id: str, vet_id: str) -> bool:
        """Remove acesso de veterinário ao pet"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(pet_id)},
                {"$pull": {"users": vet_id}}
            )
            return result.modified_count > 0
        except:
            return False
    
    def add_treatment(self, pet_id: str, user_id: str, treatment_data: Dict[str, Any]) -> bool:
        """Adiciona tratamento ao pet"""
        try:
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
        except:
            return False
    
    def update_treatment(self, pet_id: str, user_id: str, treatment_id: str, treatment_data: Dict[str, Any]) -> bool:
        """Atualiza tratamento do pet"""
        try:
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
        except:
            return False
    
    def delete_treatment(self, pet_id: str, user_id: str, treatment_id: str) -> bool:
        """Remove tratamento do pet"""
        try:
            result = self.collection.update_one(
                {
                    "_id": ObjectId(pet_id),
                    "users": user_id,
                    "deleted_at": None
                },
                {"$pull": {"treatments": {"_id": ObjectId(treatment_id)}}}
            )
            return result.matched_count > 0 and result.modified_count > 0
        except:
            return False
