import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends, status
from starlette.responses import RedirectResponse
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List, Literal
from bson import ObjectId


# Load environment variables from .env file
load_dotenv()

# Auth0 configuration
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
AUTH0_API_AUDIENCE = os.environ.get("AUTH0_API_AUDIENCE", "")
CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET", "")

if not all([AUTH0_DOMAIN, AUTH0_API_AUDIENCE, CLIENT_ID, CLIENT_SECRET]):
    raise ValueError("All Auth0 environment variables must be set.")

# MongoDB configuration
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "pet_control"
COLLECTION_NAME = "profiles"
PETS_COLLECTION_NAME = "pets"

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    profiles_collection = db[COLLECTION_NAME]
    pets_collection = db[PETS_COLLECTION_NAME]
    # The ismaster command is cheap and does not require auth.
    client.admin.command("ismaster")
except Exception as e:
    print(f"Could not connect to MongoDB: {e}")
    raise ConnectionError("Failed to connect to MongoDB.")

# FastAPI application setup
app = FastAPI(
    title="Profile Management API",
    description="API for user profile management with Auth0 and MongoDB.",
    version="1.0.0",
)

# ---
# Dependencies
# ---


def get_current_user_info(authorization: str = Header(...)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid or missing Authorization header"
        )

    access_token = authorization.split(" ")[1]

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(
            f"https://{AUTH0_DOMAIN}/userinfo",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        user_info = response.json()

        # The 'sub' field is the unique user ID from Auth0
        user_id = user_info.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token.")

        # Return both the user ID and the full profile info
        return {"id": user_id, "info": user_info}
    except requests.exceptions.RequestException as e:
        print(f"Auth0 UserInfo request failed: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")


# ---
# Pydantic Model
# ---


class UserAddress(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None


class UserProfile(BaseModel):
    """
    Pydantic model to validate incoming user profile data.
    The 'id' field is an alias for '_id' for database operations.
    """

    id: str | None = Field(alias="_id", default=None)
    name: str
    email: str | None = None
    bio: str | None = None
    address: UserAddress | None = None
    is_vet: bool | None = Field(default=False)


# Pet-related models
PetType = Literal["cat", "dog"]


class PetBase(BaseModel):
    name: str
    breed: str
    pedigree_number: str | None = None
    birth_date: str
    pet_type: PetType


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


# ---
# API Routes
# ---


@app.get("/login")
def login():
    """
    Redirects the user to Auth0 for authentication.
    """
    return RedirectResponse(
        url=f"https://{AUTH0_DOMAIN}/authorize?audience={AUTH0_API_AUDIENCE}&response_type=code&client_id={CLIENT_ID}&scope=offline_access openid profile email&redirect_uri=http://localhost:8000/token"
    )


@app.get("/token")
def get_access_token(code: str):
    """
    Exchanges the authorization code for an access token.
    """
    payload = (
        "grant_type=authorization_code",
        f"&code={code}",
        f"&client_id={CLIENT_ID}",
        f"&client_secret={CLIENT_SECRET}",
        f"&redirect_uri=http://localhost:8000/token",
    )

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(
            f"https://{AUTH0_DOMAIN}/oauth/token",
            headers=headers,
            data="".join(payload),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Auth0 Token exchange failed: {e}")
        raise HTTPException(
            status_code=400, detail="Failed to exchange code for token."
        )


@app.get("/profile")
def get_user_profile(user: dict = Depends(get_current_user_info)):
    """
    Returns the authenticated user's profile information from the database.
    """
    user_id = user["id"]
    profile = profiles_collection.find_one({"_id": user_id})

    if profile:
        # Pydantic handles the '_id' to 'id' alias correctly on return
        return UserProfile(**profile)
    else:
        # If no profile is found, return the basic info from Auth0
        return {
            "message": "User profile not found in database.",
            "auth0_info": user["info"],
        }


@app.post("/profile")
def create_or_update_user_profile(
    profile_data: UserProfile, user: dict = Depends(get_current_user_info)
):
    """
    Creates or updates a user profile in the database.
    The profile is linked to the authenticated user via their Auth0 ID.
    """

    # Use the 'id' field from the Pydantic model for the database's '_id'
    user_id = user["id"]
    profile_data.id = user_id
    profile_data.email = user["info"].get("email", profile_data.email)

    # Use 'upsert' to create or update the document
    result = profiles_collection.replace_one(
        {"email": profile_data.email},
        profile_data.model_dump(by_alias=True, exclude_unset=True),
        upsert=True,
    )

    if result.matched_count > 0:
        return {"message": "Profile updated successfully.", "user_id": user_id}
    else:
        return {"message": "Profile created successfully.", "user_id": user_id}


# ---
# Pet Endpoints (CRUD)
# ---


@app.post("/pets", status_code=status.HTTP_201_CREATED)
def create_pet(pet_data: PetCreate, user: dict = Depends(get_current_user_info)):
    """
    Creates a new pet and links it to the authenticated user.
    """
    user_id = user["id"]
    pet_document = pet_data.model_dump()
    pet_document["users"] = [user_id]

    result = pets_collection.insert_one(pet_document)

    if not result.inserted_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create pet.",
        )

    pet_document["_id"] = str(result.inserted_id)
    return {"message": "Pet created successfully.", "pet": PetInDB(**pet_document)}


@app.get("/pets", response_model=List[PetInDB])
def get_all_user_pets(user: dict = Depends(get_current_user_info)):
    """
    Returns all pets for the authenticated user.
    """
    user_id = user["id"]
    pets_cursor = pets_collection.find({"users": user_id})

    # Convert MongoDB documents to Pydantic models
    pets = []
    for pet in pets_cursor:
        pet["_id"] = str(pet["_id"])
        pets.append(PetInDB(**pet))

    return pets


@app.get("/pets/{pet_id}", response_model=PetInDB)
def get_pet_by_id(pet_id: str, user: dict = Depends(get_current_user_info)):
    """
    Returns a specific pet by ID, if the user is linked to it.
    """
    user_id = user["id"]
    pet_document = pets_collection.find_one({"_id": ObjectId(pet_id), "users": user_id})

    if not pet_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you do not have permission to view it.",
        )

    pet_document["_id"] = str(pet_document["_id"])
    return PetInDB(**pet_document)


@app.patch("/pets/{pet_id}", response_model=PetInDB)
def update_pet(
    pet_id: str,
    pet_data: PetUpdate,
    user: dict = Depends(get_current_user_info),
):
    """
    Updates an existing pet's information.
    """
    user_id = user["id"]

    # First, check if the user is authorized to modify this pet
    existing_pet = pets_collection.find_one({"_id": ObjectId(pet_id), "users": user_id})
    if not existing_pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you do not have permission to modify it.",
        )

    update_data = pet_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    pets_collection.update_one({"_id": ObjectId(pet_id)}, {"$set": update_data})

    updated_pet = pets_collection.find_one({"_id": ObjectId(pet_id)})
    updated_pet["_id"] = str(updated_pet["_id"])
    return PetInDB(**updated_pet)


@app.delete("/pets/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pet(pet_id: str, user: dict = Depends(get_current_user_info)):
    """
    Deletes a pet from the database.
    """
    user_id = user["id"]

    result = pets_collection.delete_one({"_id": ObjectId(pet_id), "users": user_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you do not have permission to delete it.",
        )

    return {"message": "Pet deleted successfully."}
