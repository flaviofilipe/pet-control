from typing import Optional
import logging
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse
from ..repositories import InfoRepository
from .auth_routes import get_current_user_from_session

logger = logging.getLogger(__name__)

# Configuração do Jinja2
templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/vacinas")
def get_vaccines_page(
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    search: Optional[str] = None,
    especie: Optional[str] = None,
    tipo: Optional[str] = None,
):
    """
    Renderiza a página de vacinas com informações detalhadas sobre cada tipo.
    """
    try:
        info_repo = InfoRepository()
        
        # Busca vacinas com filtros
        vacinas = info_repo.search_vaccines(search, especie, tipo)
        
        # Busca opções para filtros
        especies = info_repo.get_vaccine_species()
        tipos = info_repo.get_vaccine_types()

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
                "total_vacinas": len(vacinas),
            },
        )

    except Exception as e:
        logger.error(f"Error fetching vaccines data: {e}")
        raise HTTPException(
            status_code=500, detail="Erro ao carregar dados das vacinas"
        )


@router.get("/ectoparasitas")
def get_ectoparasites_page(
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    search: Optional[str] = None,
    especie: Optional[str] = None,
    tipo: Optional[str] = None,
):
    """
    Renderiza a página de ectoparasitas com informações detalhadas sobre cada tipo.
    """
    try:
        info_repo = InfoRepository()
        
        # Busca ectoparasitas com filtros
        ectoparasitas = info_repo.search_ectoparasites(search, especie, tipo)
        
        # Busca opções para filtros
        especies = info_repo.get_ectoparasite_species()
        tipos = info_repo.get_ectoparasite_types()

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
                "total_ectoparasitas": len(ectoparasitas),
            },
        )

    except Exception as e:
        logger.error(f"Error fetching ectoparasites data: {e}")
        raise HTTPException(
            status_code=500, detail="Erro ao carregar dados dos ectoparasitas"
        )


@router.get("/vermifugos")
def get_vermifugos_page(
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    search: Optional[str] = None,
    especie: Optional[str] = None,
    tipo: Optional[str] = None,
):
    """
    Renderiza a página de vermífugos com informações detalhadas sobre cada tipo.
    """
    try:
        info_repo = InfoRepository()
        
        # Busca vermífugos com filtros
        vermifugos_list = info_repo.search_vermifugos(search, especie, tipo)
        
        # Busca opções para filtros
        especies = info_repo.get_vermifugo_species()
        tipos = info_repo.get_vermifugo_types()

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
                "total_vermifugos": len(vermifugos_list),
            },
        )

    except Exception as e:
        logger.error(f"Error fetching vermifugos data: {e}")
        raise HTTPException(
            status_code=500, detail="Erro ao carregar dados dos vermífugos"
        )


@router.get("/api/vacinas/autocomplete")
def get_vaccines_autocomplete(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    user: dict = Depends(get_current_user_from_session),
):
    """
    Endpoint para autocomplete de vacinas.
    Retorna sugestões baseadas no nome da vacina.
    """
    try:
        if len(q) < 1:
            return {"suggestions": []}

        info_repo = InfoRepository()
        suggestions = info_repo.get_vaccines_autocomplete(q)

        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"Error in vaccines autocomplete: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar sugestões")


@router.get("/api/ectoparasitas/autocomplete")
def get_ectoparasites_autocomplete(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    user: dict = Depends(get_current_user_from_session),
):
    """
    Endpoint para autocomplete de ectoparasitas.
    Retorna sugestões baseadas no nome da praga.
    """
    try:
        if len(q) < 1:
            return {"suggestions": []}

        info_repo = InfoRepository()
        suggestions = info_repo.get_ectoparasites_autocomplete(q)

        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"Error in ectoparasites autocomplete: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar sugestões")


@router.get("/api/vermifugos/autocomplete")
def get_vermifugos_autocomplete(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    user: dict = Depends(get_current_user_from_session),
):
    """
    Endpoint para autocomplete de vermífugos.
    Retorna sugestões baseadas no nome da praga e outros campos.
    """
    try:
        if len(q) < 1:
            return {"suggestions": []}

        info_repo = InfoRepository()
        suggestions = info_repo.get_vermifugos_autocomplete(q)

        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"Error in vermifugos autocomplete: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar sugestões")
