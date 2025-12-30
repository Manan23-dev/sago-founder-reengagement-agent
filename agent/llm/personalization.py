from dataclasses import dataclass
import re


@dataclass
class ToneProfile:
    avg_sentence_len: float
    uses_bullets_often: bool
    signoff: str


def build_tone_profile(sent_email_bodies):
    sentences = []
    bullets = 0
    signoffs = []

    for body in sent_email_bodies:
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
    return ToneProfile(avg_sentence_len=avg_len, uses_bullets_often=uses_bullets, signoff=signoff)


def draft_outreach_email(
    investor_name,
    investor_email,
    founder_name,
    founder_email,
    company,
    meeting_context,
    key_signals,
    tone,
):
    subject = f"Re: {company} - quick follow-up"
    lines = []
    lines.append(f"Hi {founder_name},")
    lines.append("")
    lines.append("Wanted to circle back after our last chat.")
    if meeting_context:
        lines.append(meeting_context.strip())
    lines.append("")
    if key_signals:
        if tone.uses_bullets_often:
            lines.append("A few updates caught my eye:")
            for s in key_signals[:4]:
                lines.append(f"- {s['title']}")
        else:
            titles = "; ".join(s["title"] for s in key_signals[:3])
            lines.append(f"A couple updates caught my eye: {titles}.")
        lines.append("")
    lines.append("If you're open to it, I'd like to reconnect and understand where things stand now.")
    lines.append("Are you free for 20 minutes next week?")
    lines.append("")
    signoff = tone.signoff.replace("{investor_name}", investor_name)
    lines.append(signoff)
    body = "\n".join(lines)

    return {"to": founder_email, "from": investor_email, "subject": subject, "body": body}
