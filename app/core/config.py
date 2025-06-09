# app/core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic Settings"""
    FASTAPI_ENV: str = os.getenv("FASTAPI_ENV")
    APP_NAME: str = os.getenv("APP_NAME")
    VERSION: str = os.getenv("VERSION")    
    
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT")
    
    DATABASE_URL: str = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    HOST: str = os.getenv("HOST")
    PORT: int = os.getenv("PORT")
    
    # Archivos
    STATIC_FILES_DIR: str = "static"
    TEMPLATES_DIR: str = "templates"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/abx_test.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True


class DevelopmentConfig(Settings):
    """Configuración para desarrollo"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionConfig(Settings):
    """Configuración para producción"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"


class TestingConfig(Settings):
    """Configuración para testing"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


def get_settings() -> Settings:
    """Obtener configuración basada en el entorno"""
    env = os.getenv('FASTAPI_ENV')
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()

# Instancia global de configuración
settings = get_settings()
