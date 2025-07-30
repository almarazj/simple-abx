# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from fastapi import Form
from datetime import datetime


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


class ResponseItem(BaseModel):
    stimulus: Optional[str]
    pulse_density: Optional[int]
    response: Optional[str]
    correct: Optional[bool]


class TestResultSchema(BaseModel):
    user_id: str
    participant_info: ParticipantInfo
    start_time: Optional[datetime]
    responses: List[ResponseItem]
    test_config: Dict[str, Any]


class PairStatsSchema(BaseModel):
    stimulus: str
    pulse_density: int
    correct: float
    total: int


class StatsSchema(BaseModel):
    total_tests: int
    total_responses: int
    correct_responses: float
    accuracy_percentage: float


class PairStimulusSchema(BaseModel):
    label: str
    pulse_density: int
    accuracy: float
    pair_id: str


class DashboardContextSchema(BaseModel):
    request: Any  # FastAPI Request object, not validated by Pydantic
    stats: StatsSchema
    pair_stats: Dict[str, PairStatsSchema]
    accuracy_data: Dict[str, List[float]]
    response_data: Dict[str, List[int]]
    stimulus_pairs: Dict[str, List[PairStimulusSchema]]
    results: List[TestResultSchema]
    config: Any  # Your settings/config object


class SubmitResponseResult(BaseModel):
    status: str
    current: int
    total: int
    next_comparison: Optional[Any] = None
    redirect: Optional[str] = None