from pydantic import BaseModel
from typing import List, Dict, Any

from app.schemas.test_results import TestResult

class ResponsesOverview(BaseModel):
    start_time: str
    age_range: int
    headphones_brand: str
    hearing_problems: bool
    audio_experience: str
    score: float
    total: int

class PairStats(BaseModel):
    stimulus: str
    pulse_density: str
    correct: float
    total: int

class Stats(BaseModel):
    total_tests: int
    total_responses: int
    correct_responses: float
    accuracy_percentage: float

class PairStimulus(BaseModel):
    label: str
    pulse_density: int
    accuracy: int
    pair_id: str
    correct: int
    total: int

class DashboardData(BaseModel):
    stats: Stats
    stimulus_pairs: Dict[str, List[PairStimulus]]
    responses: List[ResponsesOverview]
