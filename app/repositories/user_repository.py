"""
Repository para operações com usuários/profiles usando SQLAlchemy
"""

from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.profile import Profile
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[Profile]):
    """Repository para operações com usuários/profiles"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Profile, session)
    
    async def get_profile_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca perfil pelo ID do usuário"""
        profile = await self.find_one(id=user_id)
        return profile.to_dict() if profile else None
    
    async def get_profile_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca perfil pelo email do usuário"""
        profile = await self.find_one(email=email)
        return profile.to_dict() if profile else None
    
    async def create_or_update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Cria ou atualiza perfil do usuário"""
        existing = await self.get_by_id(user_id)
        
        # Extrair dados de endereço se existir
        address = profile_data.pop("address", None)
        
        # Preparar dados para inserção/atualização
        db_data = {
            "id": user_id,
            "name": profile_data.get("name", ""),
            "email": profile_data.get("email", ""),
            "bio": profile_data.get("bio"),
            "is_vet": profile_data.get("is_vet", False),
        }
        
        if address:
            db_data["address_street"] = address.get("street")
            db_data["address_city"] = address.get("city")
            db_data["address_state"] = address.get("state")
            db_data["address_zip"] = address.get("zip")
        
        if existing:
            # Update
            for key, value in db_data.items():
                if key != "id" and hasattr(existing, key):
                    setattr(existing, key, value)
            await self.session.flush()
        else:
            # Create
            await self.create(**db_data)
        
        return True
    
    async def search_veterinarians(
        self,
        search_term: str,
        exclude_user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Busca veterinários por nome"""
        query = (
            select(Profile)
            .where(
                Profile.is_vet == True,  # noqa: E712
                Profile.deleted_at == None,  # noqa: E711
                Profile.id != exclude_user_id,
                Profile.name.ilike(f"%{search_term}%")
            )
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        profiles = result.scalars().all()
        return [p.to_dict() for p in profiles]
    
    async def get_veterinarian_by_id(self, vet_id: str) -> Optional[Dict[str, Any]]:
        """Busca veterinário por ID"""
        profile = await self.find_one(id=vet_id, is_vet=True)
        return profile.to_dict() if profile else None
    
    async def get_veterinarians_by_ids(self, vet_ids: List[str]) -> List[Dict[str, Any]]:
        """Busca veterinários por lista de IDs"""
        if not vet_ids:
            return []
        
        query = (
            select(Profile)
            .where(
                Profile.id.in_(vet_ids),
                Profile.is_vet == True,  # noqa: E712
                Profile.deleted_at == None  # noqa: E711
            )
        )
        
        result = await self.session.execute(query)
        profiles = result.scalars().all()
        return [p.to_dict() for p in profiles]
    
    async def get_users_by_ids(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Busca usuários por lista de IDs"""
        if not user_ids:
            return []
        
        query = (
            select(Profile)
            .where(
                Profile.id.in_(user_ids),
                Profile.deleted_at == None  # noqa: E711
            )
        )
        
        result = await self.session.execute(query)
        profiles = result.scalars().all()
        return [p.to_dict() for p in profiles]
    
    async def get_user_emails_by_ids(self, user_ids: List[str]) -> List[Dict[str, str]]:
        """Busca emails dos usuários por lista de IDs. Retorna id, name e email."""
        if not user_ids:
            return []
        
        query = (
            select(Profile)
            .where(
                Profile.id.in_(user_ids),
                Profile.deleted_at == None  # noqa: E711
            )
        )
        
        result = await self.session.execute(query)
        profiles = result.scalars().all()
        
        return [
            {
                "id": profile.id,
                "name": profile.name or "Usuário",
                "email": profile.email or ""
            }
            for profile in profiles
            if profile.email
        ]

