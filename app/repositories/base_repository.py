from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pymongo.collection import Collection


class BaseRepository(ABC):
    """Repository base com operações CRUD genéricas"""
    
    def __init__(self, collection: Collection):
        self.collection = collection
    
    def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca um documento"""
        return self.collection.find_one(filter_dict)
    
    def find(self, filter_dict: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Busca múltiplos documentos"""
        cursor = self.collection.find(filter_dict)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    def insert_one(self, document: Dict[str, Any]) -> str:
        """Insere um documento"""
        result = self.collection.insert_one(document)
        return str(result.inserted_id)
    
    def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> bool:
        """Atualiza um documento"""
        result = self.collection.update_one(filter_dict, update_dict)
        return result.modified_count > 0
    
    def delete_one(self, filter_dict: Dict[str, Any]) -> bool:
        """Remove um documento"""
        result = self.collection.delete_one(filter_dict)
        return result.deleted_count > 0
    
    def replace_one(self, filter_dict: Dict[str, Any], replacement: Dict[str, Any], upsert: bool = False) -> bool:
        """Substitui um documento"""
        result = self.collection.replace_one(filter_dict, replacement, upsert=upsert)
        # Retorna True se modificou, inseriu (upsert), ou se matched (documento já existe com os mesmos dados)
        return result.modified_count > 0 or result.matched_count > 0 or (upsert and result.upserted_id is not None)
