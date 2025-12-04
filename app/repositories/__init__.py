"""
Repositories para Pet Control System
"""

from app.repositories.base_repository import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.pet_repository import PetRepository
from app.repositories.info_repository import InfoRepository

# Aliases para compatibilidade
ProfileRepository = UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "PetRepository",
    "InfoRepository",
    "ProfileRepository",
]
