# main.py - Punto de entrada principal
from app.core.config import settings
from app.core.app_factory import create_app

app = create_app()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )