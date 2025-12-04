from pydantic import BaseModel, Field


class UserAddress(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None


class UserProfile(BaseModel):
    id: str | None = Field(alias="_id", default=None)
    name: str
    email: str | None = None
    bio: str | None = None
    address: UserAddress | None = None
    is_vet: bool | None = Field(default=False)
