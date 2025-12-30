import re
from ..memory.schemas import GmailThread


_TOO_EARLY_PATTERNS = [
    r"\btoo early\b",
    r"\bearly for us\b",
    r"\bcheck back\b",
    r"\bkeep me posted\b",
    r"\brevisit\b",
]

def detect_too_early_intent(thread):
    text = "\n".join(m.body_text.lower() for m in thread.messages)
    return any(re.search(p, text) for p in _TOO_EARLY_PATTERNS)


def extract_founder_email(thread, investor_email):
    # Check messages in reverse to get the most recent non-investor sender
    for m in reversed(thread.messages):
        if m.from_email.lower() != investor_email.lower():
            return m.from_email
    return None
