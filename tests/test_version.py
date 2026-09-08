"""
Locks the three version-shaped signals in this repo to one source.

`settings.APP_VERSION` is the single source every runtime signal reads
from. This test fails CI the moment `GET /version` or `CHANGELOG.md`'s top
versioned entry disagrees with it - the exact drift
(`docs/features/adopt-engineering-discipline-practices/intent.md`) that
used to go unnoticed.
"""

import re
from pathlib import Path

from app.utils.config import settings

CHANGELOG_PATH = Path(__file__).resolve().parent.parent / "CHANGELOG.md"

# Matches "## [1.1.0]" but not "## [Unreleased]" - only a real semver
# heading counts as "the top version".
_VERSION_HEADING = re.compile(r"^##\s+\[(\d+\.\d+\.\d+)\]", re.MULTILINE)


def _changelog_top_version() -> str:
    text = CHANGELOG_PATH.read_text(encoding="utf-8")
    match = _VERSION_HEADING.search(text)
    assert match, "CHANGELOG.md has no versioned '## [X.Y.Z]' heading"
    return match.group(1)


def test_version_endpoint_reports_settings_app_version(client):
    response = client.get("/version")

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == settings.APP_VERSION
    assert body["version"] != "landing-page-v2"
    assert "deployed" in body


def test_app_version_matches_changelogs_top_versioned_entry():
    """
    A PR that bumps one of `settings.APP_VERSION` / `CHANGELOG.md` without
    the other must fail here - that is the entire point of this test.
    """
    assert settings.APP_VERSION == _changelog_top_version()


def test_changelog_parser_skips_unreleased():
    """`## [Unreleased]` must never itself be read as a version string."""
    text = CHANGELOG_PATH.read_text(encoding="utf-8")
    assert "## [Unreleased]" in text
    assert _changelog_top_version() != "Unreleased"
