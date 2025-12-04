"""
SQLAlchemy Models para Pet Control System
"""

from app.database.base import Base
from app.database.models.profile import Profile
from app.database.models.pet import Pet
from app.database.models.pet_owner import PetOwner
from app.database.models.treatment import Treatment
from app.database.models.vaccine import Vaccine
from app.database.models.ectoparasite import Ectoparasite
from app.database.models.vermifugo import Vermifugo

__all__ = [
    "Base",
    "Profile",
    "Pet",
    "PetOwner",
    "Treatment",
    "Vaccine",
    "Ectoparasite",
    "Vermifugo",
]

