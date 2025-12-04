"""
Rotas de tratamentos
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Form, status
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import PetService
from app.database.connection import get_db
from .auth_routes import get_current_user_from_session

# Configuração do Jinja2
templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/pets/{pet_id}/treatments/add")
async def add_treatment_page(
    pet_id: str,
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Renderiza página para adicionar tratamento ao pet"""
    pet_service = PetService(db)
    pet = await pet_service.get_pet_details(pet_id, user["id"])
    
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found.")

    return templates.TemplateResponse(
        "treatment_form.html",
        {"request": request, "pet": pet, "treatment": None, "user_info": user["info"]},
    )


@router.post("/pets/{pet_id}/treatments")
async def create_or_update_treatment(
    pet_id: str,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
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
    """Cria ou atualiza um tratamento para o pet"""
    pet_service = PetService(db)

    treatment_data = {
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
        success, message = await pet_service.update_treatment(pet_id, treatment_id, user["id"], treatment_data)
        if not success:
            raise HTTPException(status_code=404, detail=message)
    else:
        # Lógica de criação
        success, message = await pet_service.add_treatment(pet_id, user["id"], treatment_data)
        if not success:
            raise HTTPException(status_code=404, detail=message)

    return RedirectResponse(
        url="/pets/" + pet_id + "/profile", status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/pets/{pet_id}/treatments/{treatment_id}/edit")
async def edit_treatment_page(
    pet_id: str,
    treatment_id: str,
    request: Request,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Renderiza página para editar tratamento"""
    pet_service = PetService(db)
    pet = await pet_service.get_pet_details(pet_id, user["id"])
    
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found.")

    treatment = next(
        (t for t in pet.get("treatments", []) if str(t["_id"]) == treatment_id), None
    )
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found.")

    treatment["_id"] = str(treatment["_id"])

    return templates.TemplateResponse(
        "treatment_form.html",
        {
            "request": request,
            "pet": pet,
            "treatment": treatment,
            "user_info": user["info"],
        },
    )


@router.post("/pets/{pet_id}/treatments/{treatment_id}/delete")
async def delete_treatment(
    pet_id: str,
    treatment_id: str,
    user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Remove tratamento do pet"""
    pet_service = PetService(db)
    success, message = await pet_service.delete_treatment(pet_id, treatment_id, user["id"])

    if not success:
        raise HTTPException(status_code=404, detail=message)

    return RedirectResponse(
        url="/pets/" + pet_id + "/profile", status_code=status.HTTP_303_SEE_OTHER
    )
