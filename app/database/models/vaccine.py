"""
Model Vaccine - Informações sobre vacinas
"""

from sqlalchemy import String, Text, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class Vaccine(Base):
    __tablename__ = "vaccines"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Vaccine Data
    nome_vacina: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    especie_alvo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # Cão, Gato, etc
    tipo_vacina: Mapped[str] = mapped_column(String(100), nullable=False)  # Múltipla, Única, etc
    
    # Arrays - usando JSON para compatibilidade SQLite/PostgreSQL
    protege_contra: Mapped[list | None] = mapped_column(JSON, nullable=True)
    efeitos_colaterais: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # JSON para dados estruturados
    cronograma_vacinal: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Índices
    __table_args__ = (
        Index('idx_vaccines_nome', 'nome_vacina'),
        Index('idx_vaccines_especie', 'especie_alvo'),
        Index('idx_vaccines_tipo', 'tipo_vacina'),
    )
    
    def to_dict(self) -> dict:
        """Converte o model para dicionário"""
        return {
            "_id": str(self.id),
            "nome_vacina": self.nome_vacina,
            "descricao": self.descricao,
            "especie_alvo": self.especie_alvo,
            "tipo_vacina": self.tipo_vacina,
            "protege_contra": self.protege_contra or [],
            "efeitos_colaterais": self.efeitos_colaterais or [],
            "cronograma_vacinal": self.cronograma_vacinal or {},
        }
    
    def __repr__(self) -> str:
        return f"<Vaccine(id={self.id}, nome='{self.nome_vacina}')>"
