"""Very small language detection stub for tests.

This is not a production detector — it simply uses keyword heuristics
to return a language code so the benchmark tests can run.
"""

from typing import Literal


def detect_language(text: str) -> Literal["en", "fr", "es", "jp", "unknown"]:
    t = (text or "").lower()
    if "bonjour" in t or "comment" in t:
        return "fr"
    if "hola" in t or "¿" in t:
        return "es"
    if any(ch in t for ch in ("こんにちは", "こんばんは", "元気")):
        return "jp"
    if t.strip() == "":
        return "unknown"
    return "en"
