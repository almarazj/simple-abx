"""
Inicialización y configuración de la base de datos
"""
from app.database.session import engine, Base

async def init_database():
    """Inicializar la base de datos SQL (crear tablas)"""
    from app.database.session import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
