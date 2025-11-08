from typing import Dict, Any, Optional, List
from .base_repository import BaseRepository
from ..database import database


class UserRepository(BaseRepository):
    """Repository para operações com usuários/profiles"""
    
    def __init__(self):
        super().__init__(database.profiles_collection)
    
    def get_profile_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca perfil pelo ID do usuário"""
        return self.find_one({"_id": user_id})
    
    def create_or_update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Cria ou atualiza perfil do usuário"""
        profile_data["_id"] = user_id
        return self.replace_one({"_id": user_id}, profile_data, upsert=True)
    
    def search_veterinarians(self, search_term: str, exclude_user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca veterinários por nome"""
        filter_query = {
            "is_vet": True,
            "name": {"$regex": search_term, "$options": "i"},
            "_id": {"$ne": exclude_user_id}
        }
        return self.find(filter_query, limit=limit)
    
    def get_veterinarian_by_id(self, vet_id: str) -> Optional[Dict[str, Any]]:
        """Busca veterinário por ID"""
        return self.find_one({"_id": vet_id, "is_vet": True})
    
    def get_veterinarians_by_ids(self, vet_ids: List[str]) -> List[Dict[str, Any]]:
        """Busca veterinários por lista de IDs"""
        if not vet_ids:
            return []
        return self.find({"_id": {"$in": vet_ids}, "is_vet": True})
