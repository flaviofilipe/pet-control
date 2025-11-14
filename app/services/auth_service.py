import os
import logging
import requests
from typing import Dict, Optional
from fastapi import HTTPException, Request

# Auth0 configuration
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET", "")

logger = logging.getLogger(__name__)


class AuthService:
    """Serviço para gerenciar autenticação Auth0"""
    
    @staticmethod
    def refresh_auth_token(refresh_token: str) -> dict:
        """Renova o token de acesso usando o refresh token."""
        logger.info("Attempting to refresh access token...")
        
        payload = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": refresh_token,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.post(
                f"https://{AUTH0_DOMAIN}/oauth/token",
                headers=headers,
                data=payload,
                timeout=30,
            )
            response.raise_for_status()
            tokens = response.json()
            logger.info("✅ Token refreshed successfully")
            return tokens
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            error_body = e.response.text if e.response else "no response"
            logger.error(f"❌ Token refresh failed: status={status_code}, error={error_body}")
            raise
        except Exception as e:
            logger.error(f"❌ Token refresh error: {str(e)}")
            raise
    
    @staticmethod
    def get_current_user_info_from_session(request: Request) -> Dict | Exception:
        """
        Dependência para obter informações do usuário a partir da sessão.
        Renova o token automaticamente se necessário.
        USA CACHE NA SESSÃO para evitar rate limit do Auth0 (429 Too Many Requests).
        """
        access_token = request.session.get("access_token")
        refresh_token = request.session.get("refresh_token")
        cached_user_info = request.session.get("user_info")

        # Verifica se há um flag de refresh em andamento para evitar loops
        if request.session.get("refreshing_token"):
            logger.warning("Token refresh already in progress, clearing session to avoid loop")
            request.session.clear()
            raise HTTPException(
                status_code=401, detail="Authentication loop detected. Please log in again."
            )

        if not access_token:
            raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")

        # Se temos user_info em cache, usar sem chamar Auth0
        if cached_user_info:
            user_id = cached_user_info.get("sub")
            if user_id:
                return {"id": user_id, "info": cached_user_info}

        # Cache miss ou inválido - buscar do Auth0
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = requests.get(
                f"https://{AUTH0_DOMAIN}/userinfo",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            user_info = response.json()
            user_id = user_info.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found in token.")

            # Armazena no cache da sessão
            request.session["user_info"] = user_info

            result = {"id": user_id, "info": user_info}
            return result
        except requests.exceptions.Timeout:
            logger.warning("Auth0 UserInfo request timed out")
            raise HTTPException(
                status_code=408, detail="Request timeout. Please try again."
            )
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else "unknown"
            logger.error(f"Auth0 UserInfo HTTP error: status={status_code}, error={str(http_err)}")
            
            # Se for 429 (Too Many Requests), usar cache ou retornar erro específico
            if http_err.response.status_code == 429:
                logger.error("⚠️ Auth0 Rate Limit exceeded (429). Using cached user info if available.")
                if cached_user_info:
                    user_id = cached_user_info.get("sub")
                    if user_id:
                        logger.info("✅ Using cached user info due to rate limit")
                        return {"id": user_id, "info": cached_user_info}
                # Se não tem cache, retornar erro específico SEM limpar sessão
                raise HTTPException(
                    status_code=429, 
                    detail="Auth0 rate limit exceeded. Please wait a moment and try again."
                )
            
            if http_err.response.status_code == 401 and refresh_token:
                logger.info("Access token expired, attempting to refresh")
                try:
                    # Marca que está fazendo refresh para evitar loops
                    request.session["refreshing_token"] = True

                    new_tokens = AuthService.refresh_auth_token(refresh_token)
                    new_access_token = new_tokens.get("access_token")
                    new_refresh_token = new_tokens.get("refresh_token", refresh_token)

                    request.session["access_token"] = new_access_token
                    request.session["refresh_token"] = new_refresh_token
                    request.session.pop("refreshing_token", None)

                    logger.info("Token refreshed successfully")

                    headers["Authorization"] = f"Bearer {new_access_token}"
                    response = requests.get(
                        f"https://{AUTH0_DOMAIN}/userinfo",
                        headers=headers,
                        timeout=30,
                    )
                    response.raise_for_status()
                    user_info = response.json()
                    user_id = user_info.get("sub")

                    result = {"id": user_id, "info": user_info}
                    return result
                except requests.exceptions.Timeout:
                    logger.warning("Token refresh request timed out")
                    request.session.pop("refreshing_token", None)
                    raise HTTPException(
                        status_code=408, detail="Token refresh timeout. Please try again."
                    )
                except requests.exceptions.RequestException as refresh_err:
                    logger.error("Token refresh failed, forcing re-login")
                    request.session.clear()
                    raise HTTPException(
                        status_code=401,
                        detail="Could not refresh credentials. Please log in again.",
                    )
            else:
                logger.error("Auth0 UserInfo request failed with HTTP error")
                request.session.clear()
                raise HTTPException(
                    status_code=401, detail="Could not validate credentials"
                )
        except requests.exceptions.RequestException as e:
            logger.error(f"Auth0 UserInfo request failed: {e}")

            # Para erros de rede, não limpa a sessão imediatamente
            if "timeout" in str(e).lower():
                raise HTTPException(
                    status_code=408, detail="Network timeout. Please try again."
                )
            else:
                request.session.clear()
                raise HTTPException(
                    status_code=401, detail="Could not validate credentials"
                )
    
    @staticmethod
    def get_current_user_info_from_header(authorization: str) -> Dict:
        """
        Dependência original para obter informações do usuário a partir do cabeçalho.
        Usado para proteger os endpoints da API.
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
            logger.error("Auth0 UserInfo request failed")
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    @staticmethod
    def exchange_code_for_token(code: str, callback_uri: str) -> Dict:
        """Troca o código de autorização por tokens"""
        payload = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": callback_uri,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.post(
                f"https://{AUTH0_DOMAIN}/oauth/token",
                headers=headers,
                data=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Auth0 Token exchange failed")
            raise HTTPException(
                status_code=400, detail="Failed to exchange code for token."
            )
