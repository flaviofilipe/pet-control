import os
import time
import logging
import requests
from typing import Dict, Optional
from fastapi import HTTPException, Request

# Cache simples para evitar requisições desnecessárias ao Auth0
user_cache = {}
CACHE_DURATION = 300  # 5 minutos

# Auth0 configuration
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET", "")


class AuthService:
    """Serviço para gerenciar autenticação Auth0"""
    
    @staticmethod
    def clear_user_cache(user_id: str = None):
        """Limpa o cache de usuários. Se user_id for fornecido, limpa apenas esse usuário."""
        if user_id:
            # Remove entradas que contenham o user_id
            keys_to_remove = [
                key for key in user_cache.keys() if user_id in str(user_cache[key][0])
            ]
            for key in keys_to_remove:
                del user_cache[key]
        else:
            # Limpa todo o cache
            user_cache.clear()
    
    @staticmethod
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
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def get_current_user_info_from_session(request: Request) -> Dict | Exception:
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
            raise HTTPException(
                status_code=401, detail="Authentication loop detected. Please log in again."
            )

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
                timeout=30,
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
            raise HTTPException(
                status_code=408, detail="Request timeout. Please try again."
            )
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 401 and refresh_token:
                print("Access token expired, attempting to refresh...")
                try:
                    # Marca que está fazendo refresh para evitar loops
                    request.session["refreshing_token"] = True

                    new_tokens = AuthService.refresh_auth_token(refresh_token)
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
                        timeout=30,
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
                    raise HTTPException(
                        status_code=408, detail="Token refresh timeout. Please try again."
                    )
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
                raise HTTPException(
                    status_code=401, detail="Could not validate credentials"
                )
        except requests.exceptions.RequestException as e:
            print(f"Auth0 UserInfo request failed: {e}")
            logging.error(f"Auth0 UserInfo request failed: {e}")

            # Para erros de rede, não limpa a sessão imediatamente
            if "timeout" in str(e).lower():
                raise HTTPException(
                    status_code=408, detail="Network timeout. Please try again."
                )
            else:
                # Para outros erros de rede, limpa a sessão
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
            print(f"Auth0 UserInfo request failed: {e}")
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
            print(f"Auth0 Token exchange failed: {e}")
            raise HTTPException(
                status_code=400, detail="Failed to exchange code for token."
            )
