# app/models/enums.py
from enum import Enum


class AgeRange(str, Enum):
    """Rango de edad del participante"""
    UNDER_18 = "under_18"
    BETWEEN_18_AND_24 = "between_18_and_24"
    BETWEEN_25_AND_34 = "between_25_and_34"
    BETWEEN_35_AND_44 = "between_35_and_44"
    BETWEEN_45_AND_54 = "between_45_and_54"
    BETWEEN_55_AND_64 = "between_55_and_64"
    OVER_65 = "over_65"
    
    @property
    def display_name(self):
        display_names = {
            "under_18": "Menor de 18",
            "between_18_and_24": "18-24 años",
            "between_25_and_34": "25-34 años",
            "between_35_and_44": "35-44 años",
            "between_45_and_54": "45-54 años",
            "between_55_and_64": "55-64 años",
            "over_65": "Mayor de 65"
        }
        return display_names.get(self.value, self.value)


class AudioExperience(str, Enum):
    """Experiencia en audio del participante"""
    NONE = "none"
    CASUAL = "casual"
    HOBBYIST = "hobbyist"
    PROFESSIONAL = "professional"
    
    @property
    def display_name(self):
        display_names = {
            "none": "Sin experiencia",
            "casual": "Casual",
            "hobbyist": "Aficionado",
            "professional": "Profesional"
        }
        return display_names.get(self.value, self.value)

class HeadphonesType(str, Enum):
    """Tipo de auriculares"""
    IN_EAR = "in_ear"
    ON_EAR = "on_ear"
    SPEAKERS = "speakers"
    OTHER = "other"
    
    @property
    def display_name(self):
        display_names = {
            "in_ear": "Auriculares in-ear",
            "on_ear": "Auriculares de vincha",
            "speakers": "Altavoces (PC/Laptop/Celular)",
            "other": "Otro"
        }
        return display_names.get(self.value, self.value)

class ListeningEnvironment(str, Enum):
    """Ambiente de escucha"""
    QUIET_ROOM = "quiet_room"
    NORMAL_ROOM = "normal_room"
    NOISY_ENVIRONMENT = "noisy_environment"
    OTHER = "other"
    
    @property
    def display_name(self):
        display_names = {
            "quiet_room": "Habitación silenciosa",
            "normal_room": "Habitación normal",
            "noisy_environment": "Ambiente ruidoso",
            "other": "Otro"
        }
        return display_names.get(self.value, self.value)

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
