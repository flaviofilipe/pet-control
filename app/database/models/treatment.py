"""
Model Treatment - Representa tratamentos dos pets
"""

from sqlalchemy import String, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, SoftDeleteMixin


class Treatment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "treatments"
    
    # Primary Key - UUID como string
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Foreign Key
    pet_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Treatment Data
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # Vacinas, Ectoparasitas, Vermífugo, Tratamentos
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Scheduling
    date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:MM
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Applier
    applier_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Veterinarian, Tutor
    applier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    applier_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    pet = relationship("Pet", back_populates="treatments")
    applier_profile = relationship(
        "Profile",
        back_populates="treatments_as_applier",
        foreign_keys=[applier_id]
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "category IN ('Vacinas', 'Ectoparasitas', 'Vermífugo', 'Tratamentos')",
            name='chk_category'
        ),
        CheckConstraint(
            "applier_type IN ('Veterinarian', 'Tutor')",
            name='chk_applier_type'
        ),
        Index('idx_treatments_pet', 'pet_id'),
        Index('idx_treatments_date', 'date'),
        Index('idx_treatments_pending', 'pet_id', 'done', 'date'),
        Index('idx_treatments_category', 'category'),
    )
    
    def to_dict(self) -> dict:
        """Converte o model para dicionário (compatível com código legado)"""
        return {
            "_id": self.id,
            "category": self.category,
            "name": self.name,
            "description": self.description,
            "date": self.date,
            "time": self.time,
            "done": self.done,
            "applier_type": self.applier_type,
            "applier_name": self.applier_name,
            "applier_id": self.applier_id,
        }
    
    def __repr__(self) -> str:
        return f"<Treatment(id={self.id}, pet_id={self.pet_id}, name='{self.name}')>"

