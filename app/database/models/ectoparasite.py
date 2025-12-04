"""
Model Ectoparasite - Informações sobre ectoparasitas
"""

from sqlalchemy import String, Text, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class Ectoparasite(Base):
    __tablename__ = "ectoparasites"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Ectoparasite Data
    nome_praga: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tipo_praga: Mapped[str] = mapped_column(String(100), nullable=False)  # Inseto, Ácaro, etc
    
    # Arrays - usando JSON para compatibilidade SQLite/PostgreSQL
    especies_alvo: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Cão, Gato, etc
    transmissor_de_doencas: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sintomas_no_animal: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # JSON para dados estruturados (medicamentos)
    medicamentos_de_combate: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # Observações
    observacoes_adicionais: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Índices
    __table_args__ = (
        Index('idx_ectoparasites_nome', 'nome_praga'),
        Index('idx_ectoparasites_tipo', 'tipo_praga'),
    )
    
    def to_dict(self) -> dict:
        """Converte o model para dicionário"""
        return {
            "_id": str(self.id),
            "nome_praga": self.nome_praga,
            "tipo_praga": self.tipo_praga,
            "especies_alvo": self.especies_alvo or [],
            "transmissor_de_doencas": self.transmissor_de_doencas or [],
            "sintomas_no_animal": self.sintomas_no_animal or [],
            "medicamentos_de_combate": self.medicamentos_de_combate or [],
            "observacoes_adicionais": self.observacoes_adicionais,
        }
    
    def __repr__(self) -> str:
        return f"<Ectoparasite(id={self.id}, nome='{self.nome_praga}')>"
