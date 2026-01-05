from datetime import datetime
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field, field_validator


class GmailMessage(BaseModel):
    """Represents a single Gmail message."""
    msg_id: str
    timestamp: datetime
    from_email: str
    to_emails: List[str]
    subject: str
    body_text: str


class GmailThread(BaseModel):
    """Represents a Gmail conversation thread."""
    thread_id: str
    messages: List[GmailMessage]


class InvestorProfile(BaseModel):
    """Investor configuration and preferences."""
    investor_id: str
    name: str
    email: str
    firm: Optional[str] = None
    timezone: str = "America/Los_Angeles"
    auto_send: bool = False
    signal_threshold: float = 0.75
    signal_weights: Dict[str, float] = Field(default_factory=dict)
    
    @field_validator('signal_threshold')
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate threshold is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('signal_threshold must be between 0.0 and 1.0')
        return v
    
    @field_validator('signal_weights')
    @classmethod
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate all weights are between 0.0 and 2.0."""
        if v and not all(0.0 <= w <= 2.0 for w in v.values()):
            raise ValueError('signal_weights must be between 0.0 and 2.0')
        return v


class FounderProfile(BaseModel):
    name: str
    email: Optional[str] = None
    company: str
    last_meeting_date: Optional[str] = None
    notes: Optional[str] = None


class DealState(BaseModel):
    deal_id: str
    thread_id: str
    investor_id: str
    founder: FounderProfile
    stage: Literal["too_early", "monitoring", "reengage_recommended", "closed"] = "too_early"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked_at: Optional[datetime] = None
    signal_threshold: float = 0.75
    sources: List[str] = Field(default_factory=lambda: ["funding", "hiring", "product_launch", "press"])


class SignalEvent(BaseModel):
    """Represents an external signal about a company."""
    source: str
    occurred_at: datetime
    title: str
    detail: str
    url: Optional[str] = None
    confidence: float = 0.5
    magnitude: float = 0.5
    
    @field_validator('confidence', 'magnitude')
    @classmethod
    def validate_score_range(cls, v: float) -> float:
        """Validate confidence and magnitude are between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('confidence and magnitude must be between 0.0 and 1.0')
        return v


class SignalScore(BaseModel):
    event: SignalEvent
    score: float
    reasons: List[str]


class Decision(BaseModel):
    deal_id: str
    thread_id: str
    recommended: bool
    total_score: float
    threshold: float
    scored_events: List[SignalScore]
    rationale: str


class DraftEmail(BaseModel):
    to_email: str
    from_email: str
    subject: str
    body: str
