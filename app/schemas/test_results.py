from pydantic import BaseModel
from typing import List, Any, Optional
from datetime import datetime

from app.schemas.participant_info import ParticipantInfo

class ResponseItem(BaseModel):
    stimulus: Optional[str]
    pulse_density: Optional[str]
    response: Optional[str]
    correct: Optional[bool]

class PairInfo(BaseModel):
    a_type: str
    b_type: str
    pair_id: str
    pulse_density: str
    reference_file: str
    stimulus_type: str
    variation_file: str
    x_type: str

class Comparison(BaseModel):
    correct_answer: str
    id: int
    pair_info: PairInfo
    stimulus_a: str
    stimulus_b: str
    stimulus_x: str

class TestConfig(BaseModel):
    comparisons: List[Comparison]

class TestResult(BaseModel):
    user_id: str
    participant_info: ParticipantInfo
    start_time: Optional[datetime]
    responses: List[ResponseItem]
    test_config: TestConfig

    class Config:
        arbitrary_types_allowed = True

class SubmitResponseResult(BaseModel):
    status: str
    current: int
    total: int
    next_comparison: Optional[Any] = None
    redirect: Optional[str] = None