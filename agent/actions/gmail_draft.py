from pathlib import Path
from ..memory.schemas import DraftEmail


def write_eml_draft(draft, outpath):
    content = []
    content.append(f"From: {draft.from_email}")
    content.append(f"To: {draft.to_email}")
    content.append(f"Subject: {draft.subject}")
    content.append("")
    content.append(draft.body)
    outpath.write_text("\n".join(content), encoding="utf-8")
