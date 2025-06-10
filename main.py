# main.py - Punto de entrada principal
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.database.init_db import init_database
from app.core.app_factory import create_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    yield

app = create_app(lifespan=lifespan)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )