"""Simple message parser used by tests as a lightweight stub.

This implementation is intentionally small: it extracts simple intent
and entities from plain text for unit tests and benchmarks.
"""
from typing import Dict
import re


def parse_message(text: str) -> Dict[str, str]:
    """Parse a text message and return a minimal intent dict.

    Returns a dict with at least an `intent` key. Tests only require a
    non-empty result for performance benchmarking.
    """
    txt = (text or "").strip()
    # very small heuristics used for tests
    if re.search(r"\bschedule|appointment|meeting|book\b", txt, re.I):
        intent = "schedule"
    elif re.search(r"\bremind|reminder\b", txt, re.I):
        intent = "reminder"
    elif re.search(r"\bthank|thanks\b", txt, re.I):
        intent = "gratitude"
    else:
        intent = "unknown"

    return {"intent": intent, "text": txt}
