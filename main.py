# main.py - Punto de entrada principal
from app.core.config import settings
from app.database.init_db import init_database
from app.core.app_factory import create_app

app = create_app()

@app.on_event("startup")
async def on_startup():
    await init_database()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )