import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def load_json(path: Path) -> Dict[str, Any]:
    """
    Load and parse a JSON file with error handling.
    
    Args:
        path: Path to the JSON file
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        raise


def validate_path(path: Path, must_exist: bool = True) -> Path:
    """
    Validate and sanitize file paths.
    
    Args:
        path: Path to validate
        must_exist: Whether the path must exist
        
    Returns:
        Resolved and validated path
        
    Raises:
        FileNotFoundError: If path must exist but doesn't
        ValueError: If path contains directory traversal
    """
    resolved = path.resolve()
    
    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {resolved}")
    
    if ".." in str(resolved):
        raise ValueError("Invalid path: directory traversal detected")
    
    return resolved


def sanitize_email_content(text: str, max_length: int = 10000) -> str:
    """
    Sanitize email content to prevent injection and limit length.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Email content truncated to {max_length} characters")
    
    return text


