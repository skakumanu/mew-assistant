"""
UI locale resolution and message rendering.

Locale comes from the device (``Accept-Language``) or from an explicit
per-user choice, never from sniffing the content of a message. Every user
facing sentence is a template with named placeholders held in
``app/locales/<code>.json``; reason codes from the rule engine resolve
through the ``reasons.*`` section of the same file.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

LOCALE_DIR = Path(__file__).resolve().parent.parent / "locales"
DEFAULT_LOCALE = "en"

# Accept-Language entries look like "es-419;q=0.8" - we want the base tag.
_ACCEPT_LANGUAGE_ENTRY = re.compile(
    r"^\s*([A-Za-z]{1,8}(?:-[A-Za-z0-9]{1,8})*)\s*(?:;\s*q=([0-9.]+))?\s*$"
)


@lru_cache(maxsize=None)
def available_locales() -> tuple:
    """Locale codes that ship with the app, sorted, English first."""
    codes = sorted(p.stem for p in LOCALE_DIR.glob("*.json"))
    if DEFAULT_LOCALE in codes:
        codes.remove(DEFAULT_LOCALE)
        codes.insert(0, DEFAULT_LOCALE)
    return tuple(codes)


@lru_cache(maxsize=None)
def load_locale(code: str) -> Dict[str, Any]:
    """Load one locale file, falling back to English if it is missing."""
    path = LOCALE_DIR / f"{code}.json"
    if not path.exists():
        if code == DEFAULT_LOCALE:
            raise FileNotFoundError(f"Missing default locale file: {path}")
        logger.warning("Unknown locale %r, falling back to %r", code, DEFAULT_LOCALE)
        return load_locale(DEFAULT_LOCALE)
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def resolve_locale(accept_language: Optional[str], override: Optional[str] = None) -> str:
    """
    Pick a locale code.

    ``override`` is the person's explicit choice and always wins. Otherwise
    the device's ``Accept-Language`` header decides, honouring q-values and
    falling back from ``es-MX`` to ``es``.
    """
    supported = available_locales()

    if override:
        base = override.split("-")[0].lower()
        if override.lower() in supported:
            return override.lower()
        if base in supported:
            return base

    if not accept_language:
        return DEFAULT_LOCALE

    ranked: List[tuple] = []
    for index, raw in enumerate(accept_language.split(",")):
        match = _ACCEPT_LANGUAGE_ENTRY.match(raw)
        if not match:
            continue
        tag = match.group(1).lower()
        try:
            quality = float(match.group(2)) if match.group(2) else 1.0
        except ValueError:
            quality = 1.0
        # Stable ordering: higher q first, then the order the client sent.
        ranked.append((-quality, index, tag))

    for _, _, tag in sorted(ranked):
        if tag == "*":
            return DEFAULT_LOCALE
        if tag in supported:
            return tag
        base = tag.split("-")[0]
        if base in supported:
            return base

    return DEFAULT_LOCALE


class Translator:
    """Renders locale templates. One instance per reader, per request."""

    def __init__(self, code: str = DEFAULT_LOCALE, source: str = "device"):
        self.code = code
        self.source = source
        self.strings = load_locale(code)

    # -- metadata ---------------------------------------------------------

    @property
    def dir(self) -> str:
        return self.strings.get("meta", {}).get("dir", "ltr")

    @property
    def clock(self) -> str:
        return self.strings.get("meta", {}).get("clock", "12h")

    @property
    def name(self) -> str:
        return self.strings.get("meta", {}).get("name", self.code)

    @property
    def days(self) -> List[str]:
        return self.strings.get("days", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

    # -- lookup -----------------------------------------------------------

    def raw(self, key: str) -> Any:
        """Look up a dotted key, falling back to English, then to the key."""
        value = self._walk(self.strings, key)
        if value is None and self.code != DEFAULT_LOCALE:
            value = self._walk(load_locale(DEFAULT_LOCALE), key)
        return key if value is None else value

    @staticmethod
    def _walk(tree: Dict[str, Any], key: str) -> Any:
        node: Any = tree
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    def t(self, key: str, **params: Any) -> str:
        """Render a template. Unknown placeholders are left untouched."""
        template = self.raw(key)
        if isinstance(template, dict):
            # Plural forms: {"one": ..., "other": ...}
            count = params.get("count")
            template = template.get("one" if count == 1 else "other", template.get("other", key))
        if not isinstance(template, str):
            return str(template)
        out = template
        for name, value in params.items():
            out = out.replace("{" + name + "}", str(value))
        return out

    def reason(self, code: str) -> str:
        """Render one rule-engine reason code as a sentence fragment."""
        return self.t(f"reasons.{code}")

    def reasons(self, codes: Iterable[str]) -> str:
        """Join several reason fragments the way the design's cards read."""
        parts = [self.reason(c) for c in codes]
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return ", ".join(parts[:-1]) + " · " + parts[-1]

    # -- formatting -------------------------------------------------------

    def time(self, moment: datetime) -> str:
        """Format a clock time using this locale's 12h/24h preference."""
        if self.clock == "24h":
            return moment.strftime("%H:%M")
        hour = moment.hour % 12 or 12
        suffix = "am" if moment.hour < 12 else "pm"
        if moment.minute:
            return f"{hour}:{moment.minute:02d}{suffix}"
        return f"{hour}{suffix}"

    def day_name(self, moment: datetime) -> str:
        return self.days[moment.weekday()]

    def date_label(self, moment: datetime) -> str:
        """A short date, e.g. "Sep 10". Localised month names come from the OS."""
        return f"{moment.strftime('%b')} {moment.day}"

    def when(self, moment: datetime) -> str:
        """ "Thu 5pm" - the phrase the parent's cards are built from."""
        return f"{self.day_name(moment)} {self.time(moment)}"

    def option_label(self, moment: datetime) -> str:
        """ "Thu, Sep 10 at 4:30pm" - one alternative row."""
        return self.t(
            "parent.option_at",
            day=self.day_name(moment),
            date=self.date_label(moment),
            time=self.time(moment),
        )

    def as_dict(self) -> Dict[str, Any]:
        """The whole string table, for handing to a template or a client."""
        return {
            "code": self.code,
            "source": self.source,
            "strings": self.strings,
        }
