from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime
from .treatment import Treatment

PetType = Literal["cat", "dog"]


class PetBase(BaseModel):
    name: str
    breed: str
    pedigree_number: str | None = None
    birth_date: str
    pet_type: PetType
    treatments: List[Treatment] = []
    deleted_at: Optional[datetime] = None
    nickname: Optional[str] = None
    gender: Optional[Literal["male", "female"]] = None


class PetInDB(PetBase):
    id: str = Field(alias="_id")
    users: List[str]


class PetCreate(PetBase):
    pass


class PetUpdate(BaseModel):
    name: str | None = None
    breed: str | None = None
    pedigree_number: str | None = None
    birth_date: str | None = None
    pet_type: PetType | None = None
    treatments: List[Treatment] | None = None
