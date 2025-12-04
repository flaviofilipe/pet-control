"""
Rotas de pets
"""

import requests
from datetime import datetime
from typing import Optional, Literal
from fastapi import APIRouter, HTTPException, Request, Depends, Form, Query, UploadFile, File, status
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import PetService, FileService, UserService
from app.schemas import PetType
from app.database.connection import get_db
from .auth_routes import get_current_user_from_session

# Configuração do Jinja2
templates = Jinja2Templates(directory="templates")

router = APIRouter()


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


@router.get("/pets/form")
async def pet_form_page(
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
    error: str = Query(None),
    pet_id: str = Query(None),
):
    """
    Renderiza o formulário para adicionar um novo pet.
    """
    dog_breeds = get_dog_breeds_list()
    cat_breeds = get_cat_breeds_list()

    # Busca pet para edição se pet_id for fornecido
    pet = None
    if pet_id:
        pet_service = PetService(db)
        pet = await pet_service.get_pet_details(pet_id, user["id"])

    from app.services.file_service import ALLOWED_EXTENSIONS
    
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


@router.get("/pets/{pet_id}/edit")
async def edit_pet_page(
    pet_id: str,
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Renderiza a página com o formulário pré-preenchido para editar um pet.
    """
    pet_service = PetService(db)
    pet = await pet_service.get_pet_details(pet_id, user["id"])
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado ou você não tem permissão para editar.",
        )

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


@router.get("/pets/{pet_id}/profile")
async def pet_profile_page(
    pet_id: str,
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = None,
):
    """
    Renderiza a página de perfil do pet, com detalhes e tratamentos.
    """
    pet_service = PetService(db)
    pet = await pet_service.get_pet_details(pet_id, user["id"])

    if not pet:
        raise HTTPException(status_code=404, detail="Pet não encontrado.")

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
                    pet["age"] = (
                        f"{age_years} ano{'s' if age_years > 1 else ''} e {age_months} mês{'es' if age_months > 1 else ''}"
                    )
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


@router.post("/pets")
async def create_or_update_pet_from_form(
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
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
    pet_service = PetService(db)
    file_service = FileService()

    # Processa imagem se fornecida
    photo_data = None
    if photo and photo.filename:
        is_valid, error_message = file_service.validate_image_file(photo)
        if not is_valid:
            # Redireciona com mensagem de erro user-friendly
            return RedirectResponse(
                url=f"/pets/form?error={error_message}&pet_id={pet_id or ''}",
                status_code=302,
            )

        # Se for atualização, remove imagem antiga (implementar se necessário)
        if pet_id:
            old_pet = await pet_service.get_pet_details(pet_id, user["id"])
            if old_pet and "photo" in old_pet:
                file_service.delete_pet_images(pet_id)

        # Salva nova imagem
        photo_data = file_service.save_image_with_thumbnail(photo, pet_id or "temp")

    pet_data = {
        "name": name,
        "breed": breed,
        "pedigree_number": pedigree_number,
        "birth_date": birth_date,
        "pet_type": pet_type,
        "gender": gender,
    }

    if photo_data:
        pet_data["photo"] = photo_data

    if pet_id:
        # Lógica de atualização
        success, message = await pet_service.update_pet(pet_id, pet_data, user["id"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message
            )

        # Move arquivo da pasta temporária para a pasta correta
        if photo_data:
            final_photo_data = file_service.move_temp_image_to_pet_folder(photo_data, pet_id)
            if final_photo_data:
                await pet_service.update_pet(pet_id, {"photo": final_photo_data}, user["id"])
    else:
        # Lógica de criação
        success, message, new_pet_id = await pet_service.create_pet(pet_data, user["id"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )

        # Move arquivos da pasta temporária para a pasta correta
        if photo_data and new_pet_id:
            final_photo_data = file_service.move_temp_image_to_pet_folder(photo_data, new_pet_id)
            if final_photo_data:
                await pet_service.update_pet(new_pet_id, {"photo": final_photo_data}, user["id"])

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/pets/{pet_id}/delete")
async def delete_pet_from_form(
    pet_id: str,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Realiza o soft delete de um pet.
    """
    pet_service = PetService(db)
    file_service = FileService()

    # Busca o pet para verificar se tem fotos
    pet = await pet_service.get_pet_details(pet_id, user["id"])

    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet não encontrado ou você não tem permissão para excluí-lo.",
        )

    # Remove as imagens do pet
    if pet.get("photo"):
        file_service.delete_pet_images(pet_id)

    success, message = await pet_service.delete_pet(pet_id, user["id"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/generate-pet-name")
async def generate_pet_name(
    gender: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Gera uma lista de nomes de pet ou comidas baseada no gênero.
    """
    pet_service = PetService(db)
    return pet_service.generate_pet_names(gender)


# Rotas para gerenciamento de acesso de veterinários
@router.get("/api/search-veterinarians")
async def search_veterinarians(
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
    search: str = Query(..., min_length=2),
):
    """
    Busca veterinários por nome para vinculação a pets.
    Apenas tutores podem buscar veterinários.
    """
    user_service = UserService(db)
    veterinarians = await user_service.search_veterinarians(search, user["id"])
    return JSONResponse(content={"veterinarians": veterinarians})


@router.post("/pets/{pet_id}/grant-access")
async def grant_veterinarian_access(
    pet_id: str,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
    veterinarian_id: str = Form(...),
):
    """
    Concede acesso de um veterinário a um pet específico.
    Apenas o tutor do pet pode conceder acesso.
    """
    pet_service = PetService(db)
    success, message = await pet_service.grant_veterinarian_access(pet_id, veterinarian_id, user["id"])

    return JSONResponse(content={"success": success, "message": message})


@router.post("/pets/{pet_id}/revoke-access")
async def revoke_veterinarian_access(
    pet_id: str,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
    veterinarian_id: str = Form(...),
):
    """
    Remove o acesso de um veterinário a um pet específico.
    Apenas o tutor do pet pode remover acesso.
    """
    pet_service = PetService(db)
    success, message = await pet_service.revoke_veterinarian_access(pet_id, veterinarian_id, user["id"])

    return JSONResponse(content={"success": success, "message": message})


@router.get("/pets/{pet_id}/veterinarians")
async def get_pet_veterinarians(
    pet_id: str,
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista os veterinários que têm acesso ao pet.
    Apenas o tutor do pet pode ver esta lista.
    """
    pet_service = PetService(db)
    success, veterinarians, message = await pet_service.get_pet_veterinarians(pet_id, user["id"])

    if not success:
        raise HTTPException(status_code=404, detail=message)

    return JSONResponse(content={"veterinarians": veterinarians})
