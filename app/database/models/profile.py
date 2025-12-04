"""
Model Profile - Representa usuários do sistema
"""

from sqlalchemy import String, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, SoftDeleteMixin


class Profile(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "profiles"
    
    # Primary Key - usando auth_provider_id como chave primária (ex: auth0|xxx)
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    
    # User Data
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    bio: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Address - campos separados
    address_street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    address_zip: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    # Type
    is_vet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    pet_ownerships = relationship(
        "PetOwner",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    
    treatments_as_applier = relationship(
        "Treatment",
        back_populates="applier_profile",
        foreign_keys="Treatment.applier_id"
    )
    
    # Índices
    __table_args__ = (
        Index('idx_profiles_email', 'email'),
        Index('idx_profiles_is_vet', 'is_vet'),
        Index('idx_profiles_deleted', 'deleted_at'),
    )
    
    def to_dict(self) -> dict:
        """Converte o model para dicionário (compatível com código legado)"""
        return {
            "_id": self.id,
            "name": self.name,
            "email": self.email,
            "bio": self.bio,
            "address": {
                "street": self.address_street,
                "city": self.address_city,
                "state": self.address_state,
                "zip": self.address_zip,
            } if any([self.address_street, self.address_city, self.address_state, self.address_zip]) else None,
            "is_vet": self.is_vet,
        }
    
    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, name='{self.name}', email='{self.email}')>"

