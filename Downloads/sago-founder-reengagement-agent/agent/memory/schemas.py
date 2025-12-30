from datetime import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel, Field


class GmailMessage(BaseModel):
    msg_id: str
    timestamp: datetime
    from_email: str
    to_emails: List[str]
    subject: str
    body_text: str


class GmailThread(BaseModel):
    thread_id: str
    messages: List[GmailMessage]


class InvestorProfile(BaseModel):
    investor_id: str
    name: str
    email: str
    firm: Optional[str] = None
    timezone: str = "America/Los_Angeles"
    auto_send: bool = False


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
    source: str
    occurred_at: datetime
    title: str
    detail: str
    url: Optional[str] = None
    confidence: float = 0.5
    magnitude: float = 0.5


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
