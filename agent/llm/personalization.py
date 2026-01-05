import logging
from dataclasses import dataclass
from typing import List, Dict
import re

logger = logging.getLogger(__name__)


@dataclass
class ToneProfile:
    """Profile of investor's email writing style."""
    avg_sentence_len: float
    uses_bullets_often: bool
    signoff: str


def build_tone_profile(sent_email_bodies: List[str]) -> ToneProfile:
    """
    Build tone profile from investor's sent emails.
    
    Analyzes writing style including:
    - Average sentence length
    - Bullet point usage frequency
    - Signoff pattern
    
    Args:
        sent_email_bodies: List of email body texts from investor
        
    Returns:
        ToneProfile with extracted style characteristics
    """
    if not sent_email_bodies:
        logger.warning("No email bodies provided for tone analysis")
        return ToneProfile(avg_sentence_len=0.0, uses_bullets_often=False, signoff="Best,\n{investor_name}")
    
    sentences = []
    bullets = 0
    signoffs = []

    for body in sent_email_bodies:
        if not body:
            continue
            
        parts = re.split(r"[.!?]\s+", body.strip())
        sentences += [p for p in parts if p]
        
        # Check if email uses bullet points
        if re.search(r"^\s*[-*]\s+", body, re.MULTILINE):
            bullets += 1
        
        # Extract signoff pattern
        m = re.search(r"\n\s*(Best|Thanks|Regards|Sincerely),?\s*\n\s*([^\n]+)\s*$", body, re.IGNORECASE)
        if m:
            signoffs.append(m.group(0).strip())

    if len(sentences) > 0:
        avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
    else:
        avg_len = 0.0
    
    uses_bullets = bullets >= max(1, len(sent_email_bodies)//3)
    signoff = signoffs[-1] if signoffs else "Best,\n{investor_name}"
    
    logger.info(f"Built tone profile: avg_len={avg_len:.1f}, bullets={uses_bullets}, signoff={signoff[:30]}...")
    
    return ToneProfile(avg_sentence_len=avg_len, uses_bullets_often=uses_bullets, signoff=signoff)


def draft_outreach_email(
    investor_name: str,
    investor_email: str,
    founder_name: str,
    founder_email: str,
    company: str,
    meeting_context: str,
    key_signals: List[Dict],
    tone: ToneProfile,
) -> Dict[str, str]:
    """
    Draft a personalized outreach email matching investor's tone.
    
    Creates an email that:
    - Matches investor's writing style (bullets vs inline)
    - Uses investor's signoff pattern
    - Includes relevant signals and context
    
    Args:
        investor_name: Name of the investor
        investor_email: Email of the investor
        founder_name: Name of the founder
        founder_email: Email of the founder
        company: Company name
        meeting_context: Context from previous meeting
        key_signals: List of key signal dictionaries
        tone: Investor's tone profile
        
    Returns:
        Dictionary with 'to', 'from', 'subject', and 'body' keys
    """
    from ..constants import MAX_SIGNALS_IN_EMAIL, MAX_SIGNALS_INLINE
    from ..utils import sanitize_email_content
    
    subject = f"Re: {company} - quick follow-up"
    lines = []
    lines.append(f"Hi {founder_name},")
    lines.append("")
    lines.append("Wanted to circle back after our last chat.")
    
    if meeting_context:
        sanitized_context = sanitize_email_content(meeting_context)
        lines.append(sanitized_context)
        lines.append("")
    
    if key_signals:
        if tone.uses_bullets_often:
            lines.append("A few updates caught my eye:")
            for s in key_signals[:MAX_SIGNALS_IN_EMAIL]:
                lines.append(f"- {s['title']}")
        else:
            titles = "; ".join(s["title"] for s in key_signals[:MAX_SIGNALS_INLINE])
            lines.append(f"A couple updates caught my eye: {titles}.")
        lines.append("")
    
    lines.append("If you're open to it, I'd like to reconnect and understand where things stand now.")
    lines.append("Are you free for 20 minutes next week?")
    lines.append("")
    
    signoff = tone.signoff.replace("{investor_name}", investor_name)
    lines.append(signoff)
    body = "\n".join(lines)
    
    body = sanitize_email_content(body)
    
    logger.info(f"Drafted email to {founder_email} with {len(key_signals)} signals")

    return {"to": founder_email, "from": investor_email, "subject": subject, "body": body}
