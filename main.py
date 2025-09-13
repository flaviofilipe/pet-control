import os
import requests
import time
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    Header,
    Depends,
    status,
    Request,
    Response,
    Form,
    Query,
    UploadFile,
    File,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse, JSONResponse
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from bson import ObjectId
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
import random
from faker import Faker
from faker_food import FoodProvider
import logging
import uuid
import shutil
from pathlib import Path
from PIL import Image
import io


logging.basicConfig(level=logging.ERROR)

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
VACCINES_COLLECTION_NAME = "vacinas"
ECTOPARASITES_COLLECTION_NAME = "ectoparasitas"
VERMIFUGOS_COLLECTION_NAME = "vermifugos"

# File upload configuration
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Extensões permitidas baseadas no suporte disponível
BASE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_EXTENSIONS = BASE_EXTENSIONS

THUMBNAIL_SIZE = (300, 300)

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    profiles_collection = db[COLLECTION_NAME]
    pets_collection = db[PETS_COLLECTION_NAME]
    vaccines_collection = db[VACCINES_COLLECTION_NAME]
    ectoparasites_collection = db[ECTOPARASITES_COLLECTION_NAME]
    vermifugos_collection = db[VERMIFUGOS_COLLECTION_NAME]
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
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Tratamento de erro global para redirecionar usuários não autenticados
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Tratamento global de exceções HTTP.
    Redireciona usuários não autenticados para a tela de login.
    """
    if exc.status_code == 401:
        # Para rotas que renderizam templates, redireciona para login
        return RedirectResponse(url="/login", status_code=302)
    elif exc.status_code == 408:
        # Para timeouts, retorna uma página de erro amigável
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_code": 408,
                "error_title": "Timeout",
                "error_message": "A requisição demorou muito para responder. Tente novamente.",
                "show_retry": True
            },
            status_code=408
        )
    
    # Para outras exceções HTTP, retorna a resposta padrão
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Inicializa Faker e adiciona provedor de alimentos
fake = Faker("pt_BR")
fake.add_provider(FoodProvider)

# Cache simples para evitar requisições desnecessárias ao Auth0
user_cache = {}
CACHE_DURATION = 300  # 5 minutos

def clear_user_cache(user_id: str = None):
    """Limpa o cache de usuários. Se user_id for fornecido, limpa apenas esse usuário."""
    if user_id:
        # Remove entradas que contenham o user_id
        keys_to_remove = [key for key in user_cache.keys() if user_id in str(user_cache[key][0])]
        for key in keys_to_remove:
            del user_cache[key]
    else:
        # Limpa todo o cache
        user_cache.clear()

# Cria diretório de uploads se não existir
UPLOAD_DIR.mkdir(exist_ok=True)


# Funções para manipulação de arquivos
def validate_image_file(file: UploadFile) -> tuple[bool, str]:
    """
    Valida se o arquivo é uma imagem válida.
    Retorna (is_valid, error_message)
    """
    if not file.filename:
        return False, "Nenhum arquivo selecionado"
    
    # Verifica extensão
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Formato de arquivo não suportado. Use: {', '.join(ALLOWED_EXTENSIONS).upper()}"
    
    # Verifica se é um arquivo HEIC (não suportado)
    if file_ext in ['.heic', '.heif']:
        return False, "Arquivos HEIC não são suportados. Use JPG, PNG, GIF ou WebP."
    
    # Verifica tamanho
    if file.size and file.size > MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE // (1024 * 1024)
        return False, f"Arquivo muito grande. Tamanho máximo: {max_size_mb}MB"
    
    return True, ""

def save_image_with_thumbnail(file: UploadFile, pet_id: str) -> dict:
    """
    Salva a imagem original e cria uma miniatura.
    Retorna um dicionário com os caminhos dos arquivos.
    """
    # Gera nome único para o arquivo
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{pet_id}_{uuid.uuid4().hex}{file_ext}"
    
    # Cria diretório específico para o pet
    pet_upload_dir = UPLOAD_DIR / pet_id
    pet_upload_dir.mkdir(exist_ok=True)
    
    # Caminhos dos arquivos
    original_path = pet_upload_dir / unique_filename
    thumbnail_path = pet_upload_dir / f"thumb_{unique_filename}"
    
    try:
        # Lê o arquivo
        contents = file.file.read()
        
        # Salva arquivo original
        with open(original_path, "wb") as f:
            f.write(contents)
        
        # Processa a imagem
        try:
            # Abre a imagem com PIL
            image = Image.open(io.BytesIO(contents))
                    
        except Exception as e:
            raise Exception(f"Formato de imagem não suportado: {str(e)}")
        
        # Converte para RGB se necessário
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Redimensiona mantendo proporção
        image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        
        # Salva miniatura
        image.save(thumbnail_path, "JPEG", quality=85, optimize=True)
        
        return {
            "original": str(original_path),
            "thumbnail": str(thumbnail_path),
            "filename": unique_filename
        }
        
    except Exception as e:
        # Remove arquivos em caso de erro
        if original_path.exists():
            original_path.unlink()
        if thumbnail_path.exists():
            thumbnail_path.unlink()
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao processar imagem: {str(e)}"
        )

def delete_pet_images(pet_id: str):
    """
    Remove todas as imagens de um pet.
    """
    pet_upload_dir = UPLOAD_DIR / pet_id
    if pet_upload_dir.exists():
        shutil.rmtree(pet_upload_dir)

# Funções para buscar raças
def get_dog_breeds_list():
    url = "https://dog.ceo/api/breeds/list/all"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        breeds_data = response.json()
        all_breeds = []
        for breed, sub_breeds in breeds_data["message"].items():
            if sub_breeds:
                for sub_breed in sub_breeds:
                    all_breeds.append(f"{sub_breed} {breed}".title())
            else:
                all_breeds.append(breed.title())
        return all_breeds
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar raças de cachorro: {e}")
        return []


def get_cat_breeds_list():
    url = "https://api.thecatapi.com/v1/breeds"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        breeds_data = response.json()
        cat_breeds = [breed["name"] for breed in breeds_data]
        return cat_breeds
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar raças de gato: {e}")
        return []


# ---
# Dependências
# ---
def refresh_auth_token(refresh_token: str) -> dict:
    """Renova o token de acesso usando o refresh token."""
    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        headers=headers,
        data=payload,
        timeout=30,  # Aumentado de 10s para 30s
    )
    response.raise_for_status()
    return response.json()


def get_current_user_info_from_session(request: Request) -> dict | Exception:
    """
    Dependência para obter informações do usuário a partir da sessão.
    Renova o token automaticamente se necessário.
    """
    access_token = request.session.get("access_token")
    refresh_token = request.session.get("refresh_token")
    
    # Verifica se há um flag de refresh em andamento para evitar loops
    if request.session.get("refreshing_token"):
        print("Token refresh already in progress, clearing session to avoid loop")
        request.session.clear()
        raise HTTPException(status_code=401, detail="Authentication loop detected. Please log in again.")

    if not access_token:
        # Lança exceção para que o FastAPI lide com o redirecionamento
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")

    # Verifica cache primeiro
    cache_key = f"user_{access_token[:20]}"  # Usa parte do token como chave
    current_time = time.time()
    
    if cache_key in user_cache:
        cached_data, cache_time = user_cache[cache_key]
        if current_time - cache_time < CACHE_DURATION:
            print("Using cached user info")
            return cached_data
        else:
            # Remove cache expirado
            del user_cache[cache_key]

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(
            f"https://{AUTH0_DOMAIN}/userinfo",
            headers=headers,
            timeout=30,  # Aumentado de 10s para 30s
        )
        response.raise_for_status()
        user_info = response.json()
        user_id = user_info.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token.")

        result = {"id": user_id, "info": user_info}
        
        # Armazena no cache
        user_cache[cache_key] = (result, current_time)
        
        return result
    except requests.exceptions.Timeout:
        print("Auth0 UserInfo request timed out")
        # Para timeouts, não limpa a sessão, apenas relança a exceção
        raise HTTPException(status_code=408, detail="Request timeout. Please try again.")
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401 and refresh_token:
            print("Access token expired, attempting to refresh...")
            try:
                # Marca que está fazendo refresh para evitar loops
                request.session["refreshing_token"] = True
                
                new_tokens = refresh_auth_token(refresh_token)
                new_access_token = new_tokens.get("access_token")
                new_refresh_token = new_tokens.get("refresh_token", refresh_token)

                request.session["access_token"] = new_access_token
                request.session["refresh_token"] = new_refresh_token
                # Remove o flag de refresh
                request.session.pop("refreshing_token", None)
                
                # Limpa o cache antigo
                old_cache_key = f"user_{access_token[:20]}"
                if old_cache_key in user_cache:
                    del user_cache[old_cache_key]

                print("Token refreshed successfully. Retrying request.")

                # Tenta novamente com o novo token
                headers["Authorization"] = f"Bearer {new_access_token}"
                response = requests.get(
                    f"https://{AUTH0_DOMAIN}/userinfo",
                    headers=headers,
                    timeout=30,  # Aumentado de 10s para 30s
                )
                response.raise_for_status()
                user_info = response.json()
                user_id = user_info.get("sub")

                result = {"id": user_id, "info": user_info}
                
                # Armazena no cache com a nova chave
                new_cache_key = f"user_{new_access_token[:20]}"
                user_cache[new_cache_key] = (result, current_time)
                
                return result
            except requests.exceptions.Timeout:
                print("Token refresh request timed out")
                request.session.pop("refreshing_token", None)
                raise HTTPException(status_code=408, detail="Token refresh timeout. Please try again.")
            except requests.exceptions.RequestException as refresh_err:
                print(f"Token refresh failed: {refresh_err}. Forcing re-login.")
                request.session.clear()
                # Lança exceção para que o FastAPI lide com o redirecionamento
                raise HTTPException(
                    status_code=401,
                    detail="Could not refresh credentials. Please log in again.",
                )
        else:
            print(f"Auth0 UserInfo request failed with HTTP error: {http_err}")
            # Para outros erros HTTP, limpa a sessão
            request.session.clear()
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except requests.exceptions.RequestException as e:
        print(f"Auth0 UserInfo request failed: {e}")
        logging.error(f"Auth0 UserInfo request failed: {e}")
        
        # Para erros de rede, não limpa a sessão imediatamente
        if "timeout" in str(e).lower():
            raise HTTPException(status_code=408, detail="Network timeout. Please try again.")
        else:
            # Para outros erros de rede, limpa a sessão
            request.session.clear()
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


# Novo modelo para Tratamentos
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


class PetBase(BaseModel):
    name: str
    breed: str
    pedigree_number: str | None = None
    birth_date: str
    pet_type: PetType
    treatments: List[Treatment] = []
    deleted_at: Optional[datetime] = None
    nickname: Optional[str] = None  # Novo campo para o nickname
    gender: Optional[Literal["male", "female"]] = None  # Novo campo para o gênero


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
    Sempre força o usuário a digitar as credenciais.
    """
    return RedirectResponse(
        url=f"https://{AUTH0_DOMAIN}/authorize?audience={AUTH0_API_AUDIENCE}&response_type=code&client_id={CLIENT_ID}&scope=offline_access openid profile email&redirect_uri={AUTH0_CALLBACK_URI}&prompt=login"
    )


@app.get("/dashboard", name="dashboard")
def get_dashboard_page(
    request: Request, user: dict = Depends(get_current_user_info_from_session)
):
    """
    Renderiza a página do dashboard para usuários autenticados,
    passando os dados do usuário e a lista de pets para o template.
    """
    try:
        is_authenticated = "access_token" in request.session
        user_id = user["id"]
        # Filtra apenas pets que não foram deletados
        pets_cursor = pets_collection.find({"users": user_id, "deleted_at": None})
        pets_list = []
        for pet in pets_cursor:
            pet["_id"] = str(pet["_id"])
            if "treatments" in pet:
                for treatment in pet["treatments"]:
                    treatment["_id"] = str(treatment["_id"])
            pets_list.append(pet)

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "is_authenticated": is_authenticated,
                "current_year": 2024,
                "user_info": user["info"],
                "pets": pets_list,
            },
        )
    except HTTPException as e:
        print(f"Error fetching dashboard data: {e}")


@app.get("/vacinas")
def get_vaccines_page(
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
    search: Optional[str] = None,
    especie: Optional[str] = None,
    tipo: Optional[str] = None,
):
    """
    Renderiza a página de vacinas com informações detalhadas sobre cada tipo.
    """
    try:
        # Filtros de busca
        filter_query = {}
        
        if search:
            filter_query["$or"] = [
                {"nome_vacina": {"$regex": search, "$options": "i"}},
                {"descricao": {"$regex": search, "$options": "i"}},
                {"protege_contra": {"$regex": search, "$options": "i"}}
            ]
        
        if especie:
            filter_query["especie_alvo"] = especie
        
        if tipo:
            filter_query["tipo_vacina"] = tipo
        
        # Busca vacinas com filtros
        vacinas = list(vaccines_collection.find(filter_query).sort("nome_vacina", 1))
        
        # Converte ObjectId para string
        for vacina in vacinas:
            vacina["_id"] = str(vacina["_id"])
        
        # Busca opções para filtros
        especies = list(vaccines_collection.distinct("especie_alvo"))
        tipos = list(vaccines_collection.distinct("tipo_vacina"))
        
        return templates.TemplateResponse(
            "pages/vacinas.html",
            {
                "request": request,
                "user": user,
                "vacinas": vacinas,
                "especies": especies,
                "tipos": tipos,
                "search": search or "",
                "especie_filter": especie or "",
                "tipo_filter": tipo or "",
                "total_vacinas": len(vacinas)
            },
        )
        
    except Exception as e:
        print(f"Error fetching vaccines data: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar dados das vacinas")


@app.get("/ectoparasitas")
def get_ectoparasites_page(
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
    search: Optional[str] = None,
    especie: Optional[str] = None,
    tipo: Optional[str] = None,
):
    """
    Renderiza a página de ectoparasitas com informações detalhadas sobre cada tipo.
    """
    try:
        # Filtros de busca
        filter_query = {}
        
        if search:
            filter_query["$or"] = [
                {"nome_praga": {"$regex": search, "$options": "i"}},
                {"transmissor_de_doencas": {"$regex": search, "$options": "i"}},
                {"sintomas_no_animal": {"$regex": search, "$options": "i"}},
                {"medicamentos_de_combate.descricao": {"$regex": search, "$options": "i"}},
                {"medicamentos_de_combate.principios_ativos": {"$regex": search, "$options": "i"}},
                {"observacoes_adicionais": {"$regex": search, "$options": "i"}}
            ]
        
        if especie:
            filter_query["especies_alvo"] = especie
        
        if tipo:
            filter_query["tipo_praga"] = tipo
        
        # Busca ectoparasitas com filtros
        ectoparasitas = list(ectoparasites_collection.find(filter_query).sort("nome_praga", 1))
        
        # Converte ObjectId para string
        for ectoparasita in ectoparasitas:
            ectoparasita["_id"] = str(ectoparasita["_id"])
        
        # Busca opções para filtros
        especies = list(ectoparasites_collection.distinct("especies_alvo"))
        # Flatten da lista de listas
        especies_flat = []
        for especie_list in especies:
            if isinstance(especie_list, list):
                especies_flat.extend(especie_list)
            else:
                especies_flat.append(especie_list)
        especies = list(set(especies_flat))  # Remove duplicatas
        
        tipos = list(ectoparasites_collection.distinct("tipo_praga"))
        
        return templates.TemplateResponse(
            "pages/ectoparasitas.html",
            {
                "request": request,
                "user": user,
                "ectoparasitas": ectoparasitas,
                "especies": especies,
                "tipos": tipos,
                "search": search or "",
                "especie_filter": especie or "",
                "tipo_filter": tipo or "",
                "total_ectoparasitas": len(ectoparasitas)
            },
        )
        
    except Exception as e:
        print(f"Error fetching ectoparasites data: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar dados dos ectoparasitas")


@app.get("/vermifugos")
def get_vermifugos_page(
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
    search: Optional[str] = None,
    especie: Optional[str] = None,
    tipo: Optional[str] = None,
):
    """
    Renderiza a página de vermífugos com informações detalhadas sobre cada tipo.
    """
    try:
        # Busca o documento principal que contém todos os vermífugos
        vermifugos_doc = vermifugos_collection.find_one()
        
        if not vermifugos_doc:
            vermifugos_list = []
        else:
            vermifugos_list = vermifugos_doc.get("parasitas_e_tratamentos", [])
        
        # Aplica filtros se fornecidos
        if search:
            search_lower = search.lower()
            vermifugos_list = [
                v for v in vermifugos_list 
                if search_lower in v.get("nome_praga", "").lower()
                or search_lower in v.get("tipo_praga", "").lower()
                or any(search_lower in sintoma.lower() for sintoma in v.get("sintomas_no_animal", []))
                or any(search_lower in med.get("descricao", "").lower() for med in v.get("medicamentos_de_combate", []))
                or any(search_lower in principio.lower() for med in v.get("medicamentos_de_combate", []) for principio in med.get("principios_ativos", []))
                or search_lower in v.get("observacoes_adicionais", "").lower()
            ]
        
        if especie:
            vermifugos_list = [
                v for v in vermifugos_list 
                if especie in v.get("especies_alvo", [])
            ]
        
        if tipo:
            vermifugos_list = [
                v for v in vermifugos_list 
                if v.get("tipo_praga") == tipo
            ]
        
        # Adiciona ID único para cada vermífugo para compatibilidade com templates
        for i, vermifugo in enumerate(vermifugos_list):
            vermifugo["_id"] = str(i)
        
        # Busca opções para filtros
        all_vermifugos = vermifugos_doc.get("parasitas_e_tratamentos", []) if vermifugos_doc else []
        especies = list(set([especie for v in all_vermifugos for especie in v.get("especies_alvo", [])]))
        tipos = list(set([v.get("tipo_praga") for v in all_vermifugos if v.get("tipo_praga")]))
        
        return templates.TemplateResponse(
            "pages/vermifugos.html",
            {
                "request": request,
                "user": user,
                "vermifugos": vermifugos_list,
                "especies": especies,
                "tipos": tipos,
                "search": search or "",
                "especie_filter": especie or "",
                "tipo_filter": tipo or "",
                "total_vermifugos": len(vermifugos_list)
            },
        )
        
    except Exception as e:
        print(f"Error fetching vermifugos data: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar dados dos vermífugos")


@app.get("/api/vacinas/autocomplete")
def get_vaccines_autocomplete(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    user: dict = Depends(get_current_user_info_from_session),
):
    """
    Endpoint para autocomplete de vacinas.
    Retorna sugestões baseadas no nome da vacina.
    """
    try:
        if len(q) < 1:
            return {"suggestions": []}
        
        # Busca vacinas que começam com o termo digitado
        filter_query = {
            "nome_vacina": {"$regex": f"^{q}", "$options": "i"}
        }
        
        # Busca até 10 sugestões
        vacinas = list(vaccines_collection.find(filter_query)
                      .limit(10)
                      .sort("nome_vacina", 1))
        
        suggestions = []
        for vacina in vacinas:
            suggestions.append({
                "id": str(vacina["_id"]),
                "nome": vacina["nome_vacina"],
                "especie": vacina["especie_alvo"],
                "tipo": vacina["tipo_vacina"]
            })
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        print(f"Error in vaccines autocomplete: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar sugestões")


@app.get("/api/ectoparasitas/autocomplete")
def get_ectoparasites_autocomplete(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    user: dict = Depends(get_current_user_info_from_session),
):
    """
    Endpoint para autocomplete de ectoparasitas.
    Retorna sugestões baseadas no nome da praga.
    """
    try:
        if len(q) < 1:
            return {"suggestions": []}
        
        # Busca ectoparasitas que começam com o termo digitado ou contêm o termo
        filter_query = {
            "$or": [
                {"nome_praga": {"$regex": f"^{q}", "$options": "i"}},
                {"nome_praga": {"$regex": q, "$options": "i"}},
                {"transmissor_de_doencas": {"$regex": q, "$options": "i"}},
                {"sintomas_no_animal": {"$regex": q, "$options": "i"}},
                {"medicamentos_de_combate.principios_ativos": {"$regex": q, "$options": "i"}}
            ]
        }
        
        # Busca até 10 sugestões
        ectoparasitas = list(ectoparasites_collection.find(filter_query)
                           .limit(10)
                           .sort("nome_praga", 1))
        
        suggestions = []
        for ectoparasita in ectoparasitas:
            especies = ", ".join(ectoparasita["especies_alvo"])
            
            # Determina onde o termo foi encontrado para mostrar contexto
            match_context = ""
            if q.lower() in ectoparasita["nome_praga"].lower():
                match_context = "Nome"
            elif any(q.lower() in doenca.lower() for doenca in ectoparasita.get("transmissor_de_doencas", [])):
                match_context = "Doença"
            elif any(q.lower() in sintoma.lower() for sintoma in ectoparasita.get("sintomas_no_animal", [])):
                match_context = "Sintoma"
            elif any(q.lower() in principio.lower() for medicamento in ectoparasita.get("medicamentos_de_combate", []) for principio in medicamento.get("principios_ativos", [])):
                match_context = "Princípio Ativo"
            
            suggestions.append({
                "id": str(ectoparasita["_id"]),
                "nome": ectoparasita["nome_praga"],
                "especies": especies,
                "tipo": ectoparasita["tipo_praga"],
                "contexto": match_context
            })
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        print(f"Error in ectoparasites autocomplete: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar sugestões")


@app.get("/api/vermifugos/autocomplete")
def get_vermifugos_autocomplete(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    user: dict = Depends(get_current_user_info_from_session),
):
    """
    Endpoint para autocomplete de vermífugos.
    Retorna sugestões baseadas no nome da praga e outros campos.
    """
    try:
        if len(q) < 1:
            return {"suggestions": []}
        
        # Busca o documento principal que contém todos os vermífugos
        vermifugos_doc = vermifugos_collection.find_one()
        
        if not vermifugos_doc:
            return {"suggestions": []}
        
        vermifugos_list = vermifugos_doc.get("parasitas_e_tratamentos", [])
        suggestions = []
        
        # Busca vermífugos que contenham o termo pesquisado
        for i, vermifugo in enumerate(vermifugos_list):
            q_lower = q.lower()
            match_found = False
            match_context = ""
            
            # Verifica se o termo está no nome da praga
            if q_lower in vermifugo.get("nome_praga", "").lower():
                match_found = True
                match_context = "Nome"
            
            # Verifica se o termo está no tipo de praga
            elif q_lower in vermifugo.get("tipo_praga", "").lower():
                match_found = True
                match_context = "Tipo"
            
            # Verifica se o termo está nos sintomas
            elif any(q_lower in sintoma.lower() for sintoma in vermifugo.get("sintomas_no_animal", [])):
                match_found = True
                match_context = "Sintoma"
            
            # Verifica se o termo está nos princípios ativos
            elif any(q_lower in principio.lower() for med in vermifugo.get("medicamentos_de_combate", []) for principio in med.get("principios_ativos", [])):
                match_found = True
                match_context = "Princípio Ativo"
            
            # Verifica se o termo está nas observações
            elif q_lower in vermifugo.get("observacoes_adicionais", "").lower():
                match_found = True
                match_context = "Observações"
            
            if match_found:
                especies = ", ".join(vermifugo.get("especies_alvo", []))
                
                suggestions.append({
                    "id": str(i),
                    "nome": vermifugo.get("nome_praga", ""),
                    "especies": especies,
                    "tipo": vermifugo.get("tipo_praga", ""),
                    "contexto": match_context
                })
                
                # Limita a 10 sugestões
                if len(suggestions) >= 10:
                    break
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        print(f"Error in vermifugos autocomplete: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar sugestões")


@app.get("/callback")
def callback(request: Request, code: str):
    """
    Manipula o redirecionamento do Auth0 após a autenticação.
    Armazena o token de acesso e o refresh token na sessão.
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
            timeout=30,  # Aumentado de 10s para 30s
        )
        response.raise_for_status()
        token_info = response.json()

        # Armazena ambos os tokens na sessão
        request.session["access_token"] = token_info.get("access_token")
        request.session["refresh_token"] = token_info.get("refresh_token")

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
    Limpa a sessão e faz logout completo do Auth0.
    """
    # Limpa o cache do usuário antes de limpar a sessão
    access_token = request.session.get("access_token")
    if access_token:
        cache_key = f"user_{access_token[:20]}"
        if cache_key in user_cache:
            del user_cache[cache_key]
    
    request.session.clear()
    
    # URL de logout do Auth0 que força o usuário a digitar credenciais novamente
    auth0_logout_url = f"https://{AUTH0_DOMAIN}/v2/logout?client_id={CLIENT_ID}&returnTo={request.base_url}"
    
    return RedirectResponse(url=auth0_logout_url)


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


# Pet Endpoints
@app.get("/pets/form")
def pet_form_page(
    request: Request, 
    user: dict = Depends(get_current_user_info_from_session),
    error: str = Query(None),
    pet_id: str = Query(None)
):
    """
    Renderiza o formulário para adicionar um novo pet.
    """
    dog_breeds = get_dog_breeds_list()
    cat_breeds = get_cat_breeds_list()
    
    # Busca pet para edição se pet_id for fornecido
    pet = None
    if pet_id:
        try:
            pet = pets_collection.find_one(
                {"_id": ObjectId(pet_id), "users": user["id"], "deleted_at": None}
            )
        except Exception:
            pass

    return templates.TemplateResponse(
        "pet_form.html",
        {
            "request": request,
            "pet": pet,
            "dog_breeds": dog_breeds,
            "cat_breeds": cat_breeds,
            "error": error,
            "supported_formats": list(ALLOWED_EXTENSIONS),
        },
    )


@app.get("/pets/{pet_id}/edit")
def edit_pet_page(
    pet_id: str,
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
):
    """
    Renderiza a página com o formulário pré-preenchido para editar um pet.
    """
    user_id = user["id"]
    pet = pets_collection.find_one(
        {"_id": ObjectId(pet_id), "users": user_id, "deleted_at": None}
    )
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado ou você não tem permissão para editar.",
        )
    pet["_id"] = str(pet["_id"])

    dog_breeds = get_dog_breeds_list()
    cat_breeds = get_cat_breeds_list()

    return templates.TemplateResponse(
        "pet_form.html",
        {
            "request": request,
            "pet": pet,
            "dog_breeds": dog_breeds,
            "cat_breeds": cat_breeds,
        },
    )


@app.get("/pets/{pet_id}/profile")
def pet_profile_page(
    pet_id: str,
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
    search: Optional[str] = None,
):
    """
    Renderiza a página de perfil do pet, com detalhes e tratamentos.
    """
    user_id = user["id"]
    pet = pets_collection.find_one(
        {"_id": ObjectId(pet_id), "users": user_id, "deleted_at": None}
    )

    if not pet:
        raise HTTPException(status_code=404, detail="Pet não encontrado.")

    pet["_id"] = str(pet["_id"])

    # Calcula a idade do pet e formata a data
    try:
        birth_date_str = pet.get("birth_date", "")
        if not birth_date_str:
            pet["age"] = "Data não informada"
            pet["birth_date_formatted"] = "Não informada"
        else:
            # Tenta diferentes formatos de data
            birth_date = None
            try:
                # Formato YYYY-MM-DD (do input type="date")
                birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            except ValueError:
                try:
                    # Formato DD/MM/YYYY (formato brasileiro)
                    birth_date = datetime.strptime(birth_date_str, "%d/%m/%Y").date()
                except ValueError:
                    # Formato MM/DD/YYYY (formato americano)
                    birth_date = datetime.strptime(birth_date_str, "%m/%d/%Y").date()
            
            # Formata a data para exibição (DD/MM/YYYY)
            pet["birth_date_formatted"] = birth_date.strftime("%d/%m/%Y")
            
            # Calcula a idade
            today = datetime.now().date()
            age_years = today.year - birth_date.year
            age_months = today.month - birth_date.month
            
            if age_months < 0:
                age_years -= 1
                age_months += 12
            
            # Ajusta se o dia ainda não chegou
            if today.day < birth_date.day:
                age_months -= 1
                if age_months < 0:
                    age_years -= 1
                    age_months += 12
            
            # Formata a idade
            if age_years > 0:
                if age_months > 0:
                    pet["age"] = f"{age_years} ano{'s' if age_years > 1 else ''} e {age_months} mês{'es' if age_months > 1 else ''}"
                else:
                    pet["age"] = f"{age_years} ano{'s' if age_years > 1 else ''}"
            else:
                pet["age"] = f"{age_months} mês{'es' if age_months > 1 else ''}"
    except (ValueError, TypeError):
        pet["age"] = "Data de nascimento inválida"
        pet["birth_date_formatted"] = pet.get("birth_date", "Data inválida")

    # Processa os tratamentos e aplica o filtro
    treatments = pet.get("treatments", [])

    # Separa tratamentos expirados, agendados e concluídos
    today = datetime.now().date()
    scheduled_treatments = []
    expired_treatments = []
    done_treatments = []

    for t in treatments:
        treatment_date = datetime.strptime(t.get("date"), "%Y-%m-%d").date()
        t["_id"] = str(t["_id"])  # Garante que o ID é string
        
        # Formata a data para exibição (DD/MM/YYYY)
        t["date_formatted"] = treatment_date.strftime("%d/%m/%Y")

        if t.get("done"):
            done_treatments.append(t)
        elif treatment_date > today:
            scheduled_treatments.append(t)
        else:
            expired_treatments.append(t)

    # Aplica o filtro de pesquisa, se houver
    if search:
        search_lower = search.lower()
        scheduled_treatments = [
            t
            for t in scheduled_treatments
            if search_lower in t.get("name", "").lower()
            or search_lower in t.get("category", "").lower()
            or search_lower in t.get("date", "").lower()
        ]
        expired_treatments = [
            t
            for t in expired_treatments
            if search_lower in t.get("name", "").lower()
            or search_lower in t.get("category", "").lower()
            or search_lower in t.get("date", "").lower()
        ]
        done_treatments = [
            t
            for t in done_treatments
            if search_lower in t.get("name", "").lower()
            or search_lower in t.get("category", "").lower()
            or search_lower in t.get("date", "").lower()
        ]

    # Ordena os tratamentos por data
    scheduled_treatments.sort(
        key=lambda x: datetime.strptime(x.get("date"), "%Y-%m-%d")
    )
    expired_treatments.sort(key=lambda x: datetime.strptime(x.get("date"), "%Y-%m-%d"))
    done_treatments.sort(
        key=lambda x: datetime.strptime(x.get("date"), "%Y-%m-%d"), reverse=True
    )

    return templates.TemplateResponse(
        "pet_profile.html",
        {
            "request": request,
            "pet": pet,
            "scheduled_treatments": scheduled_treatments,
            "expired_treatments": expired_treatments,
            "done_treatments": done_treatments,
        },
    )


@app.post("/pets")
async def create_or_update_pet_from_form(
    user: dict = Depends(get_current_user_info_from_session),
    pet_id: str | None = Form(None),
    name: str = Form(...),
    breed: str = Form(...),
    pedigree_number: str | None = Form(None),
    birth_date: str = Form(...),
    pet_type: PetType = Form(...),
    gender: Optional[Literal["male", "female"]] = Form(None),
    photo: UploadFile = File(None),
):
    """
    Cria ou atualiza um pet a partir do formulário HTML.
    """
    user_id = user["id"]

    # Processa imagem se fornecida
    photo_data = None
    if photo and photo.filename:
        is_valid, error_message = validate_image_file(photo)
        if not is_valid:
            # Redireciona com mensagem de erro user-friendly
            return RedirectResponse(
                url=f"/pets/form?error={error_message}&pet_id={pet_id or ''}",
                status_code=302
            )
        
        # Se for atualização, remove imagem antiga
        if pet_id:
            old_pet = pets_collection.find_one({"_id": ObjectId(pet_id)})
            if old_pet and "photo" in old_pet:
                try:
                    old_photo_path = Path(old_pet["photo"]["original"])
                    if old_photo_path.exists():
                        old_photo_path.unlink()
                    old_thumb_path = Path(old_pet["photo"]["thumbnail"])
                    if old_thumb_path.exists():
                        old_thumb_path.unlink()
                except Exception:
                    pass  # Ignora erros ao remover arquivos antigos
        
        # Salva nova imagem
        photo_data = save_image_with_thumbnail(photo, pet_id or "temp")

    pet_data = {
        "name": name,
        "breed": breed,
        "pedigree_number": pedigree_number,
        "birth_date": birth_date,
        "pet_type": pet_type,
        "users": [user_id],
        "gender": gender,
    }

    if pet_id:
        # Lógica de atualização
        if photo_data:
            pet_data["photo"] = photo_data
        
        result = pets_collection.update_one(
            {"_id": ObjectId(pet_id), "users": user_id, "deleted_at": None},
            {"$set": pet_data},
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pet não encontrado ou você não tem permissão para editar.",
            )
        
        # Move arquivo da pasta temporária para a pasta correta
        if photo_data and photo_data.get("original"):
            temp_path = Path(photo_data["original"])
            if temp_path.exists():
                final_path = UPLOAD_DIR / pet_id / temp_path.name
                final_path.parent.mkdir(exist_ok=True)
                shutil.move(str(temp_path), str(final_path))
                
                # Atualiza caminhos no banco
                photo_data["original"] = str(final_path)
                photo_data["thumbnail"] = str(final_path.parent / f"thumb_{temp_path.name}")
                
                pets_collection.update_one(
                    {"_id": ObjectId(pet_id)},
                    {"$set": {"photo": photo_data}}
                )
    else:
        # Gera nickname único
        base_name = name.split()[0].lower()
        nickname = None
        attempts = 0
        max_attempts = 100
        
        while nickname is None and attempts < max_attempts:
            random_code = "".join(random.choices("0123456789", k=4))
            candidate_nickname = f"{base_name}_{random_code}"
            
            # Verifica se o nickname já existe
            existing_pet = pets_collection.find_one({"nickname": candidate_nickname})
            if not existing_pet:
                nickname = candidate_nickname
            else:
                attempts += 1
        
        # Se não conseguiu gerar um nickname único, usa timestamp
        if nickname is None:
            import time
            timestamp = str(int(time.time()))[-6:]  # Últimos 6 dígitos do timestamp
            nickname = f"{base_name}_{timestamp}"

        # Lógica de criação
        pet_data["treatments"] = []
        pet_data["deleted_at"] = None
        pet_data["nickname"] = nickname
        
        if photo_data:
            pet_data["photo"] = photo_data
        
        result = pets_collection.insert_one(pet_data)
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao criar pet.",
            )
        
        # Move arquivo da pasta temporária para a pasta correta
        if photo_data and photo_data.get("original"):
            temp_path = Path(photo_data["original"])
            if temp_path.exists():
                final_path = UPLOAD_DIR / str(result.inserted_id) / temp_path.name
                final_path.parent.mkdir(exist_ok=True)
                shutil.move(str(temp_path), str(final_path))
                
                # Atualiza caminhos no banco
                photo_data["original"] = str(final_path)
                photo_data["thumbnail"] = str(final_path.parent / f"thumb_{temp_path.name}")
                
                pets_collection.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"photo": photo_data}}
                )

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/pets/{pet_id}/delete")
def delete_pet_from_form(
    pet_id: str, user: dict = Depends(get_current_user_info_from_session)
):
    """
    Realiza o soft delete de um pet.
    """
    user_id = user["id"]
    
    # Busca o pet para verificar se tem fotos
    pet = pets_collection.find_one(
        {"_id": ObjectId(pet_id), "users": user_id, "deleted_at": None}
    )
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado ou você não tem permissão para excluí-lo.",
        )
    
    # Remove as imagens do pet
    if pet.get("photo"):
        try:
            delete_pet_images(pet_id)
        except Exception:
            pass  # Ignora erros ao remover arquivos
    
    result = pets_collection.update_one(
        {"_id": ObjectId(pet_id), "users": user_id, "deleted_at": None},
        {"$set": {"deleted_at": datetime.now()}},
    )

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


# --- ROTAS PARA TRATAMENTOS ---


@app.get("/pets/{pet_id}/treatments/add")
def add_treatment_page(
    pet_id: str,
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
):
    pet = pets_collection.find_one(
        {"_id": ObjectId(pet_id), "users": user["id"], "deleted_at": None}
    )
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found.")

    return templates.TemplateResponse(
        "treatment_form.html", {"request": request, "pet": pet, "treatment": None, "user_info": user["info"]}
    )


@app.post("/pets/{pet_id}/treatments")
def create_or_update_treatment(
    pet_id: str,
    user: dict = Depends(get_current_user_info_from_session),
    treatment_id: Optional[str] = Form(None),
    category: str = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    date: str = Form(...),
    time: Optional[str] = Form(None),
    applier_type: str = Form(...),
    applier_name: Optional[str] = Form(None),
    applier_id: Optional[str] = Form(None),
    done: bool = Form(False),
):
    user_id = user["id"]
    
    # Se o usuário logado é um veterinário e applier_type é "Veterinarian",
    # adiciona automaticamente o veterinário à lista de usuários do pet
    if applier_type == "Veterinarian" and user["info"].get("is_vet", False):
        pets_collection.update_one(
            {"_id": ObjectId(pet_id), "deleted_at": None},
            {"$addToSet": {"users": user_id}}
        )

    # Validações e criação do subdocumento
    treatment_data = {
        "_id": ObjectId(treatment_id) if treatment_id else ObjectId(),
        "category": category,
        "name": name,
        "description": description,
        "date": date,
        "time": time,
        "applier_type": applier_type,
        "applier_name": applier_name,
        "applier_id": applier_id,
        "done": done,
    }

    if treatment_id:
        # Lógica de atualização
        result = pets_collection.update_one(
            {
                "_id": ObjectId(pet_id),
                "users": user_id,
                "deleted_at": None,
                "treatments._id": ObjectId(treatment_id),
            },
            {"$set": {"treatments.$": treatment_data}},
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Treatment not found or not authorized."
            )
    else:
        # Lógica de criação
        result = pets_collection.update_one(
            {"_id": ObjectId(pet_id), "users": user_id, "deleted_at": None},
            {"$push": {"treatments": treatment_data}},
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Pet not found or not authorized."
            )

    return RedirectResponse(
        url="/pets/" + pet_id + "/profile", status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/pets/{pet_id}/treatments/{treatment_id}/edit")
def edit_treatment_page(
    pet_id: str,
    treatment_id: str,
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
):
    user_id = user["id"]
    pet = pets_collection.find_one(
        {"_id": ObjectId(pet_id), "users": user_id, "deleted_at": None}
    )
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found.")

    treatment = next(
        (t for t in pet.get("treatments", []) if str(t["_id"]) == treatment_id), None
    )
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found.")

    treatment["_id"] = str(treatment["_id"])

    return templates.TemplateResponse(
        "treatment_form.html", {"request": request, "pet": pet, "treatment": treatment, "user_info": user["info"]}
    )


@app.post("/pets/{pet_id}/treatments/{treatment_id}/delete")
def delete_treatment(
    pet_id: str,
    treatment_id: str,
    user: dict = Depends(get_current_user_info_from_session),
):
    user_id = user["id"]

    result = pets_collection.update_one(
        {"_id": ObjectId(pet_id), "users": user_id, "deleted_at": None},
        {"$pull": {"treatments": {"_id": ObjectId(treatment_id)}}},
    )

    if result.matched_count == 0 or result.modified_count == 0:
        raise HTTPException(
            status_code=404, detail="Treatment not found or not authorized."
        )

    return RedirectResponse(
        url="/pets/" + pet_id + "/profile", status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/generate-pet-name")
def generate_pet_name(gender: str = Query(...)):
    """
    Gera uma lista de nomes de pet ou comidas baseada no gênero.
    """
    if gender not in ["male", "female"]:
        return {"names": ["Selecione um gênero válido."]}

    nomes_comuns_unissex = ["Pingo", "Bolinha", "Mel", "Pipoca", "Amora", "Jade", "Max"]
    nomes = []

    # 50% de chance de gerar nomes de pet ou de comida
    if random.choice([True, False]):
        # Nomes de pet
        if gender == "male":
            nomes.extend([fake.first_name_male() for _ in range(5)])
        else:
            nomes.extend([fake.first_name_female() for _ in range(5)])

        # Adiciona alguns nomes unissex
        nomes.extend(random.sample(nomes_comuns_unissex, 5))
    else:
        # Nomes de comida
        nomes.extend([fake.dish() for _ in range(10)])

    # Remove duplicatas e retorna a lista
    return {"names": list(set(nomes))}


# Rotas para gerenciamento de acesso de veterinários

@app.get("/api/search-veterinarians")
def search_veterinarians(
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
    search: str = Query(..., min_length=2),
):
    """
    Busca veterinários por nome para vinculação a pets.
    Apenas tutores podem buscar veterinários.
    """
    user_id = user["id"]
    
    # Busca veterinários que contenham o termo de busca no nome
    veterinarians_cursor = profiles_collection.find({
        "is_vet": True,
        "name": {"$regex": search, "$options": "i"},
        "_id": {"$ne": user_id}  # Exclui o próprio usuário
    }).limit(10)
    
    veterinarians = []
    for vet in veterinarians_cursor:
        veterinarians.append({
            "id": str(vet["_id"]),
            "name": vet.get("name", "Sem nome"),
            "email": vet.get("email", ""),
        })
    
    return JSONResponse(content={"veterinarians": veterinarians})


@app.post("/pets/{pet_id}/grant-access")
def grant_veterinarian_access(
    pet_id: str,
    user: dict = Depends(get_current_user_info_from_session),
    veterinarian_id: str = Form(...),
):
    """
    Concede acesso de um veterinário a um pet específico.
    Apenas o tutor do pet pode conceder acesso.
    """
    user_id = user["id"]
    
    # Verifica se o pet existe e se o usuário é o tutor
    pet = pets_collection.find_one({
        "_id": ObjectId(pet_id),
        "users": user_id,
        "deleted_at": None
    })
    
    if not pet:
        raise HTTPException(status_code=404, detail="Pet não encontrado ou sem permissão.")
    
    # Verifica se o veterinário existe
    vet = profiles_collection.find_one({
        "_id": veterinarian_id,
        "is_vet": True
    })
    
    if not vet:
        raise HTTPException(status_code=404, detail="Veterinário não encontrado.")
    
    # Adiciona o veterinário à lista de usuários do pet
    result = pets_collection.update_one(
        {"_id": ObjectId(pet_id)},
        {"$addToSet": {"users": veterinarian_id}}
    )
    
    if result.modified_count > 0:
        return JSONResponse(content={
            "success": True,
            "message": f"Acesso concedido ao veterinário {vet.get('name', 'Sem nome')} com sucesso!"
        })
    else:
        return JSONResponse(content={
            "success": True,
            "message": "O veterinário já tinha acesso a este pet."
        })


@app.post("/pets/{pet_id}/revoke-access")
def revoke_veterinarian_access(
    pet_id: str,
    user: dict = Depends(get_current_user_info_from_session),
    veterinarian_id: str = Form(...),
):
    """
    Remove o acesso de um veterinário a um pet específico.
    Apenas o tutor do pet pode remover acesso.
    """
    user_id = user["id"]
    
    # Verifica se o pet existe e se o usuário é o tutor
    pet = pets_collection.find_one({
        "_id": ObjectId(pet_id),
        "users": user_id,
        "deleted_at": None
    })
    
    if not pet:
        raise HTTPException(status_code=404, detail="Pet não encontrado ou sem permissão.")
    
    # Não permite remover o próprio tutor
    if veterinarian_id == user_id:
        raise HTTPException(status_code=400, detail="Você não pode remover seu próprio acesso.")
    
    # Remove o veterinário da lista de usuários do pet
    result = pets_collection.update_one(
        {"_id": ObjectId(pet_id)},
        {"$pull": {"users": veterinarian_id}}
    )
    
    if result.modified_count > 0:
        return JSONResponse(content={
            "success": True,
            "message": "Acesso do veterinário removido com sucesso!"
        })
    else:
        return JSONResponse(content={
            "success": False,
            "message": "Veterinário não tinha acesso a este pet."
        })


@app.get("/pets/{pet_id}/veterinarians")
def get_pet_veterinarians(
    pet_id: str,
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
):
    """
    Lista os veterinários que têm acesso ao pet.
    Apenas o tutor do pet pode ver esta lista.
    """
    user_id = user["id"]
    
    # Verifica se o pet existe e se o usuário é o tutor
    pet = pets_collection.find_one({
        "_id": ObjectId(pet_id),
        "users": user_id,
        "deleted_at": None
    })
    
    if not pet:
        raise HTTPException(status_code=404, detail="Pet não encontrado ou sem permissão.")
    
    # Busca todos os veterinários que têm acesso (exceto o tutor)
    veterinarian_ids = [uid for uid in pet.get("users", []) if uid != user_id]
    
    veterinarians = []
    if veterinarian_ids:
        vets_cursor = profiles_collection.find({
            "_id": {"$in": veterinarian_ids},
            "is_vet": True
        })
        
        for vet in vets_cursor:
            veterinarians.append({
                "id": str(vet["_id"]),
                "name": vet.get("name", "Sem nome"),
                "email": vet.get("email", ""),
            })
    
    return JSONResponse(content={"veterinarians": veterinarians})


@app.get("/vet-dashboard", name="vet_dashboard")
def get_vet_dashboard_page(
    request: Request, user: dict = Depends(get_current_user_info_from_session)
):
    """
    Renderiza o dashboard específico para veterinários.
    """
    try:
        is_authenticated = "access_token" in request.session
        user_id = user["id"]
        
        # Busca pets que o veterinário tem acesso
        pets_cursor = pets_collection.find({"users": user_id, "deleted_at": None})
        pets_list = []
        for pet in pets_cursor:
            pet["_id"] = str(pet["_id"])
            if "treatments" in pet:
                for treatment in pet["treatments"]:
                    treatment["_id"] = str(treatment["_id"])
            pets_list.append(pet)

        return templates.TemplateResponse(
            "vet_dashboard.html",
            {
                "request": request,
                "is_authenticated": is_authenticated,
                "current_year": 2024,
                "user_info": user["info"],
                "pets": pets_list,
            },
        )
    except HTTPException as e:
        print(f"Error fetching vet dashboard data: {e}")


@app.get("/api/search-pet-by-nickname")
def search_pet_by_nickname(
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
    nickname: str = Query(...),
):
    """
    Busca um pet pelo nickname para veterinários visualizarem informações básicas.
    """
    try:
        pet = pets_collection.find_one({
            "nickname": nickname, 
            "deleted_at": None
        })
        
        if not pet:
            return JSONResponse(
                content={"success": False, "message": "Pet não encontrado."},
                status_code=404
            )
        
        # Converte ObjectId para string
        pet["_id"] = str(pet["_id"])
        if "users" in pet:
            pet["users"] = [str(uid) for uid in pet["users"]]
        
        # Remove dados sensíveis se o veterinário não tem acesso
        user_id = user["id"]
        has_access = user_id in pet.get("users", [])
        
        if not has_access:
            # Remove informações detalhadas se não tem acesso
            pet = {
                "_id": pet["_id"],
                "name": pet.get("name"),
                "nickname": pet.get("nickname"),
                "breed": pet.get("breed"),
                "pet_type": pet.get("pet_type"),
                "gender": pet.get("gender"),
                "birth_date": pet.get("birth_date"),
                "has_access": False,
                "message": "Você não tem acesso ao histórico completo deste pet."
            }
        else:
            pet["has_access"] = True
            # Converte treatment IDs também
            if "treatments" in pet:
                for treatment in pet["treatments"]:
                    treatment["_id"] = str(treatment["_id"])
        
        return JSONResponse(content={"success": True, "pet": pet})
        
    except Exception as e:
        return JSONResponse(
            content={"success": False, "message": "Erro ao buscar pet."},
            status_code=500
        )


@app.get("/api/search-pet-by-id")
def search_pet_by_id(
    request: Request,
    user: dict = Depends(get_current_user_info_from_session),
    pet_id: str = Query(...),
):
    """
    Busca um pet pelo ID para veterinários visualizarem informações básicas.
    (Mantido para compatibilidade)
    """
    try:
        pet = pets_collection.find_one({
            "_id": ObjectId(pet_id), 
            "deleted_at": None
        })
        
        if not pet:
            return JSONResponse(
                content={"success": False, "message": "Pet não encontrado."},
                status_code=404
            )
        
        # Converte ObjectId para string
        pet["_id"] = str(pet["_id"])
        if "users" in pet:
            pet["users"] = [str(uid) for uid in pet["users"]]
        
        # Remove dados sensíveis se o veterinário não tem acesso
        user_id = user["id"]
        has_access = user_id in pet.get("users", [])
        
        if not has_access:
            # Remove informações detalhadas se não tem acesso
            pet = {
                "_id": pet["_id"],
                "name": pet.get("name"),
                "nickname": pet.get("nickname"),
                "breed": pet.get("breed"),
                "pet_type": pet.get("pet_type"),
                "gender": pet.get("gender"),
                "birth_date": pet.get("birth_date"),
                "has_access": False,
                "message": "Você não tem acesso ao histórico completo deste pet."
            }
        else:
            pet["has_access"] = True
            # Converte treatment IDs também
            if "treatments" in pet:
                for treatment in pet["treatments"]:
                    treatment["_id"] = str(treatment["_id"])
        
        return JSONResponse(content={"success": True, "pet": pet})
        
    except Exception as e:
        return JSONResponse(
            content={"success": False, "message": "Erro ao buscar pet."},
            status_code=500
        )
