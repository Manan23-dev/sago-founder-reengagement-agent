import logging
from typing import List, Dict
from ..memory.schemas import SignalEvent, SignalScore
from ..constants import HIGH_SCORE_THRESHOLD

logger = logging.getLogger(__name__)


def score_event(event: SignalEvent, investor_weights: Dict[str, float]) -> SignalScore:
    """
    Score a signal event based on confidence, magnitude, and investor preferences.
    
    Formula: score = confidence × magnitude × source_weight (clamped to [0, 1])
    
    Args:
        event: The signal event to score
        investor_weights: Dictionary mapping signal sources to weight multipliers
        
    Returns:
        SignalScore with calculated score and reasoning
    """
    w = float(investor_weights.get(event.source, 1.0))
    score = max(0.0, min(1.0, event.confidence * event.magnitude * w))
    
    reasons = [
        f"source={event.source} weight={w:.2f}",
        f"confidence={event.confidence:.2f}",
        f"magnitude={event.magnitude:.2f}",
    ]
    
    if score > HIGH_SCORE_THRESHOLD:
        reasons.append("high combined signal")
    
    logger.debug(f"Scored event '{event.title}': {score:.3f}")
    
    return SignalScore(event=event, score=score, reasons=reasons)


def aggregate_scores(scored: List[SignalScore]) -> float:
    """
    Aggregate multiple signal scores using diminishing returns formula.
    
    Uses formula: total = 1 - ∏(1 - score_i)
    This prevents over-weighting when multiple weak signals exist.
    Example: 3 signals at 0.5 each = 0.875 (not 1.5)
    
    Args:
        scored: List of scored signal events
        
    Returns:
        Aggregated score between 0.0 and 1.0
    """
    if not scored:
        logger.warning("No scores to aggregate")
        return 0.0
    
    prod = 1.0
    for s in scored:
        score_val = max(0.0, min(1.0, s.score))
        prod *= (1.0 - score_val)
    
    total = 1.0 - prod
    logger.info(f"Aggregated {len(scored)} signals to total score: {total:.3f}")
    
    return total
