from dataclasses import dataclass
from typing import Dict
from .constants import DEFAULT_THRESHOLD, DEFAULT_WEIGHTS, MAX_SIGNALS_IN_EMAIL, MIN_CONFIDENCE


@dataclass
class Config:
    default_threshold: float = DEFAULT_THRESHOLD
    default_weights: Dict[str, float] = None
    max_signals_in_email: int = MAX_SIGNALS_IN_EMAIL
    min_confidence: float = MIN_CONFIDENCE
    
    def __post_init__(self):
        if self.default_weights is None:
            self.default_weights = DEFAULT_WEIGHTS.copy()


