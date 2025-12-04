"""
Base Repository para operações CRUD com SQLAlchemy
"""

from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Repository base para operações CRUD com SQLAlchemy.
    
    Usage:
        class ProfileRepository(BaseRepository[Profile]):
            def __init__(self, session: AsyncSession):
                super().__init__(Profile, session)
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, **kwargs) -> ModelType:
        """Criar novo registro"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(
        self,
        id: Any,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """Buscar por ID"""
        query = select(self.model).where(self.model.id == id)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at == None)  # noqa: E711
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ModelType]:
        """Buscar todos os registros"""
        query = select(self.model)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at == None)  # noqa: E711
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def find_one(self, include_deleted: bool = False, **filters) -> Optional[ModelType]:
        """Buscar um registro por filtros"""
        query = select(self.model)
        
        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at == None)  # noqa: E711
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        **filters
    ) -> List[ModelType]:
        """Buscar múltiplos registros por filtros"""
        query = select(self.model)
        
        for key, value in filters.items():
            if isinstance(value, list):
                query = query.where(getattr(self.model, key).in_(value))
            else:
                query = query.where(getattr(self.model, key) == value)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at == None)  # noqa: E711
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        """Atualizar registro"""
        instance = await self.get_by_id(id)
        
        if not instance:
            return None
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def soft_delete(self, id: Any) -> bool:
        """Soft delete de registro"""
        instance = await self.get_by_id(id)
        
        if not instance or not hasattr(instance, 'soft_delete'):
            return False
        
        instance.soft_delete()
        await self.session.flush()
        return True
    
    async def hard_delete(self, id: Any) -> bool:
        """Delete físico de registro"""
        instance = await self.get_by_id(id, include_deleted=True)
        
        if not instance:
            return False
        
        await self.session.delete(instance)
        await self.session.flush()
        return True
    
    async def count(self, include_deleted: bool = False, **filters) -> int:
        """Contar registros"""
        query = select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at == None)  # noqa: E711
        
        result = await self.session.execute(query)
        return result.scalar_one()

