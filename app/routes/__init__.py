from .auth_routes import router as auth_router
from .dashboard_routes import router as dashboard_router  
from .user_routes import router as user_router
from .pet_routes import router as pet_router
from .treatment_routes import router as treatment_router
from .info_routes import router as info_router
from .vet_routes import router as vet_router

__all__ = [
    "auth_router",
    "dashboard_router",
    "user_router", 
    "pet_router",
    "treatment_router",
    "info_router",
    "vet_router",
]
