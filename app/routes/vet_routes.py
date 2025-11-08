from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse
from ..services import PetService
from .auth_routes import get_current_user_from_session

# Configuração do Jinja2
templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/vet-dashboard", name="vet_dashboard")
def get_vet_dashboard_page(
    request: Request, user: dict = Depends(get_current_user_from_session)
):
    """
    Renderiza o dashboard específico para veterinários.
    """
    try:
        is_authenticated = "access_token" in request.session
        pet_service = PetService()
        pets_list = pet_service.get_user_pets(user["id"])

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
        raise


@router.get("/api/search-pet-by-nickname")
def search_pet_by_nickname(
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    nickname: str = Query(...),
):
    """
    Busca um pet pelo nickname para veterinários visualizarem informações básicas.
    """
    try:
        pet_service = PetService()
        success, pet_data, message = pet_service.search_pet_by_nickname(nickname, user["id"])

        if not success:
            return JSONResponse(
                content={"success": False, "message": message},
                status_code=404,
            )

        return JSONResponse(content={"success": True, "pet": pet_data})

    except Exception as e:
        print(f"Error searching pet by nickname: {e}")
        return JSONResponse(
            content={"success": False, "message": "Erro ao buscar pet."},
            status_code=500,
        )


@router.get("/api/search-pet-by-id")
def search_pet_by_id(
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    pet_id: str = Query(...),
):
    """
    Busca um pet pelo ID para veterinários visualizarem informações básicas.
    (Mantido para compatibilidade)
    """
    try:
        pet_service = PetService()
        pet = pet_service.get_pet_details(pet_id, user["id"])

        if not pet:
            return JSONResponse(
                content={"success": False, "message": "Pet não encontrado."},
                status_code=404,
            )

        # Verifica se o usuário tem acesso
        has_access = user["id"] in pet.get("users", [])

        if not has_access:
            # Remove informações detalhadas se não tem acesso
            limited_pet = {
                "_id": pet["_id"],
                "name": pet.get("name"),
                "nickname": pet.get("nickname"),
                "breed": pet.get("breed"),
                "pet_type": pet.get("pet_type"),
                "gender": pet.get("gender"),
                "birth_date": pet.get("birth_date"),
                "has_access": False,
                "message": "Você não tem acesso ao histórico completo deste pet.",
            }
            pet = limited_pet
        else:
            pet["has_access"] = True

        return JSONResponse(content={"success": True, "pet": pet})

    except Exception as e:
        print(f"Error searching pet by ID: {e}")
        return JSONResponse(
            content={"success": False, "message": "Erro ao buscar pet."},
            status_code=500,
        )
