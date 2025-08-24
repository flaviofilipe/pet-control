import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends
from starlette.responses import RedirectResponse
from pymongo import MongoClient
from pydantic import BaseModel, Field

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

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    profiles_collection = db[COLLECTION_NAME]
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
