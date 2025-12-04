"""
Model Pet - Representa os pets do sistema
"""

from sqlalchemy import String, Index, CheckConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any
from app.database.base import Base, TimestampMixin, SoftDeleteMixin


class Pet(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "pets"
    
    # Primary Key - UUID como string
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Pet Data
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    nickname: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    breed: Mapped[str] = mapped_column(String(100), nullable=False)
    pedigree_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    birth_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    pet_type: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # 'cat' ou 'dog'
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)  # 'male' ou 'female'
    
    # Photo - JSON com original, thumbnail e filename
    photo: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    owners = relationship(
        "PetOwner",
        back_populates="pet",
        cascade="all, delete-orphan"
    )
    
    treatments = relationship(
        "Treatment",
        back_populates="pet",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "pet_type IN ('cat', 'dog')",
            name='chk_pet_type'
        ),
        CheckConstraint(
            "gender IS NULL OR gender IN ('male', 'female')",
            name='chk_gender'
        ),
        Index('idx_pets_nickname', 'nickname'),
        Index('idx_pets_deleted', 'deleted_at'),
    )
    
    def to_dict(self, include_treatments: bool = True) -> dict:
        """Converte o model para dicionário (compatível com código legado)"""
        result = {
            "_id": self.id,
            "name": self.name,
            "nickname": self.nickname,
            "breed": self.breed,
            "pedigree_number": self.pedigree_number,
            "birth_date": self.birth_date,
            "pet_type": self.pet_type,
            "gender": self.gender,
            "photo": self.photo,
            "users": [owner.profile_id for owner in self.owners if not owner.deleted_at],
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        
        if include_treatments:
            result["treatments"] = [
                treatment.to_dict() for treatment in self.treatments
                if not treatment.deleted_at
            ]
        
        return result
    
    def __repr__(self) -> str:
        return f"<Pet(id={self.id}, name='{self.name}', type='{self.pet_type}')>"

