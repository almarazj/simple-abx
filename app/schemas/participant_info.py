from pydantic import BaseModel
from fastapi import Form


class ParticipantInfo(BaseModel):
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