import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from dateutil import parser as dtp

from .memory.schemas import GmailThread, SignalEvent, InvestorProfile, Decision, DraftEmail
from .listeners.gmail_intake import detect_too_early_intent, extract_founder_email
from .signals.collectors import MockSignalCollector, deduplicate_signals
from .scoring.engine import score_event, aggregate_scores
from .llm.personalization import build_tone_profile, draft_outreach_email
from .actions.gmail_draft import write_eml_draft
from .utils import load_json, validate_path
from .constants import DEFAULT_THRESHOLD, DEFAULT_WEIGHTS
from .config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_inputs(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Load and validate all input files.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Dictionary with loaded data: thread, investor, sent_bodies, events
        
    Raises:
        FileNotFoundError: If any input file is missing
        ValueError: If any input file is invalid
    """
    logger.info("Loading input files...")
    
    try:
        thread_data = load_json(validate_path(args.thread))
        investor_data = load_json(validate_path(args.investor))
        sent_data = load_json(validate_path(args.sent))
        signals_data = load_json(validate_path(args.signals))
        
        thread = GmailThread.model_validate(thread_data)
        investor = InvestorProfile.model_validate(investor_data)
        sent_bodies = sent_data.get("sent_email_bodies", [])
        
        if not sent_bodies:
            logger.warning("No sent email bodies found, using default tone")
        
        raw_events = signals_data.get("events", [])
        if not raw_events:
            logger.warning("No signal events found in input")
        
        events = []
        for e in raw_events:
            try:
                e["occurred_at"] = dtp.parse(e["occurred_at"])
                events.append(SignalEvent.model_validate(e))
            except Exception as ex:
                logger.error(f"Failed to parse event: {e.get('title', 'unknown')} - {ex}")
                continue
        
        logger.info(f"Loaded {len(events)} signal events")
        
        return {
            "thread": thread,
            "investor": investor,
            "sent_bodies": sent_bodies,
            "events": events,
            "thread_data": thread_data,
        }
        
    except Exception as e:
        logger.error(f"Error loading inputs: {e}")
        raise


def process_signals(
    events: List[SignalEvent],
    company: str,
    investor_weights: Dict[str, float],
    config: Config
) -> List:
    """
    Process and score signals for a company.
    
    Args:
        events: List of signal events
        company: Company name
        investor_weights: Investor's signal source weights
        config: Configuration object
        
    Returns:
        List of scored signal events
    """
    logger.info(f"Processing signals for {company}...")
    
    if not events:
        logger.warning("No events to process")
        return []
    
    collector = MockSignalCollector(events)
    collected = collector.collect(company)
    
    if not collected:
        logger.warning(f"No signals collected for {company}")
        return []
    
    # Deduplicate signals
    collected = deduplicate_signals(collected)
    
    # Filter by minimum confidence
    filtered = [e for e in collected if e.confidence >= config.min_confidence]
    if len(filtered) < len(collected):
        logger.info(f"Filtered {len(collected) - len(filtered)} low-confidence signals")
    
    # Score events
    scored = []
    for ev in filtered:
        try:
            scored.append(score_event(ev, investor_weights))
        except Exception as e:
            logger.error(f"Error scoring event '{ev.title}': {e}")
            continue
    
    logger.info(f"Scored {len(scored)} signals")
    return scored


def make_decision(
    scored: List,
    threshold: float,
    thread_id: str,
    deal_id: str = "deal_demo_001"
) -> Decision:
    """
    Make re-engagement decision based on aggregated scores.
    
    Args:
        scored: List of scored signal events
        threshold: Decision threshold
        thread_id: Gmail thread ID
        deal_id: Deal identifier
        
    Returns:
        Decision object with recommendation and rationale
    """
    if not scored:
        logger.warning("No scored events for decision making")
        total = 0.0
    else:
        total = aggregate_scores(scored)
    
    recommended = total >= threshold
    
    if recommended:
        rationale = "Signals indicate meaningful momentum. Re-engagement recommended."
        logger.info(f"Decision: RE-ENGAGE (score: {total:.3f} >= threshold: {threshold:.3f})")
    else:
        rationale = "Signals are not strong enough yet. Continue monitoring."
        logger.info(f"Decision: WAIT (score: {total:.3f} < threshold: {threshold:.3f})")
    
    return Decision(
        deal_id=deal_id,
        thread_id=thread_id,
        recommended=recommended,
        total_score=total,
        threshold=threshold,
        scored_events=scored,
        rationale=rationale,
    )


def generate_outputs(
    decision: Decision,
    draft: DraftEmail,
    company: str,
    scored: List,
    outdir: Path
) -> None:
    """
    Generate all output files.
    
    Args:
        decision: Decision object
        draft: Draft email (if recommended)
        company: Company name
        scored: List of scored events
        outdir: Output directory path
    """
    logger.info(f"Generating outputs to {outdir}...")
    
    try:
        outdir.mkdir(parents=True, exist_ok=True)
        
        # Write decision JSON
        decision_path = outdir / "decision.json"
        decision_path.write_text(decision.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"Wrote decision to {decision_path}")
        
        # Write notification email
        notification = []
        notification.append(f"Deal: {company}")
        notification.append(f"Thread: {decision.thread_id}")
        notification.append(f"Decision: {'RE-ENGAGE' if decision.recommended else 'WAIT'}")
        notification.append(f"Score: {decision.total_score:.2f} (threshold {decision.threshold:.2f})")
        notification.append("")
        notification.append("Top signals:")
        for s in sorted(scored, key=lambda x: x.score, reverse=True)[:5]:
            notification.append(f"- [{s.event.source}] {s.event.title} (score {s.score:.2f})")
        
        notification_path = outdir / "notification_email.txt"
        notification_path.write_text("\n".join(notification), encoding="utf-8")
        logger.info(f"Wrote notification to {notification_path}")
        
        # Write draft email if recommended
        if decision.recommended and draft:
            draft_path = outdir / "draft_reply.eml"
            write_eml_draft(draft, draft_path)
            logger.info(f"Wrote draft email to {draft_path}")
        
    except Exception as e:
        logger.error(f"Error generating outputs: {e}")
        raise


def main() -> None:
    """Main entry point for the demo script."""
    parser = argparse.ArgumentParser(
        description="Founder Re-engagement Agent Demo"
    )
    parser.add_argument("--thread", required=True, type=Path,
                       help="Path to Gmail thread JSON file")
    parser.add_argument("--investor", required=True, type=Path,
                       help="Path to investor profile JSON file")
    parser.add_argument("--sent", required=True, type=Path,
                       help="Path to sent emails JSON file")
    parser.add_argument("--signals", required=True, type=Path,
                       help="Path to signals JSON file")
    parser.add_argument("--outdir", required=True, type=Path,
                       help="Output directory for results")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        config = Config()
        
        # Load inputs
        inputs = load_inputs(args)
        thread = inputs["thread"]
        investor = inputs["investor"]
        sent_bodies = inputs["sent_bodies"]
        events = inputs["events"]
        thread_data = inputs["thread_data"]
        
        # Detect intent
        if not detect_too_early_intent(thread):
            logger.error("No 'too early' intent detected")
            sys.exit("No 'too early' intent detected. Try a different thread sample.")
        
        # Extract founder info
        founder_email = extract_founder_email(thread, investor.email) or "founder@example.com"
        founder_name = thread_data.get("founder_name", "Founder")
        company = thread_data.get("company", "Company")
        
        logger.info(f"Processing deal for {company} (founder: {founder_name})")
        
        # Get investor weights
        investor_weights = investor.signal_weights or config.default_weights
        threshold = investor.signal_threshold or config.default_threshold
        
        # Process signals
        scored = process_signals(events, company, investor_weights, config)
        
        if not scored:
            logger.warning("No signals to score, cannot make decision")
            sys.exit("No valid signals found. Cannot make decision.")
        
        # Make decision
        decision = make_decision(scored, threshold, thread.thread_id)
        
        # Generate draft if recommended
        draft = None
        if decision.recommended:
            logger.info("Generating personalized email draft...")
            tone = build_tone_profile(sent_bodies)
            sorted_scored = sorted(scored, key=lambda x: x.score, reverse=True)
            key_signals = []
            for s in sorted_scored:
                key_signals.append({
                    "title": s.event.title,
                    "detail": s.event.detail,
                    "url": s.event.url,
                    "source": s.event.source,
                })
            
            draft_dict = draft_outreach_email(
                investor_name=investor.name,
                investor_email=investor.email,
                founder_name=founder_name,
                founder_email=founder_email,
                company=company,
                meeting_context=thread_data.get("meeting_context", ""),
                key_signals=key_signals,
                tone=tone,
            )
            draft = DraftEmail(
                to_email=draft_dict["to"],
                from_email=draft_dict["from"],
                subject=draft_dict["subject"],
                body=draft_dict["body"],
            )
        
        # Generate outputs
        generate_outputs(decision, draft, company, scored, args.outdir)
        
        logger.info(f"Successfully completed processing. Outputs written to {args.outdir}")
        print(f"Wrote outputs to {args.outdir}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
