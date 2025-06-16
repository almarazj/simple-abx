# app/models/enums.py
from enum import Enum

class TestResponse(str, Enum):
    """Respuestas posibles del test ABX"""
    A = "A"
    B = "B"
    TIE = "tie"
    
    @property
    def display_name(self):
        display_names = {
            "A": "A",
            "B": "B",
            "tie": "Empate/No puedo distinguir"
        }
        return display_names.get(self.value, self.value)

class TestStatus(str, Enum):
    """Estados del test"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    
    @property
    def display_name(self):
        display_names = {
            "not_started": "No iniciado",
            "in_progress": "En progreso",
            "completed": "Completado",
            "abandoned": "Abandonado"
        }
        return display_names.get(self.value, self.value)

class LogLevel(str, Enum):
    """Niveles de logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Environment(str, Enum):
    """Ambientes de la aplicación"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
