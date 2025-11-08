from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from ..services import UserService
from .auth_routes import get_current_user_from_session

# Configuração do Jinja2
templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/profile")
def get_user_profile(
    request: Request, user: dict = Depends(get_current_user_from_session)
):
    """
    Exibe o perfil do usuário logado em uma página HTML.
    """
    user_service = UserService()
    profile_data = user_service.get_user_profile(user["id"], user["info"])

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user_info": profile_data,
        },
    )


@router.get("/profile/edit")
def edit_user_profile_page(
    request: Request, user: dict = Depends(get_current_user_from_session)
):
    """
    Renderiza a página com o formulário para editar o perfil do usuário.
    """
    user_service = UserService()
    profile_data = user_service.get_user_profile(user["id"], user["info"])

    return templates.TemplateResponse(
        "profile_update.html",
        {
            "request": request,
            "user_info": profile_data,
        },
    )


@router.post("/profile")
def create_or_update_user_profile(
    user: dict = Depends(get_current_user_from_session),
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
    """
    user_service = UserService()
    
    profile_data = {
        "_id": user["id"],
        "name": name,
        "bio": bio,
        "address": {
            "street": street,
            "city": city,
            "state": state,
            "zip": zip,
        },
        "is_vet": is_vet,
    }

    success, message = user_service.create_or_update_profile(
        user["id"], profile_data, user["info"].get("email")
    )

    if not success:
        print(f"Error updating profile: {message}")

    # Redireciona o usuário de volta para a página de perfil
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)
