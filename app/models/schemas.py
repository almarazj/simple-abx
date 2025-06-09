# app/models/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.enums import AudioExperience, HeadphonesType, ListeningEnvironment, TestResponse, AgeRange
from fastapi import Form

# Schemas para requests
class ParticipantInfoCreate(BaseModel):
    age_range: AgeRange
    audio_experience: AudioExperience
    headphones_type: HeadphonesType
    listening_environment: ListeningEnvironment

    @classmethod
    def as_form(
        cls,
        age_range: str = Form(...),
        audio_experience: AudioExperience = Form(...),
        headphones_type: HeadphonesType = Form(...),
        listening_environment: ListeningEnvironment = Form(...)
    ):
        return cls(
            age_range=age_range,
            audio_experience=audio_experience,
            headphones_type=headphones_type,
            listening_environment=listening_environment
        )

class TestResponseSubmit(BaseModel):
    """Schema para envío de respuesta del test"""
    response: TestResponse = Field(..., description="Respuesta del usuario")
    
    class Config:
        use_enum_values = True

# Schemas para responses
class ParticipantInfo(BaseModel):
    """Schema para información del participante"""
    age_range: str
    audio_experience: str
    audio_experience_display: Optional[str] = None
    headphones_type: str
    headphones_type_display: Optional[str] = None
    listening_environment: str
    listening_environment_display: Optional[str] = None

class ComparisonData(BaseModel):
    """Schema para datos de una comparación"""
    stimulus_a: str = Field(..., description="Estímulo A")
    stimulus_b: str = Field(..., description="Estímulo B")
    stimulus_x: str = Field(..., description="Estímulo X (a comparar)")
    correct_answer: str = Field(..., description="Respuesta correcta")

class ResponseData(BaseModel):
    """Schema para datos de una respuesta"""
    comparison_id: int = Field(..., description="ID de la comparación")
    stimulus_a: str
    stimulus_b: str
    stimulus_x: str
    user_response: str
    correct_answer: str
    is_correct: bool
    timestamp: str

class TestStatistics(BaseModel):
    """Schema para estadísticas del test"""
    total_comparisons: int = Field(..., description="Total de comparaciones")
    correct_responses: int = Field(..., description="Respuestas correctas")
    incorrect_responses: int = Field(..., description="Respuestas incorrectas")
    ties: int = Field(..., description="Empates")
    accuracy_percentage: float = Field(..., description="Porcentaje de precisión")
    confidence_interval: Optional[Dict[str, float]] = Field(None, description="Intervalo de confianza")
    test_duration: Optional[str] = Field(None, description="Duración del test")

class SessionInfo(BaseModel):
    """Schema para información de sesión (debug)"""
    user_id: Optional[str]
    session_keys: List[str]
    current_comparison: Optional[int]
    total_comparisons: int
    responses_count: int
    participant_info: bool
    test_config: bool
    start_time: Optional[str]
    timestamp: str

# Schemas para responses de API
class StandardResponse(BaseModel):
    """Response estándar para operaciones"""
    status: str = Field(..., description="Estado de la operación")
    message: Optional[str] = Field(None, description="Mensaje descriptivo")

class TestStartResponse(StandardResponse):
    """Response para inicio de test"""
    redirect: Optional[str] = Field(None, description="URL de redirección")

class TestSubmitResponse(StandardResponse):
    """Response para envío de respuesta"""
    redirect: Optional[str] = Field(None, description="URL de redirección")
    next_comparison: Optional[ComparisonData] = Field(None, description="Siguiente comparación")
    current: Optional[int] = Field(None, description="Comparación actual")
    total: Optional[int] = Field(None, description="Total de comparaciones")
    action: Optional[str] = Field(None, description="Acción requerida")

class DebugSessionResponse(StandardResponse):
    """Response para debug de sesión"""
    session_info: Optional[SessionInfo] = Field(None, description="Información de sesión")

class TestResultSummary(BaseModel):
    """Schema para resumen de resultados"""
    result_id: Optional[str] = Field(None, description="ID del resultado guardado")
    user_id: str = Field(..., description="ID del usuario")
    participant_info: ParticipantInfo
    statistics: TestStatistics
    test_config: Dict[str, Any]
    start_time: str
    end_time: str
    responses: List[ResponseData]

# Schemas para base de datos
class TestResultDB(BaseModel):
    """Schema para resultado de test en base de datos"""
    user_id: str
    participant_info: Dict[str, Any]
    start_time: str
    end_time: str
    responses: List[Dict[str, Any]]
    test_config: Dict[str, Any]
    statistics: Dict[str, Any]
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Schemas para configuración
class TestConfig(BaseModel):
    """Schema para configuración del test"""
    num_comparisons: int = Field(default=21, ge=1, le=50, description="Número de comparaciones")
    audio_format: str = Field(default="wav", description="Formato de audio")
    test_type: str = Field(default="white_noise_vs_velvet_noise", description="Tipo de test")
    
    @validator('num_comparisons')
    def validate_num_comparisons(cls, v):
        if v < 1 or v > 50:
            raise ValueError('Número de comparaciones debe estar entre 1 y 50')
        return v
    
    @validator('audio_format')
    def validate_audio_format(cls, v):
        valid_formats = ['wav', 'mp3', 'flac']
        if v.lower() not in valid_formats:
            raise ValueError(f'Formato de audio debe ser uno de: {valid_formats}')
        return v.lower()
