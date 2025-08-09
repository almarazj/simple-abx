from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Test Application"
    APP_DESCRIPTION: str = "Aplicación para tests de audio ABX"
    VERSION: str = "0.1.0"

    # Firestore
    GOOGLE_PROJECT_ID: str = "simple-abx"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/abx_test.log"
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"

class DevelopmentConfig(Settings):
    """Configuración para desarrollo"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    FIRESTORE_COLLECTION: str = "test-results-dev"

class ProductionConfig(Settings):
    """Configuración para producción"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    FIRESTORE_COLLECTION: str = "test-results-3.0"

def get_settings(APP_ENV: str) -> Settings:

    if APP_ENV == "prod":
        return ProductionConfig()
    elif APP_ENV == "dev":
        return DevelopmentConfig()

# Instancia global de configuración
settings = get_settings(APP_ENV="dev")
