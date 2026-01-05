import re
import logging
from typing import Optional
from ..memory.schemas import GmailThread

logger = logging.getLogger(__name__)

_TOO_EARLY_PATTERNS = [
    r"\btoo early\b",
    r"\bearly for us\b",
    r"\bcheck back\b",
    r"\bkeep me posted\b",
    r"\brevisit\b",
]


def detect_too_early_intent(thread: GmailThread) -> bool:
    """
    Detect if a Gmail thread contains "too early" intent from investor.
    
    Uses regex pattern matching to find common phrases indicating the investor
    wants to revisit the deal later.
    
    Args:
        thread: Gmail thread to analyze
        
    Returns:
        True if "too early" intent detected, False otherwise
    """
    if not thread.messages:
        logger.warning("Empty thread provided for intent detection")
        return False
    
    text = "\n".join(m.body_text.lower() for m in thread.messages)
    detected = any(re.search(p, text) for p in _TOO_EARLY_PATTERNS)
    
    if detected:
        logger.info(f"Detected 'too early' intent in thread {thread.thread_id}")
    
    return detected


def extract_founder_email(thread: GmailThread, investor_email: str) -> Optional[str]:
    """
    Extract founder email from thread by finding non-investor sender.
    
    Checks messages in reverse order to get the most recent non-investor sender,
    assuming the founder is the other participant in the conversation.
    
    Args:
        thread: Gmail thread to analyze
        investor_email: Email address of the investor
        
    Returns:
        Founder email if found, None otherwise
    """
    if not thread.messages:
        logger.warning("Empty thread provided for email extraction")
        return None
    
    investor_email_lower = investor_email.lower()
    for m in reversed(thread.messages):
        if m.from_email.lower() != investor_email_lower:
            logger.info(f"Extracted founder email: {m.from_email}")
            return m.from_email
    
    logger.warning(f"Could not extract founder email from thread {thread.thread_id}")
    return None
