from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.templating import Jinja2Templates
from ..services import PetService
from .auth_routes import get_current_user_from_session

# Configuração do Jinja2
templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/")
def get_landing_page(request: Request):
    """Página inicial do site"""
    is_authenticated = "access_token" in request.session
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_authenticated": is_authenticated,
            "current_year": 2024,
        },
    )


@router.get("/dashboard", name="dashboard")
def get_dashboard_page(
    request: Request, user: dict = Depends(get_current_user_from_session)
):
    """
    Renderiza a página do dashboard para usuários autenticados,
    passando os dados do usuário e a lista de pets para o template.
    """
    try:
        is_authenticated = "access_token" in request.session
        pet_service = PetService()
        pets_list = pet_service.get_user_pets(user["id"])

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
        raise
