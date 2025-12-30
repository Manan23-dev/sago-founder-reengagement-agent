from ..memory.schemas import SignalEvent, SignalScore


def score_event(event, investor_weights):
    w = float(investor_weights.get(event.source, 1.0))
    score = max(0.0, min(1.0, event.confidence * event.magnitude * w))
    reasons = [
        f"source={event.source} weight={w:.2f}",
        f"confidence={event.confidence:.2f}",
        f"magnitude={event.magnitude:.2f}",
    ]
    if score > 0.7:
        reasons.append("high combined signal")
    return SignalScore(event=event, score=score, reasons=reasons)


def aggregate_scores(scored):
    # Diminishing returns: multiple signals don't add linearly
    prod = 1.0
    for s in scored:
        score_val = max(0.0, min(1.0, s.score))
        prod *= (1.0 - score_val)
    return 1.0 - prod
