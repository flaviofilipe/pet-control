"""
Repository para informações sobre vacinas, ectoparasitas e vermífugos usando SQLAlchemy
"""

from typing import Dict, Any, Optional, List
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.vaccine import Vaccine
from app.database.models.ectoparasite import Ectoparasite
from app.database.models.vermifugo import Vermifugo


class InfoRepository:
    """Repository para informações sobre vacinas, ectoparasitas e vermífugos"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==================== VACINAS ====================
    
    async def search_vaccines(
        self,
        search: Optional[str] = None,
        species: Optional[str] = None,
        vaccine_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Busca vacinas com filtros"""
        query = select(Vaccine)
        
        if search:
            search_filter = or_(
                Vaccine.nome_vacina.ilike(f"%{search}%"),
                Vaccine.descricao.ilike(f"%{search}%"),
                func.array_to_string(Vaccine.protege_contra, ' ').ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        if species:
            query = query.where(Vaccine.especie_alvo == species)
        
        if vaccine_type:
            query = query.where(Vaccine.tipo_vacina == vaccine_type)
        
        query = query.order_by(Vaccine.nome_vacina)
        
        result = await self.session.execute(query)
        vaccines = result.scalars().all()
        return [v.to_dict() for v in vaccines]
    
    async def get_vaccine_species(self) -> List[str]:
        """Retorna espécies disponíveis para vacinas"""
        query = select(Vaccine.especie_alvo).distinct()
        result = await self.session.execute(query)
        return [row[0] for row in result.all() if row[0]]
    
    async def get_vaccine_types(self) -> List[str]:
        """Retorna tipos de vacinas disponíveis"""
        query = select(Vaccine.tipo_vacina).distinct()
        result = await self.session.execute(query)
        return [row[0] for row in result.all() if row[0]]
    
    async def get_vaccines_autocomplete(self, query_str: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Autocomplete para vacinas"""
        query = (
            select(Vaccine)
            .where(Vaccine.nome_vacina.ilike(f"{query_str}%"))
            .order_by(Vaccine.nome_vacina)
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        vaccines = result.scalars().all()
        
        suggestions = []
        for vaccine in vaccines:
            suggestions.append({
                "id": str(vaccine.id),
                "nome": vaccine.nome_vacina,
                "especie": vaccine.especie_alvo,
                "tipo": vaccine.tipo_vacina,
            })
        return suggestions
    
    # ==================== ECTOPARASITAS ====================
    
    async def search_ectoparasites(
        self,
        search: Optional[str] = None,
        species: Optional[str] = None,
        pest_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Busca ectoparasitas com filtros"""
        query = select(Ectoparasite)
        
        if search:
            search_filter = or_(
                Ectoparasite.nome_praga.ilike(f"%{search}%"),
                func.array_to_string(Ectoparasite.transmissor_de_doencas, ' ').ilike(f"%{search}%"),
                func.array_to_string(Ectoparasite.sintomas_no_animal, ' ').ilike(f"%{search}%"),
                Ectoparasite.observacoes_adicionais.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        if species:
            query = query.where(Ectoparasite.especies_alvo.any(species))
        
        if pest_type:
            query = query.where(Ectoparasite.tipo_praga == pest_type)
        
        query = query.order_by(Ectoparasite.nome_praga)
        
        result = await self.session.execute(query)
        ectoparasites = result.scalars().all()
        return [e.to_dict() for e in ectoparasites]
    
    async def get_ectoparasite_species(self) -> List[str]:
        """Retorna espécies disponíveis para ectoparasitas"""
        query = select(func.unnest(Ectoparasite.especies_alvo)).distinct()
        result = await self.session.execute(query)
        return [row[0] for row in result.all() if row[0]]
    
    async def get_ectoparasite_types(self) -> List[str]:
        """Retorna tipos de ectoparasitas disponíveis"""
        query = select(Ectoparasite.tipo_praga).distinct()
        result = await self.session.execute(query)
        return [row[0] for row in result.all() if row[0]]
    
    async def get_ectoparasites_autocomplete(self, query_str: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Autocomplete para ectoparasitas"""
        search_filter = or_(
            Ectoparasite.nome_praga.ilike(f"%{query_str}%"),
            func.array_to_string(Ectoparasite.transmissor_de_doencas, ' ').ilike(f"%{query_str}%"),
            func.array_to_string(Ectoparasite.sintomas_no_animal, ' ').ilike(f"%{query_str}%")
        )
        
        query = (
            select(Ectoparasite)
            .where(search_filter)
            .order_by(Ectoparasite.nome_praga)
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        ectoparasites = result.scalars().all()
        
        suggestions = []
        for ectoparasite in ectoparasites:
            especies = ", ".join(ectoparasite.especies_alvo or [])
            
            # Determina onde o termo foi encontrado
            match_context = ""
            q_lower = query_str.lower()
            if q_lower in ectoparasite.nome_praga.lower():
                match_context = "Nome"
            elif any(q_lower in d.lower() for d in (ectoparasite.transmissor_de_doencas or [])):
                match_context = "Doença"
            elif any(q_lower in s.lower() for s in (ectoparasite.sintomas_no_animal or [])):
                match_context = "Sintoma"
            
            suggestions.append({
                "id": str(ectoparasite.id),
                "nome": ectoparasite.nome_praga,
                "especies": especies,
                "tipo": ectoparasite.tipo_praga,
                "contexto": match_context,
            })
        
        return suggestions
    
    # ==================== VERMÍFUGOS ====================
    
    async def search_vermifugos(
        self,
        search: Optional[str] = None,
        species: Optional[str] = None,
        pest_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Busca vermífugos com filtros"""
        query = select(Vermifugo)
        
        if search:
            search_filter = or_(
                Vermifugo.nome_praga.ilike(f"%{search}%"),
                Vermifugo.tipo_praga.ilike(f"%{search}%"),
                func.array_to_string(Vermifugo.sintomas_no_animal, ' ').ilike(f"%{search}%"),
                Vermifugo.observacoes_adicionais.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        if species:
            query = query.where(Vermifugo.especies_alvo.any(species))
        
        if pest_type:
            query = query.where(Vermifugo.tipo_praga == pest_type)
        
        query = query.order_by(Vermifugo.nome_praga)
        
        result = await self.session.execute(query)
        vermifugos = result.scalars().all()
        return [v.to_dict() for v in vermifugos]
    
    async def get_vermifugo_species(self) -> List[str]:
        """Retorna espécies disponíveis para vermífugos"""
        query = select(func.unnest(Vermifugo.especies_alvo)).distinct()
        result = await self.session.execute(query)
        return [row[0] for row in result.all() if row[0]]
    
    async def get_vermifugo_types(self) -> List[str]:
        """Retorna tipos de vermífugos disponíveis"""
        query = select(Vermifugo.tipo_praga).distinct()
        result = await self.session.execute(query)
        return [row[0] for row in result.all() if row[0]]
    
    async def get_vermifugos_autocomplete(self, query_str: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Autocomplete para vermífugos"""
        search_filter = or_(
            Vermifugo.nome_praga.ilike(f"%{query_str}%"),
            Vermifugo.tipo_praga.ilike(f"%{query_str}%"),
            func.array_to_string(Vermifugo.sintomas_no_animal, ' ').ilike(f"%{query_str}%")
        )
        
        query = (
            select(Vermifugo)
            .where(search_filter)
            .order_by(Vermifugo.nome_praga)
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        vermifugos = result.scalars().all()
        
        suggestions = []
        for vermifugo in vermifugos:
            especies = ", ".join(vermifugo.especies_alvo or [])
            
            # Determina onde o termo foi encontrado
            match_context = ""
            q_lower = query_str.lower()
            if q_lower in vermifugo.nome_praga.lower():
                match_context = "Nome"
            elif q_lower in vermifugo.tipo_praga.lower():
                match_context = "Tipo"
            elif any(q_lower in s.lower() for s in (vermifugo.sintomas_no_animal or [])):
                match_context = "Sintoma"
            
            suggestions.append({
                "id": str(vermifugo.id),
                "nome": vermifugo.nome_praga,
                "especies": especies,
                "tipo": vermifugo.tipo_praga,
                "contexto": match_context,
            })
        
        return suggestions

