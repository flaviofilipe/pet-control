import os
from fastapi import APIRouter, HTTPException, Request, Depends
from starlette.responses import RedirectResponse
from ..services import AuthService

# Auth0 configuration
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
AUTH0_API_AUDIENCE = os.environ.get("AUTH0_API_AUDIENCE", "")
CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
AUTH0_CALLBACK_URI = os.environ.get("AUTH0_CALLBACK_URI", "http://localhost:8000/callback")

router = APIRouter()


@router.get("/login")
def login():
    """
    Redireciona o usuário para o Auth0 para autenticação.
    Sempre força o usuário a digitar as credenciais.
    """
    return RedirectResponse(
        url=f"https://{AUTH0_DOMAIN}/authorize?audience={AUTH0_API_AUDIENCE}&response_type=code&client_id={CLIENT_ID}&scope=offline_access openid profile email&redirect_uri={AUTH0_CALLBACK_URI}&prompt=login"
    )


@router.get("/callback")
def callback(request: Request, code: str):
    """
    Manipula o redirecionamento do Auth0 após a autenticação.
    Armazena o token de acesso e o refresh token na sessão.
    """
    try:
        token_info = AuthService.exchange_code_for_token(code, AUTH0_CALLBACK_URI)

        # Armazena ambos os tokens na sessão
        request.session["access_token"] = token_info.get("access_token")
        request.session["refresh_token"] = token_info.get("refresh_token")

        # Redireciona o usuário para o dashboard
        return RedirectResponse(url="/dashboard")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in callback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")


@router.get("/logout")
def logout(request: Request):
    """
    Limpa a sessão e faz logout completo do Auth0.
    """
    # Limpa a sessão do usuário
    request.session.clear()

    # URL de logout do Auth0 que força o usuário a digitar credenciais novamente
    auth0_logout_url = f"https://{AUTH0_DOMAIN}/v2/logout?client_id={CLIENT_ID}&returnTo={request.base_url}"

    return RedirectResponse(url=auth0_logout_url)


# Dependências para as rotas
def get_current_user_from_session(request: Request):
    """Dependência para obter usuário da sessão"""
    return AuthService.get_current_user_info_from_session(request)


def get_current_user_from_header(authorization: str = Depends()):
    """Dependência para obter usuário do header"""
    return AuthService.get_current_user_info_from_header(authorization)
