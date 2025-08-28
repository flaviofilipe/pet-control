import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends, status, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List, Literal
from bson import ObjectId
from starlette.middleware.sessions import SessionMiddleware  # Adicionado

# Load environment variables from .env file
load_dotenv()

# Auth0 configuration
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
AUTH0_API_AUDIENCE = os.environ.get("AUTH0_API_AUDIENCE", "")
CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET", "")
AUTH0_CALLBACK_URI = os.environ.get(
    "AUTH0_CALLBACK_URI", "http://localhost:8000/callback"
)

if not all(
    [AUTH0_DOMAIN, AUTH0_API_AUDIENCE, CLIENT_ID, CLIENT_SECRET, AUTH0_CALLBACK_URI]
):
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

# Adicionando o middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionando o middleware de sessão para gerenciar o estado do usuário logado
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET_KEY", "your-super-secret-key-here"),
)

# Configuração do Jinja2
templates = Jinja2Templates(directory="templates")

# Servindo arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---
# Dependências
# ---
def get_current_user_info_from_session(request: Request):
    """
    Dependência para obter informações do usuário a partir da sessão.
    Isso é usado para proteger as rotas de templates HTML.
    """
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(
            f"https://{AUTH0_DOMAIN}/userinfo",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        user_info = response.json()
        user_id = user_info.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token.")

        return {"id": user_id, "info": user_info}
    except requests.exceptions.RequestException as e:
        print(f"Auth0 UserInfo request failed: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")


def get_current_user_info_from_header(authorization: str = Header(...)):
    """
    Dependência original para obter informações do usuário a partir do cabeçalho.
    Isso é usado para proteger os endpoints da API.
    """
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
        user_id = user_info.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token.")
        return {"id": user_id, "info": user_info}
    except requests.exceptions.RequestException as e:
        print(f"Auth0 UserInfo request failed: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")


# Pydantic Models (Sem alteração)
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
# Rotas da API
# ---


@app.get("/")
def get_landing_page(request: Request):
    
    is_authenticated = "access_token" in request.session
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_authenticated": is_authenticated,
            "current_year": 2024,
        },
    )


@app.get("/login")
def login():
    """
    Redireciona o usuário para o Auth0 para autenticação.
    """
    return RedirectResponse(
        url=f"https://{AUTH0_DOMAIN}/authorize?audience={AUTH0_API_AUDIENCE}&response_type=code&client_id={CLIENT_ID}&scope=offline_access openid profile email&redirect_uri={AUTH0_CALLBACK_URI}"
    )


@app.get("/dashboard", name="dashboard")
def get_dashboard_page(request: Request, user: dict = Depends(get_current_user_info_from_session)):
    """
    Renderiza a página do dashboard para usuários autenticados,
    passando os dados do usuário e a lista de pets para o template.
    """
    is_authenticated = "access_token" in request.session
    user_id = user["id"]
    pets_cursor = pets_collection.find({"users": user_id})
    pets_list = []
    for pet in pets_cursor:
        pet["_id"] = str(pet["_id"])
        pets_list.append(pet)
        
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "is_authenticated": is_authenticated,
            "current_year": 2024,
            "user_info": user["info"],
            "pets": pets_list
        }
    )


@app.get("/callback")
def callback(request: Request, code: str):
    """
    Manipula o redirecionamento do Auth0 após a autenticação.
    Troca o código de autorização por um token e armazena-o na sessão.
    """
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": AUTH0_CALLBACK_URI,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(
            f"https://{AUTH0_DOMAIN}/oauth/token",
            headers=headers,
            data=payload,
            timeout=10,
        )
        response.raise_for_status()
        token_info = response.json()

        # Armazena o token de acesso na sessão
        request.session["access_token"] = token_info.get("access_token")

        # Redireciona o usuário para o dashboard
        return RedirectResponse(url="/dashboard")

    except requests.exceptions.RequestException as e:
        print(f"Auth0 Token exchange failed: {e}")
        raise HTTPException(
            status_code=400, detail="Failed to exchange code for token."
        )


# Rota para logout
@app.get("/logout")
def logout(request: Request):
    """
    Limpa a sessão e redireciona para a página inicial.
    """
    request.session.clear()
    return RedirectResponse(url="/")


@app.get("/profile")
def get_user_profile(
    request: Request, user: dict = Depends(get_current_user_info_from_session)
):
    """
    Exibe o perfil do usuário logado em uma página HTML.
    """
    user_id = user["id"]
    profile = profiles_collection.find_one({"_id": user_id})

    # Verifica se existe um perfil completo no banco de dados.
    if profile:
        profile_data = profile
    else:
        # Se não houver, usa os dados do Auth0 como fallback.
        profile_data = {
            "name": user["info"].get("name", "Usuário"),
            "email": user["info"].get("email"),
            "bio": "Complete seu perfil para adicionar uma biografia.",
            "address": None,
            "is_vet": False,
        }

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user_info": profile_data,
        },
    )


@app.get("/profile/edit")
def edit_user_profile_page(
    request: Request, user: dict = Depends(get_current_user_info_from_session)
):
    """
    Renderiza a página com o formulário para editar o perfil do usuário.
    """
    user_id = user["id"]
    profile = profiles_collection.find_one({"_id": user_id})

    if profile:
        profile_data = profile
    else:
        profile_data = {
            "name": user["info"].get("name", "Usuário"),
            "email": user["info"].get("email"),
            "bio": None,
            "address": None,
            "is_vet": False,
        }

    return templates.TemplateResponse(
        "profile_update.html",
        {
            "request": request,
            "user_info": profile_data,
        },
    )


@app.post("/profile")
def create_or_update_user_profile(
    user: dict = Depends(get_current_user_info_from_session),
    name: str = Form(...),
    bio: str | None = Form(None),
    street: str | None = Form(None),
    city: str | None = Form(None),
    state: str | None = Form(None),
    zip: str | None = Form(None),
    is_vet: bool = Form(False),
):
    """
    Cria ou atualiza um perfil de usuário a partir dos dados do formulário HTML.
    Esta rota substitui a lógica anterior de criação e atualização.
    """
    user_id = user["id"]
    email = user["info"].get("email")

    profile_data = {
        "_id": user_id,
        "name": name,
        "email": email,
        "bio": bio,
        "address": {
            "street": street,
            "city": city,
            "state": state,
            "zip": zip,
        },
        "is_vet": is_vet,
    }

    # Use 'upsert' para criar ou atualizar o documento
    profiles_collection.replace_one(
        {"_id": user_id},
        profile_data,
        upsert=True,
    )

    # Redireciona o usuário de volta para a página de perfil
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/profile")
def create_or_update_user_profile(
    profile_data: UserProfile, user: dict = Depends(get_current_user_info_from_header)
):
    user_id = user["id"]
    profile_data.id = user_id
    profile_data.email = user["info"].get("email", profile_data.email)
    result = profiles_collection.replace_one(
        {"email": profile_data.email},
        profile_data.model_dump(by_alias=True, exclude_unset=True),
        upsert=True,
    )
    if result.matched_count > 0:
        return {"message": "Profile updated successfully.", "user_id": user_id}
    else:
        return {"message": "Profile created successfully.", "user_id": user_id}


# Pet Endpoints (CRUD)
@app.get("/pets/create")
def add_pet_page(request: Request, user: dict = Depends(get_current_user_info_from_session)):
    """
    Renderiza o formulário para adicionar um novo pet.
    """
    return templates.TemplateResponse("add_pet.html", {"request": request})

@app.post("/pets")
def create_or_update_pet_from_form(
    user: dict = Depends(get_current_user_info_from_session),
    pet_id: str | None = Form(None), # Novo campo para o ID
    name: str = Form(...),
    breed: str = Form(...),
    pedigree_number: str | None = Form(None),
    birth_date: str = Form(...),
    pet_type: PetType = Form(...)
):
    """
    Cria ou atualiza um pet a partir do formulário HTML.
    """
    user_id = user["id"]
    
    pet_data = {
        "name": name,
        "breed": breed,
        "pedigree_number": pedigree_number,
        "birth_date": birth_date,
        "pet_type": pet_type,
        "users": [user_id]
    }
    
    if pet_id:
        # Lógica de atualização
        result = pets_collection.update_one(
            {"_id": ObjectId(pet_id), "users": user_id},
            {"$set": pet_data}
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pet não encontrado ou você não tem permissão para editar."
            )
    else:
        # Lógica de criação
        result = pets_collection.insert_one(pet_data)
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao criar pet."
            )
            
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/pets/{pet_id}/delete")
def delete_pet_from_form(
    pet_id: str,
    user: dict = Depends(get_current_user_info_from_session)
):
    """
    Deleta um pet a partir da submissão do formulário.
    """
    user_id = user["id"]
    result = pets_collection.delete_one({"_id": ObjectId(pet_id), "users": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado ou você não tem permissão para excluí-lo."
        )
    
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/pets/{pet_id}/edit")
def edit_pet_page(
    pet_id: str,
    request: Request,
    user: dict = Depends(get_current_user_info_from_session)
):
    """
    Renderiza a página com o formulário pré-preenchido para editar um pet.
    """
    user_id = user["id"]
    pet = pets_collection.find_one({"_id": ObjectId(pet_id), "users": user_id})
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado ou você não tem permissão para editar."
        )
    pet["_id"] = str(pet["_id"])
    return templates.TemplateResponse(
        "pet_form.html",
        {"request": request, "pet": pet}
    )


@app.get("/pets/form")
def pet_form_page(request: Request, user: dict = Depends(get_current_user_info_from_session)):
    """
    Renderiza o formulário para adicionar ou editar um pet.
    """
    return templates.TemplateResponse("pet_form.html", {"request": request, "pet": None})