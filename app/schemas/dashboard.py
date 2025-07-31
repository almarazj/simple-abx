from pydantic import BaseModel
from typing import List, Dict, Any

from app.schemas.test_results import TestResult

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
    accuracy: float
    pair_id: str

class DashboardData(BaseModel):
    stats: Stats
    pair_stats: Dict[str, PairStats]
    accuracy_data: Dict[str, List[float]]
    response_data: Dict[str, List[int]]
    stimulus_pairs: Dict[str, List[PairStimulus]]
    results: List[TestResult]
