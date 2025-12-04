"""
Model PetOwner - Relacionamento Many-to-Many entre Pet e Profile
"""

from sqlalchemy import String, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, SoftDeleteMixin


class PetOwner(Base, TimestampMixin, SoftDeleteMixin):
    """Tabela de relacionamento Many-to-Many entre Pet e Profile"""
    __tablename__ = "pet_owners"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Foreign Keys
    pet_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False
    )
    
    profile_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relationships
    pet = relationship("Pet", back_populates="owners")
    profile = relationship("Profile", back_populates="pet_ownerships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('pet_id', 'profile_id', name='uq_pet_owner'),
        Index('idx_pet_owners_pet', 'pet_id'),
        Index('idx_pet_owners_profile', 'profile_id'),
    )
    
    def __repr__(self) -> str:
        return f"<PetOwner(pet_id={self.pet_id}, profile_id={self.profile_id})>"

