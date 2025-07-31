from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic Settings"""
    APP_NAME: str = "Test Application"
    VERSION: str = "0.1.0"

    # Firestore
    GOOGLE_PROJECT_ID: str = "simple-abx"
    FIRESTORE_COLLECTION: str = "test-results-dev"

    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Archivos
    STATIC_FILES_DIR: str = "static"
    TEMPLATES_DIR: str = "templates"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/abx_test.log"
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"
    
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
    env = "development"
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()

# Instancia global de configuración
settings = get_settings()
