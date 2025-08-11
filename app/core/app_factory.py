from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, get_app_logger
from app.core.exceptions import setup_exception_handlers
from app.core.db_session import collection
from app.core.gcloud_storage import storage_router
from app.web.web import web_router
from app.api import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
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
    
    app.mount("/static", StaticFiles(directory="static"), name="static")
    # Serve the React app (if built) under /app with index.html fallback
    try:
        app.mount("/app", StaticFiles(directory="static/spa", html=True), name="spa")
    except Exception:
        # Ignore if SPA is not built yet
        pass
    # CORS for local React dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
    app.include_router(web_router)
    app.include_router(storage_router)
    app.include_router(api_router)
    
    return app