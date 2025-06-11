# app/core/app_factory.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import setup_exception_handlers
from app.web.web import web_router

def create_app() -> FastAPI:
    """Factory para crear la aplicación FastAPI"""
    
    # Crear aplicación
    app = FastAPI(
        title=settings.APP_NAME,
        description="Aplicación para tests de audio ABX",
        version=settings.VERSION,
        debug=settings.DEBUG,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # Configurar logging
    setup_logging()
    
    # Configurar archivos estáticos
    app.mount("/static", StaticFiles(directory=settings.STATIC_FILES_DIR), name="static")
    
    # Registrar routers
    app.include_router(web_router)
    
    # Configurar manejadores de errores
    setup_exception_handlers(app)
    
    return app