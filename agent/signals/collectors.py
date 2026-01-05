import logging
from typing import List
from datetime import datetime, timedelta
from ..memory.schemas import SignalEvent
from ..constants import SIGNAL_AGE_DAYS

logger = logging.getLogger(__name__)


class SignalCollector:
    """Abstract base class for signal collectors."""
    
    def collect(self, company: str) -> List[SignalEvent]:
        """
        Collect signal events for a given company.
        
        Args:
            company: Company name to collect signals for
            
        Returns:
            List of signal events
        """
        raise NotImplementedError


class MockSignalCollector(SignalCollector):
    """Mock signal collector for testing and prototyping."""
    
    def __init__(self, events: List[SignalEvent]):
        """
        Initialize with pre-loaded events.
        
        Args:
            events: List of signal events to return
        """
        self._events = events
        logger.info(f"Initialized MockSignalCollector with {len(events)} events")

    def collect(self, company: str) -> List[SignalEvent]:
        """
        Return pre-loaded events (filtered by company in production).
        
        Args:
            company: Company name (not used in mock implementation)
            
        Returns:
            List of signal events
        """
        filtered = self._filter_recent(self._events)
        logger.info(f"Collected {len(filtered)} signals for {company}")
        return filtered
    
    def _filter_recent(self, events: List[SignalEvent]) -> List[SignalEvent]:
        """Filter signals to only include recent ones."""
        cutoff = datetime.now() - timedelta(days=SIGNAL_AGE_DAYS)
        recent = [e for e in events if e.occurred_at >= cutoff]
        if len(recent) < len(events):
            logger.debug(f"Filtered out {len(events) - len(recent)} old signals")
        return recent


def deduplicate_signals(events: List[SignalEvent]) -> List[SignalEvent]:
    """
    Remove duplicate or very similar signals.
    
    Deduplicates based on source, title (case-insensitive), and date.
    
    Args:
        events: List of signal events
        
    Returns:
        List of unique signal events
    """
    seen = set()
    unique = []
    
    for event in events:
        key = (event.source, event.title.lower(), event.occurred_at.date())
        if key not in seen:
            seen.add(key)
            unique.append(event)
    
    if len(unique) < len(events):
        logger.info(f"Deduplicated {len(events)} signals to {len(unique)} unique signals")
    
    return unique
