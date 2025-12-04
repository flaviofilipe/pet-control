from pydantic import BaseModel, Field
from typing import Optional, Literal


class Treatment(BaseModel):
    id: str = Field(alias="_id")
    category: Literal["Vacinas", "Ectoparasitas", "Vermífugo", "Tratamentos"]
    name: str
    description: str | None = None
    date: str
    time: str | None = None
    applier_type: Literal["Veterinarian", "Tutor"]
    applier_name: Optional[str] = None
    applier_id: Optional[str] = None
    done: bool = Field(default=False)
