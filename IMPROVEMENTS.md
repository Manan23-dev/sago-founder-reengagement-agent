# Code Improvements & Enhancement Plan

## Priority 1: Critical Improvements (Do First)

### 1. Error Handling & Validation
**Current Issues:**
- No try-catch blocks for file operations
- No validation for JSON parsing
- No handling for missing fields
- No validation for file paths

**Improvements:**
```python
# Add to demo_run.py
def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

# Add validation for empty signals
if not collected:
    raise ValueError("No signals collected for company")
```

### 2. Input Validation
**Current Issues:**
- No validation for investor weights
- No validation for threshold range
- No validation for email formats

**Improvements:**
```python
# Add to schemas.py
from pydantic import EmailStr, Field, field_validator

class InvestorProfile(BaseModel):
    # ... existing fields ...
    
    @field_validator('signal_threshold')
    @classmethod
    def validate_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('threshold must be between 0.0 and 1.0')
        return v
    
    @field_validator('signal_weights')
    @classmethod
    def validate_weights(cls, v):
        if not all(0.0 <= w <= 2.0 for w in v.values()):
            raise ValueError('weights must be between 0.0 and 2.0')
        return v
```

### 3. Logging
**Current Issues:**
- No logging for debugging
- No error tracking
- No audit trail

**Improvements:**
```python
# Add logging.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use in demo_run.py
logger.info(f"Processing thread: {thread.thread_id}")
logger.warning(f"Low signal score: {total:.2f}")
logger.error(f"Failed to extract founder email")
```

---

## Priority 2: Code Quality Improvements

### 4. Type Hints
**Current Issues:**
- Missing type hints in many functions
- Makes code harder to understand and maintain

**Improvements:**
```python
# Add type hints throughout
from typing import List, Dict, Optional

def score_event(event: SignalEvent, investor_weights: Dict[str, float]) -> SignalScore:
    ...

def aggregate_scores(scored: List[SignalScore]) -> float:
    ...
```

### 5. Docstrings
**Current Issues:**
- No function documentation
- Hard to understand purpose and parameters

**Improvements:**
```python
def score_event(event: SignalEvent, investor_weights: Dict[str, float]) -> SignalScore:
    """
    Score a signal event based on confidence, magnitude, and investor preferences.
    
    Args:
        event: The signal event to score
        investor_weights: Dictionary mapping signal sources to weight multipliers
        
    Returns:
        SignalScore with calculated score and reasoning
        
    Formula: score = confidence × magnitude × source_weight (clamped to [0, 1])
    """
    ...
```

### 6. Configuration Management
**Current Issues:**
- Hardcoded default values
- No configuration file
- Difficult to adjust without code changes

**Improvements:**
```python
# Add config.py
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    default_threshold: float = 0.75
    default_weights: Dict[str, float] = None
    max_signals_in_email: int = 4
    min_confidence: float = 0.3
    
    def __post_init__(self):
        if self.default_weights is None:
            self.default_weights = {
                "funding": 1.2,
                "hiring": 1.0,
                "product_launch": 1.1,
                "press": 0.9,
            }
```

### 7. Constants Extraction
**Current Issues:**
- Magic numbers and strings scattered
- Hard to maintain

**Improvements:**
```python
# Add constants.py
DEFAULT_THRESHOLD = 0.75
DEFAULT_WEIGHTS = {
    "funding": 1.2,
    "hiring": 1.0,
    "product_launch": 1.1,
    "press": 0.9,
}
MAX_SIGNALS_IN_EMAIL = 4
HIGH_SCORE_THRESHOLD = 0.7
```

---

## Priority 3: Feature Enhancements

### 8. Signal Deduplication
**Current Issues:**
- No deduplication of similar signals
- Could over-weight duplicate information

**Improvements:**
```python
# Add to collectors.py
def deduplicate_signals(events: List[SignalEvent]) -> List[SignalEvent]:
    """Remove duplicate or very similar signals."""
    seen = set()
    unique = []
    for event in events:
        key = (event.source, event.title.lower(), event.occurred_at.date())
        if key not in seen:
            seen.add(key)
            unique.append(event)
    return unique
```

### 9. Time-Based Signal Filtering
**Current Issues:**
- No filtering by recency
- Old signals treated same as new

**Improvements:**
```python
# Add time decay
from datetime import datetime, timedelta

def filter_recent_signals(events: List[SignalEvent], days: int = 90) -> List[SignalEvent]:
    """Filter signals to only include those within specified days."""
    cutoff = datetime.now() - timedelta(days=days)
    return [e for e in events if e.occurred_at >= cutoff]

# Add time decay to scoring
def apply_time_decay(score: float, event: SignalEvent, days_old: int) -> float:
    """Apply exponential decay based on signal age."""
    decay_factor = 0.95 ** days_old  # 5% decay per day
    return score * decay_factor
```

### 10. Better Email Personalization
**Current Issues:**
- Limited personalization
- No variation in email templates
- Doesn't adapt to signal types

**Improvements:**
```python
# Add multiple email templates
EMAIL_TEMPLATES = {
    "funding_focused": "I saw {company} raised {details}. Would love to reconnect...",
    "hiring_focused": "Noticed {company} is scaling the team with {details}...",
    "product_focused": "Excited to see {company} launched {details}...",
}

def select_template(key_signals: List[Dict]) -> str:
    """Select template based on dominant signal type."""
    source_counts = {}
    for s in key_signals:
        source = s.get('source', 'general')
        source_counts[source] = source_counts.get(source, 0) + 1
    dominant = max(source_counts, key=source_counts.get)
    return EMAIL_TEMPLATES.get(f"{dominant}_focused", EMAIL_TEMPLATES["general"])
```

### 11. Signal Source Reliability Scoring
**Current Issues:**
- All sources treated equally
- No learning from past accuracy

**Improvements:**
```python
# Add source reliability tracking
class SourceReliability:
    def __init__(self):
        self.source_stats = {}  # source -> {correct: int, total: int}
    
    def update(self, source: str, was_correct: bool):
        if source not in self.source_stats:
            self.source_stats[source] = {"correct": 0, "total": 0}
        self.source_stats[source]["total"] += 1
        if was_correct:
            self.source_stats[source]["correct"] += 1
    
    def get_reliability(self, source: str) -> float:
        if source not in self.source_stats:
            return 0.5  # Default
        stats = self.source_stats[source]
        return stats["correct"] / stats["total"] if stats["total"] > 0 else 0.5
```

---

## Priority 4: Testing & Quality Assurance

### 12. Unit Tests
**Current Issues:**
- No tests
- Hard to verify correctness
- Risky to refactor

**Improvements:**
```python
# Add tests/test_scoring.py
import pytest
from agent.scoring.engine import score_event, aggregate_scores
from agent.memory.schemas import SignalEvent

def test_score_event():
    event = SignalEvent(
        source="funding",
        occurred_at=datetime.now(),
        title="Test",
        detail="Test",
        confidence=0.8,
        magnitude=0.7
    )
    weights = {"funding": 1.2}
    result = score_event(event, weights)
    assert 0.0 <= result.score <= 1.0
    assert result.score == pytest.approx(0.8 * 0.7 * 1.2)

def test_aggregate_scores():
    # Test diminishing returns
    ...
```

### 13. Integration Tests
**Current Issues:**
- No end-to-end testing
- Can't verify full flow

**Improvements:**
```python
# Add tests/test_integration.py
def test_end_to_end():
    # Test full flow with sample data
    ...
```

### 14. Test Fixtures
**Current Issues:**
- Sample data scattered
- Hard to reuse

**Improvements:**
```python
# Add tests/fixtures.py
@pytest.fixture
def sample_thread():
    return GmailThread(...)

@pytest.fixture
def sample_investor():
    return InvestorProfile(...)
```

---

## Priority 5: Performance & Optimization

### 15. Caching
**Current Issues:**
- Tone profiles recalculated every time
- No caching of expensive operations

**Improvements:**
```python
# Add caching
from functools import lru_cache

@lru_cache(maxsize=100)
def build_tone_profile_cached(sent_email_bodies_tuple):
    """Cached version of tone profile building."""
    return build_tone_profile(list(sent_email_bodies_tuple))
```

### 16. Optimize Signal Processing
**Current Issues:**
- Sequential processing
- Could be parallelized

**Improvements:**
```python
# Add parallel processing
from concurrent.futures import ThreadPoolExecutor

def score_events_parallel(events, investor_weights):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(score_event, ev, investor_weights) for ev in events]
        return [f.result() for f in futures]
```

### 17. Batch Operations
**Current Issues:**
- Processes one deal at a time
- Could batch multiple deals

**Improvements:**
```python
# Add batch processing
def process_multiple_deals(deal_configs: List[Dict]):
    """Process multiple deals in batch."""
    results = []
    for config in deal_configs:
        result = process_single_deal(config)
        results.append(result)
    return results
```

---

## Priority 6: Security & Best Practices

### 18. Path Validation
**Current Issues:**
- No validation of file paths
- Potential security risk

**Improvements:**
```python
# Add path validation
def validate_path(path: Path, must_exist: bool = True) -> Path:
    """Validate and sanitize file paths."""
    resolved = path.resolve()
    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {resolved}")
    # Prevent directory traversal
    if ".." in str(resolved):
        raise ValueError("Invalid path: directory traversal detected")
    return resolved
```

### 19. Input Sanitization
**Current Issues:**
- No sanitization of user inputs
- Potential injection risks

**Improvements:**
```python
# Add sanitization
import html

def sanitize_email_content(text: str) -> str:
    """Sanitize email content to prevent injection."""
    # Remove potentially dangerous characters
    text = html.escape(text)
    # Limit length
    return text[:10000]  # Reasonable email length limit
```

### 20. Environment Variables
**Current Issues:**
- No support for environment-based config
- Hardcoded values

**Improvements:**
```python
# Add env support
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_THRESHOLD = float(os.getenv("DEFAULT_THRESHOLD", "0.75"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

---

## Priority 7: Code Organization

### 21. Refactor Long Functions
**Current Issues:**
- `demo_run.main()` is too long
- Does too many things

**Improvements:**
```python
# Break into smaller functions
def load_inputs(args):
    """Load and validate all input files."""
    ...

def process_signals(events, company, investor_weights):
    """Process and score signals."""
    ...

def make_decision(scored, threshold):
    """Make re-engagement decision."""
    ...

def generate_outputs(decision, draft, args):
    """Generate output files."""
    ...
```

### 22. Separate Concerns
**Current Issues:**
- Business logic mixed with I/O
- Hard to test

**Improvements:**
```python
# Separate into service classes
class ReengagementService:
    def __init__(self, config):
        self.config = config
        self.scorer = ScoringEngine()
        self.personalizer = PersonalizationEngine()
    
    def process_deal(self, deal_data):
        """Process a single deal."""
        ...
```

### 23. Add Abstract Base Classes
**Current Issues:**
- Interfaces not well defined
- Hard to swap implementations

**Improvements:**
```python
# Add ABCs
from abc import ABC, abstractmethod

class SignalCollector(ABC):
    @abstractmethod
    def collect(self, company: str) -> List[SignalEvent]:
        """Collect signals for a company."""
        pass

class PersonalizationEngine(ABC):
    @abstractmethod
    def build_tone_profile(self, emails: List[str]) -> ToneProfile:
        """Build tone profile from emails."""
        pass
```

---

## Priority 8: Documentation

### 24. API Documentation
**Current Issues:**
- No API docs
- Hard to understand interfaces

**Improvements:**
- Add docstrings to all public functions
- Generate Sphinx documentation
- Add usage examples

### 25. Code Comments
**Current Issues:**
- Some complex logic not explained
- Algorithm rationale missing

**Improvements:**
```python
# Add explanatory comments for complex algorithms
def aggregate_scores(scored):
    # Diminishing returns aggregation prevents over-weighting
    # Formula: 1 - ∏(1 - score_i)
    # This ensures multiple weak signals don't dominate
    # Example: 3 signals at 0.5 each = 0.875 (not 1.5)
    ...
```

---

## Implementation Priority

### Week 1: Critical Fixes
1. Error handling & validation
2. Logging
3. Input validation

### Week 2: Code Quality
4. Type hints
5. Docstrings
6. Configuration management

### Week 3: Features
7. Signal deduplication
8. Time-based filtering
9. Better personalization

### Week 4: Testing
10. Unit tests
11. Integration tests
12. Test fixtures

### Week 5: Performance
13. Caching
14. Parallel processing
15. Batch operations

### Week 6: Security & Polish
16. Path validation
17. Input sanitization
18. Code refactoring

---

## Quick Wins (Can Do Immediately)

1. **Add logging** - 30 minutes
2. **Add type hints** - 1 hour
3. **Extract constants** - 30 minutes
4. **Add docstrings** - 2 hours
5. **Add error handling** - 1 hour

---

## Metrics to Track After Improvements

- **Code Coverage**: Target 80%+
- **Type Coverage**: Target 100%
- **Error Rate**: Track and reduce
- **Performance**: Measure latency improvements
- **Maintainability**: Track code complexity

---

## Summary

**Total Improvements**: 25 major areas
**Estimated Time**: 4-6 weeks for full implementation
**Quick Wins**: 5 improvements (~5 hours)

**Focus Areas**:
1. Reliability (error handling, validation)
2. Maintainability (type hints, docs, tests)
3. Features (deduplication, time filtering)
4. Performance (caching, parallelization)
5. Security (validation, sanitization)


