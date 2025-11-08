from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse
from .config import SESSION_SECRET_KEY
from .services import FileService
from .routes import (
    auth_router,
    dashboard_router,
    user_router,
    pet_router,
    treatment_router,
    info_router,
    vet_router,
)

# FastAPI application setup
def create_app() -> FastAPI:
    app = FastAPI(
        title="Profile Management API",
        description="API for user profile management with Auth0 and MongoDB.",
        version="1.0.0",
    )

    # Configuração de middlewares
    setup_middlewares(app)
    
    # Configuração de arquivos estáticos e templates
    setup_static_files(app)
    
    # Configuração de rotas
    setup_routes(app)
    
    # Configuração de handlers de exceção
    setup_exception_handlers(app)
    
    # Limpeza de arquivos temporários na inicialização
    FileService.cleanup_temp_images()
    
    return app


def setup_middlewares(app: FastAPI):
    """Configura middlewares da aplicação"""
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Session middleware para gerenciar estado do usuário logado
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET_KEY,
    )


def setup_static_files(app: FastAPI):
    """Configura arquivos estáticos e templates"""
    # Servindo arquivos estáticos
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


def setup_routes(app: FastAPI):
    """Configura todas as rotas da aplicação"""
    
    # Health check endpoint para Docker e monitoramento
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Endpoint de health check para monitoramento e Docker"""
        try:
            from .database import database
            from datetime import datetime
            
            # Testa conexão com banco de dados
            database.client.admin.command("ismaster")
            
            return {
                "status": "healthy",
                "service": "pet-control-api",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "database": "connected"
            }
        except Exception as e:
            raise HTTPException(
                status_code=503, 
                detail={
                    "status": "unhealthy",
                    "service": "pet-control-api",
                    "timestamp": datetime.now().isoformat(),
                    "error": "Database connection failed",
                    "details": str(e)
                }
            )
    
    app.include_router(auth_router, tags=["Authentication"])
    app.include_router(dashboard_router, tags=["Dashboard"])
    app.include_router(user_router, tags=["User"])
    app.include_router(pet_router, tags=["Pets"])
    app.include_router(treatment_router, tags=["Treatments"])
    app.include_router(info_router, tags=["Information"])
    app.include_router(vet_router, tags=["Veterinarian"])


def setup_exception_handlers(app: FastAPI):
    """Configura handlers de exceção"""
    # Templates para páginas de erro
    templates = Jinja2Templates(directory="templates")
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Tratamento global de exceções HTTP.
        Redireciona usuários não autenticados para a tela de login.
        """
        if exc.status_code == 401:
            # Para rotas que renderizam templates, redireciona para login
            return RedirectResponse(url="/login", status_code=302)
        elif exc.status_code == 408:
            # Para timeouts, retorna uma página de erro amigável
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error_code": 408,
                    "error_title": "Timeout",
                    "error_message": "A requisição demorou muito para responder. Tente novamente.",
                    "show_retry": True,
                },
                status_code=408,
            )

        # Para outras exceções HTTP, retorna a resposta padrão
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
