from typing import Dict, Any, Optional, List
from .base_repository import BaseRepository
from ..database import database


class InfoRepository(BaseRepository):
    """Repository para informações sobre vacinas, ectoparasitas e vermífugos"""
    
    def __init__(self):
        # Não usa super().__init__ pois trabalha com múltiplas collections
        self.vaccines_collection = database.vaccines_collection
        self.ectoparasites_collection = database.ectoparasites_collection
        self.vermifugos_collection = database.vermifugos_collection
    
    # Métodos para Vacinas
    def search_vaccines(self, search: Optional[str] = None, species: Optional[str] = None, vaccine_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Busca vacinas com filtros"""
        filter_query = {}
        
        if search:
            filter_query["$or"] = [
                {"nome_vacina": {"$regex": search, "$options": "i"}},
                {"descricao": {"$regex": search, "$options": "i"}},
                {"protege_contra": {"$regex": search, "$options": "i"}},
            ]
        
        if species:
            filter_query["especie_alvo"] = species
            
        if vaccine_type:
            filter_query["tipo_vacina"] = vaccine_type
        
        vaccines = list(self.vaccines_collection.find(filter_query).sort("nome_vacina", 1))
        for vaccine in vaccines:
            vaccine["_id"] = str(vaccine["_id"])
        
        return vaccines
    
    def get_vaccine_species(self) -> List[str]:
        """Retorna espécies disponíveis para vacinas"""
        return list(self.vaccines_collection.distinct("especie_alvo"))
    
    def get_vaccine_types(self) -> List[str]:
        """Retorna tipos de vacinas disponíveis"""
        return list(self.vaccines_collection.distinct("tipo_vacina"))
    
    def get_vaccines_autocomplete(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Autocomplete para vacinas"""
        filter_query = {"nome_vacina": {"$regex": f"^{query}", "$options": "i"}}
        vaccines = list(self.vaccines_collection.find(filter_query).limit(limit).sort("nome_vacina", 1))
        
        suggestions = []
        for vaccine in vaccines:
            suggestions.append({
                "id": str(vaccine["_id"]),
                "nome": vaccine["nome_vacina"],
                "especie": vaccine["especie_alvo"],
                "tipo": vaccine["tipo_vacina"],
            })
        return suggestions
    
    # Métodos para Ectoparasitas
    def search_ectoparasites(self, search: Optional[str] = None, species: Optional[str] = None, pest_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Busca ectoparasitas com filtros"""
        filter_query = {}
        
        if search:
            filter_query["$or"] = [
                {"nome_praga": {"$regex": search, "$options": "i"}},
                {"transmissor_de_doencas": {"$regex": search, "$options": "i"}},
                {"sintomas_no_animal": {"$regex": search, "$options": "i"}},
                {"medicamentos_de_combate.descricao": {"$regex": search, "$options": "i"}},
                {"medicamentos_de_combate.principios_ativos": {"$regex": search, "$options": "i"}},
                {"observacoes_adicionais": {"$regex": search, "$options": "i"}},
            ]
        
        if species:
            filter_query["especies_alvo"] = species
            
        if pest_type:
            filter_query["tipo_praga"] = pest_type
        
        ectoparasites = list(self.ectoparasites_collection.find(filter_query).sort("nome_praga", 1))
        for ectoparasite in ectoparasites:
            ectoparasite["_id"] = str(ectoparasite["_id"])
        
        return ectoparasites
    
    def get_ectoparasite_species(self) -> List[str]:
        """Retorna espécies disponíveis para ectoparasitas"""
        species = list(self.ectoparasites_collection.distinct("especies_alvo"))
        # Flatten da lista de listas
        species_flat = []
        for species_list in species:
            if isinstance(species_list, list):
                species_flat.extend(species_list)
            else:
                species_flat.append(species_list)
        return list(set(species_flat))
    
    def get_ectoparasite_types(self) -> List[str]:
        """Retorna tipos de ectoparasitas disponíveis"""
        return list(self.ectoparasites_collection.distinct("tipo_praga"))
    
    def get_ectoparasites_autocomplete(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Autocomplete para ectoparasitas"""
        filter_query = {
            "$or": [
                {"nome_praga": {"$regex": f"^{query}", "$options": "i"}},
                {"nome_praga": {"$regex": query, "$options": "i"}},
                {"transmissor_de_doencas": {"$regex": query, "$options": "i"}},
                {"sintomas_no_animal": {"$regex": query, "$options": "i"}},
                {"medicamentos_de_combate.principios_ativos": {"$regex": query, "$options": "i"}},
            ]
        }
        
        ectoparasites = list(self.ectoparasites_collection.find(filter_query).limit(limit).sort("nome_praga", 1))
        
        suggestions = []
        for ectoparasite in ectoparasites:
            especies = ", ".join(ectoparasite["especies_alvo"])
            
            # Determina onde o termo foi encontrado
            match_context = ""
            if query.lower() in ectoparasite["nome_praga"].lower():
                match_context = "Nome"
            elif any(query.lower() in doenca.lower() for doenca in ectoparasite.get("transmissor_de_doencas", [])):
                match_context = "Doença"
            elif any(query.lower() in sintoma.lower() for sintoma in ectoparasite.get("sintomas_no_animal", [])):
                match_context = "Sintoma"
            elif any(query.lower() in principio.lower() for medicamento in ectoparasite.get("medicamentos_de_combate", []) for principio in medicamento.get("principios_ativos", [])):
                match_context = "Princípio Ativo"
            
            suggestions.append({
                "id": str(ectoparasite["_id"]),
                "nome": ectoparasite["nome_praga"],
                "especies": especies,
                "tipo": ectoparasite["tipo_praga"],
                "contexto": match_context,
            })
        
        return suggestions
    
    # Métodos para Vermífugos
    def search_vermifugos(self, search: Optional[str] = None, species: Optional[str] = None, pest_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Busca vermífugos com filtros"""
        vermifugos_doc = self.vermifugos_collection.find_one()
        
        if not vermifugos_doc:
            return []
        
        vermifugos_list = vermifugos_doc.get("parasitas_e_tratamentos", [])
        
        # Aplica filtros se fornecidos
        if search:
            search_lower = search.lower()
            vermifugos_list = [
                v for v in vermifugos_list
                if search_lower in v.get("nome_praga", "").lower()
                or search_lower in v.get("tipo_praga", "").lower()
                or any(search_lower in sintoma.lower() for sintoma in v.get("sintomas_no_animal", []))
                or any(search_lower in med.get("descricao", "").lower() for med in v.get("medicamentos_de_combate", []))
                or any(search_lower in principio.lower() for med in v.get("medicamentos_de_combate", []) for principio in med.get("principios_ativos", []))
                or search_lower in v.get("observacoes_adicionais", "").lower()
            ]
        
        if species:
            vermifugos_list = [v for v in vermifugos_list if species in v.get("especies_alvo", [])]
            
        if pest_type:
            vermifugos_list = [v for v in vermifugos_list if v.get("tipo_praga") == pest_type]
        
        # Adiciona ID único para cada vermífugo
        for i, vermifugo in enumerate(vermifugos_list):
            vermifugo["_id"] = str(i)
        
        return vermifugos_list
    
    def get_vermifugo_species(self) -> List[str]:
        """Retorna espécies disponíveis para vermífugos"""
        vermifugos_doc = self.vermifugos_collection.find_one()
        if not vermifugos_doc:
            return []
            
        all_vermifugos = vermifugos_doc.get("parasitas_e_tratamentos", [])
        species = list(set([
            especie for v in all_vermifugos 
            for especie in v.get("especies_alvo", [])
        ]))
        return species
    
    def get_vermifugo_types(self) -> List[str]:
        """Retorna tipos de vermífugos disponíveis"""
        vermifugos_doc = self.vermifugos_collection.find_one()
        if not vermifugos_doc:
            return []
            
        all_vermifugos = vermifugos_doc.get("parasitas_e_tratamentos", [])
        types = list(set([v.get("tipo_praga") for v in all_vermifugos if v.get("tipo_praga")]))
        return types
    
    def get_vermifugos_autocomplete(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Autocomplete para vermífugos"""
        vermifugos_doc = self.vermifugos_collection.find_one()
        if not vermifugos_doc:
            return []
        
        vermifugos_list = vermifugos_doc.get("parasitas_e_tratamentos", [])
        suggestions = []
        
        for i, vermifugo in enumerate(vermifugos_list):
            q_lower = query.lower()
            match_found = False
            match_context = ""
            
            if q_lower in vermifugo.get("nome_praga", "").lower():
                match_found = True
                match_context = "Nome"
            elif q_lower in vermifugo.get("tipo_praga", "").lower():
                match_found = True
                match_context = "Tipo"
            elif any(q_lower in sintoma.lower() for sintoma in vermifugo.get("sintomas_no_animal", [])):
                match_found = True
                match_context = "Sintoma"
            elif any(q_lower in principio.lower() for med in vermifugo.get("medicamentos_de_combate", []) for principio in med.get("principios_ativos", [])):
                match_found = True
                match_context = "Princípio Ativo"
            elif q_lower in vermifugo.get("observacoes_adicionais", "").lower():
                match_found = True
                match_context = "Observações"
            
            if match_found:
                especies = ", ".join(vermifugo.get("especies_alvo", []))
                suggestions.append({
                    "id": str(i),
                    "nome": vermifugo.get("nome_praga", ""),
                    "especies": especies,
                    "tipo": vermifugo.get("tipo_praga", ""),
                    "contexto": match_context,
                })
                
                if len(suggestions) >= limit:
                    break
        
        return suggestions
