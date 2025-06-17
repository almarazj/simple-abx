# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from fastapi import Form

# Schemas para requests
class ParticipantInfoCreate(BaseModel):
    age_range: int
    headphones_brand: str
    hearing_problems: str
    audio_experience: str

    @classmethod
    def as_form(
        cls,
        age_range: int = Form(...),
        headphones_brand: str = Form(...),
        hearing_problems: str = Form(...),
        audio_experience: str = Form(...)
    ):
        return cls(
            age_range=age_range,
            headphones_brand=headphones_brand,
            hearing_problems=hearing_problems,
            audio_experience=audio_experience
        )

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
