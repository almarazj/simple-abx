from pydantic import BaseModel
from typing import List, Optional

class AudioPair(BaseModel):
    id: str
    stimulus_type: str
    pulse_density: str
    reference: str
    variation: str

class Variation(BaseModel):
    id: str
    pulse_density: str
    file: str
    description: Optional[str] = None

class Stimulus(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    reference_file: str
    variations: List[Variation]

class TestMetadata(BaseModel):
    test_type: str
    description: Optional[str] = None
    stimuli: List[Stimulus]