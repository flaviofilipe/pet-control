from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from ..services import PetService
from ..repositories import UserRepository
from .auth_routes import get_current_user_from_session
from ..models import UserProfile

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
        
        # Busca pets do usuário
        pet_service = PetService()
        pets_list = pet_service.get_user_pets(user["id"])
        
        # Busca perfil do usuário no banco de dados pelo email
        user_repository = UserRepository()
        user_email = user["info"].get("email")
        user_nickname = user["info"].get("nickname")
        user_profile = None
        
        if user_email:
            user_profile = user_repository.get_profile_by_email(user_email)
            
            if not user_profile:
                # Tenta buscar por ID como fallback
                user_profile = user_repository.get_profile_by_id(user["id"])
        
        # Se o usuário não tem perfil configurado, redireciona para completar o cadastro
        if not user_profile:
            # Adiciona mensagem na sessão para informar o usuário
            request.session["profile_message"] = "complete_profile"
            request.session["profile_message_text"] = "Por favor, complete seu perfil para continuar."
            return RedirectResponse(url="/profile/edit", status_code=303)
        
        # Combina informações do Auth0 com o perfil do banco
        user_info = {
            "id": user["id"],
            "email": user_email,
            "nickname": user_nickname,
            "photo": user["info"].get("picture"),  # Auth0 usa 'picture', mas template usa 'photo'
            "profile": user_profile  # Perfil completo do banco de dados
        }
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "is_authenticated": is_authenticated,
                "current_year": 2024,
                "user_info": user_info,
                "pets": pets_list,
            },
        )
    except HTTPException as e:
        print(f"Error fetching dashboard data: {e}")
        raise
