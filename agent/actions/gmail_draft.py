import logging
from pathlib import Path
from ..memory.schemas import DraftEmail
from ..utils import validate_path

logger = logging.getLogger(__name__)


def write_eml_draft(draft: DraftEmail, outpath: Path) -> None:
    """
    Write email draft to EML file format.
    
    Creates a minimal RFC822-like email file that can be imported into Gmail.
    
    Args:
        draft: DraftEmail object with email content
        outpath: Path where to write the EML file
        
    Raises:
        ValueError: If path validation fails
        IOError: If file write fails
    """
    try:
        validated_path = validate_path(outpath, must_exist=False)
        validated_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = []
        content.append(f"From: {draft.from_email}")
        content.append(f"To: {draft.to_email}")
        content.append(f"Subject: {draft.subject}")
        content.append("")
        content.append(draft.body)
        
        validated_path.write_text("\n".join(content), encoding="utf-8")
        logger.info(f"Wrote email draft to {validated_path}")
        
    except Exception as e:
        logger.error(f"Failed to write email draft to {outpath}: {e}")
        raise
