"""
Model Vermifugo - Informações sobre vermífugos/endoparasitas
"""

from sqlalchemy import String, Text, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class Vermifugo(Base):
    __tablename__ = "vermifugos"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Vermifugo/Endoparasite Data
    nome_praga: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tipo_praga: Mapped[str] = mapped_column(String(100), nullable=False)  # Nematódeo, Cestódeo, etc
    
    # Arrays - usando JSON para compatibilidade SQLite/PostgreSQL
    especies_alvo: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Cão, Gato, etc
    sintomas_no_animal: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # JSON para dados estruturados (medicamentos)
    medicamentos_de_combate: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # Observações
    observacoes_adicionais: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Índices
    __table_args__ = (
        Index('idx_vermifugos_nome', 'nome_praga'),
        Index('idx_vermifugos_tipo', 'tipo_praga'),
    )
    
    def to_dict(self) -> dict:
        """Converte o model para dicionário"""
        return {
            "_id": str(self.id),
            "nome_praga": self.nome_praga,
            "tipo_praga": self.tipo_praga,
            "especies_alvo": self.especies_alvo or [],
            "sintomas_no_animal": self.sintomas_no_animal or [],
            "medicamentos_de_combate": self.medicamentos_de_combate or [],
            "observacoes_adicionais": self.observacoes_adicionais,
        }
    
    def __repr__(self) -> str:
        return f"<Vermifugo(id={self.id}, nome='{self.nome_praga}')>"
