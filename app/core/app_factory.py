from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, get_app_logger
from app.core.exceptions import setup_exception_handlers
from app.core.db_session import collection
from app.web.web import web_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Aplicación para tests de audio ABX",
        version=settings.VERSION,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    
    setup_logging()    
    logger = get_app_logger()
    logger.info("Initializing application...")
    logger.info(f"Firestore collection: {collection.id}")

    setup_exception_handlers(app)
    
    app.mount("/static", StaticFiles(directory=settings.STATIC_FILES_DIR), name="static")
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
    app.include_router(web_router)
    
    return app