# Founder Re-engagement Agent (Sago take-home)

Prototype agent that detects "too early" founder threads in Gmail, sets a monitoring job, watches for meaningful signals, and drafts a personalized outreach email when it is time to re-engage.

Scope: rough prototype. Gmail and Drive actions are stubbed behind interfaces so the core flow runs locally.

## Design principles

### Seamless integration (Gmail + Google Drive)
- Input: a Gmail thread where the investor says "too early" and optionally a Drive link or attached deck.
- Output: a draft reply in the same Gmail thread (stubbed locally as a `.eml` draft file).
- No new UI. The only surfaces are Gmail and Drive.

### Hyper-personalization
- Builds an investor tone profile from prior sent emails (sampled in `samples/inputs/investor_sent_emails.json`).
- Stores deal context (founder, company, prior meeting notes).
- Generates outreach that matches the investor's typical structure, verbosity, and sign-off.

### True agency
- Creates a monitoring job with a cadence and signal sources.
- Collects signals (mock collectors implemented, real ones sketched).
- Scores and decides whether to notify.
- Drafts outreach automatically and can be configured for auto-send.

## Quickstart

Requirements:
- Python 3.10+

Install:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the end-to-end demo (local, mocked):
```bash
python -m agent.demo_run \
  --thread samples/inputs/gmail_thread_too_early.json \
  --investor samples/inputs/investor_profile.json \
  --sent samples/inputs/investor_sent_emails.json \
  --signals samples/inputs/mock_signals_stream.json \
  --outdir samples/outputs/run1
```

Outputs:
- `decision.json` (signal scoring and threshold decision)
- `notification_email.txt` (what would be sent to investor)
- `draft_reply.eml` (what would be inserted as a Gmail draft reply)

## Repo layout

- `agent/listeners/` Gmail intake and intent detection (stub + interfaces)
- `agent/signals/` signal collectors (mock implementation + skeleton for real APIs)
- `agent/scoring/` feature extraction and scoring engine
- `agent/memory/` simple memory store and schemas
- `agent/llm/` prompt templates and a pluggable LLM client interface
- `agent/actions/` Gmail draft/send executor (stub implementation)
- `docs/architecture.pdf` 1-2 page system architecture

## Notes on production hardening (not implemented)
- Gmail push notifications (watch) via Pub/Sub.
- Drive attachment ingestion and embedding store for retrieval.
- Source-specific confidence calibration and de-duplication.
- Human-in-the-loop policy for auto-send and compliance logging.
