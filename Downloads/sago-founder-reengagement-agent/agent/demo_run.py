import argparse
import json
from pathlib import Path
from dateutil import parser as dtp

from .memory.schemas import GmailThread, SignalEvent, InvestorProfile, Decision, DraftEmail
from .listeners.gmail_intake import detect_too_early_intent, extract_founder_email
from .signals.collectors import MockSignalCollector
from .scoring.engine import score_event, aggregate_scores
from .llm.personalization import build_tone_profile, draft_outreach_email
from .actions.gmail_draft import write_eml_draft


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--thread", required=True, type=Path)
    parser.add_argument("--investor", required=True, type=Path)
    parser.add_argument("--sent", required=True, type=Path)
    parser.add_argument("--signals", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    thread = GmailThread.model_validate(load_json(args.thread))
    investor = InvestorProfile.model_validate(load_json(args.investor))
    sent_bodies = load_json(args.sent)["sent_email_bodies"]

    if not detect_too_early_intent(thread):
        raise SystemExit("No 'too early' intent detected. Try a different thread sample.")

    founder_email = extract_founder_email(thread, investor.email) or "founder@example.com"
    founder_name = load_json(args.thread).get("founder_name", "Founder")
    company = load_json(args.thread).get("company", "Company")

    raw_events = load_json(args.signals)["events"]
    events = []
    for e in raw_events:
        e["occurred_at"] = dtp.parse(e["occurred_at"])
        events.append(SignalEvent.model_validate(e))

    collector = MockSignalCollector(events)
    collected = collector.collect(company)

    investor_weights = load_json(args.investor).get("signal_weights", {
        "funding": 1.2,
        "hiring": 1.0,
        "product_launch": 1.1,
        "press": 0.9,
    })

    scored = []
    for ev in collected:
        scored.append(score_event(ev, investor_weights))
    total = aggregate_scores(scored)

    threshold = float(load_json(args.investor).get("signal_threshold", 0.75))
    recommended = total >= threshold

    if recommended:
        rationale = "Signals indicate meaningful momentum. Re-engagement recommended."
    else:
        rationale = "Signals are not strong enough yet. Continue monitoring."

    decision = Decision(
        deal_id="deal_demo_001",
        thread_id=thread.thread_id,
        recommended=recommended,
        total_score=total,
        threshold=threshold,
        scored_events=scored,
        rationale=rationale,
    )

    (args.outdir/"decision.json").write_text(decision.model_dump_json(indent=2), encoding="utf-8")

    notification = []
    notification.append(f"Deal: {company}")
    notification.append(f"Thread: {thread.thread_id}")
    notification.append(f"Decision: {'RE-ENGAGE' if recommended else 'WAIT'}")
    notification.append(f"Score: {total:.2f} (threshold {threshold:.2f})")
    notification.append("")
    notification.append("Top signals:")
    for s in sorted(scored, key=lambda x: x.score, reverse=True)[:5]:
        notification.append(f"- [{s.event.source}] {s.event.title} (score {s.score:.2f})")
    (args.outdir/"notification_email.txt").write_text("\n".join(notification), encoding="utf-8")

    if recommended:
        tone = build_tone_profile(sent_bodies)
        sorted_scored = sorted(scored, key=lambda x: x.score, reverse=True)
        key_signals = []
        for s in sorted_scored:
            key_signals.append({"title": s.event.title, "detail": s.event.detail, "url": s.event.url})
        draft_dict = draft_outreach_email(
            investor_name=investor.name,
            investor_email=investor.email,
            founder_name=founder_name,
            founder_email=founder_email,
            company=company,
            meeting_context=load_json(args.thread).get("meeting_context", ""),
            key_signals=key_signals,
            tone=tone,
        )
        draft = DraftEmail(
            to_email=draft_dict["to"],
            from_email=draft_dict["from"],
            subject=draft_dict["subject"],
            body=draft_dict["body"],
        )
        write_eml_draft(draft, args.outdir/"draft_reply.eml")

    print(f"Wrote outputs to {args.outdir}")

if __name__ == "__main__":
    main()
