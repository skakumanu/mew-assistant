"""
Verifies the two `.gitleaks.toml` rules added to close a demonstrated
blind spot in gitleaks v8.18.4's bundled default ruleset (see
docs/features/adopt-engineering-discipline-practices/spec.md, section 2).

Loads `.gitleaks.toml` with the stdlib `tomllib` and checks each new
rule's own regex with Python's `re` - never invoking the gitleaks binary,
and never committing or referencing a real secret. Fixtures below are
synthetic, incident-*shaped* strings only, built via string concatenation
so no single source line ever contains one unbroken
`scheme://user:pass@host`- or `GOCSPX-...`-shaped literal - the exact
thing this file exists to test for. Splitting the literal defeats
source-text secret scanners (gitleaks, GitGuardian) that scan this file's
raw text; the concatenated runtime value is what actually gets passed to
`pattern.search()` below, so the regex itself is still exercised in full.
"""

import re
import tomllib
from pathlib import Path

GITLEAKS_TOML = Path(__file__).resolve().parent.parent / ".gitleaks.toml"


def _load_rule(rule_id: str) -> dict:
    config = tomllib.loads(GITLEAKS_TOML.read_text(encoding="utf-8"))
    for rule in config.get("rules", []):
        if rule.get("id") == rule_id:
            return rule
    raise AssertionError(f"No [[rules]] entry with id={rule_id!r} in .gitleaks.toml")


# Benign strings any new rule must never flag - a credential-free URL, and
# the pre-existing allowlist placeholders this file's sibling rules coexist
# with.
BENIGN_STRINGS = [
    "https://example.com/no-credentials-here",
    "postgresql://x/y",
    "YOUR_ACCESS_TOKEN",
    "Authorization: Bearer YOUR_TOKEN",
]


class TestConnectionStringCredentialRule:
    """
    Incident shape: a plaintext password inside a `scheme://user:pass@host`
    connection string - exactly `app/utils/config.py`'s own `DATABASE_URL`
    shape, and the shape gitleaks' default `generic-api-key` rule cannot
    reach (no keyword/operator pair sits next to the password there).
    """

    def _regex(self):
        rule = _load_rule("connection-string-credential")
        return re.compile(rule["regex"])

    def test_matches_a_postgres_connection_string_with_a_credential(self):
        pattern = self._regex()
        fixture = "postgresql://mewadmin:REDACTEDFORTEST1234" + "@db.example.com:5432/mew_assistant"
        assert pattern.search(fixture)

    def test_matches_every_declared_scheme(self):
        pattern = self._regex()
        credential = "REDACTEDFORTEST1234"
        fixtures = [
            "postgres://user:" + credential + "@host:5432/db",
            "mysql://user:" + credential + "@host:3306/db",
            "mongodb://user:" + credential + "@host:27017/db",
            "mongodb+srv://user:" + credential + "@cluster0.mongodb.net/db",
            "redis://:" + credential + "@host:6379",
            "amqp://user:" + credential + "@host:5672/vhost",
            "amqps://user:" + credential + "@host:5671/vhost",
        ]
        for fixture in fixtures:
            assert pattern.search(fixture), f"expected a match for {fixture!r}"

    def test_does_not_match_a_credential_free_url(self):
        pattern = self._regex()
        for fixture in BENIGN_STRINGS:
            assert not pattern.search(fixture), f"unexpected match for {fixture!r}"

    def test_does_not_match_the_existing_allowlist_placeholders(self):
        pattern = self._regex()
        config = tomllib.loads(GITLEAKS_TOML.read_text(encoding="utf-8"))
        for placeholder in config["allowlist"]["regexes"]:
            # These are themselves regex snippets; treat each as the literal
            # example text a doc would show, minus the deliberately-broad
            # connection-string placeholders this same PR adds for its own
            # false positives (those are expected to match - that's the
            # point of allowlisting them).
            if "postgresql://mew" in placeholder:
                continue
            assert not pattern.search(placeholder), f"unexpected match for {placeholder!r}"


class TestGoogleOAuthClientSecretRule:
    """
    Incident shape: a Google OAuth client secret, `GOCSPX-` prefixed -
    Google's own scanner-friendly format, recognisable without a nearby
    keyword (unlike gitleaks' default `generic-api-key`, defeated here by
    the incident's `name`/`value` line split).
    """

    def _regex(self):
        rule = _load_rule("google-oauth-client-secret")
        return re.compile(rule["regex"])

    def test_matches_a_gocspx_prefixed_secret(self):
        pattern = self._regex()
        # Same length/shape as the real leaked value, never the value itself.
        fixture = "GOCSPX-" + "aBcDeFgHiJkLmNoPqRsT1234"
        assert pattern.search(fixture)

    def test_matches_even_split_across_a_name_value_json_export(self):
        """The exact shape that defeated `generic-api-key` in the incident."""
        pattern = self._regex()
        secret = "GOCSPX-" + "aBcDeFgHiJkLmNoPqRsT1234"
        fixture = '"name":  "GOOGLE_CLIENT_SECRET",\n"value":  "' + secret + '"'
        assert pattern.search(fixture)

    def test_does_not_match_a_credential_free_url(self):
        pattern = self._regex()
        for fixture in BENIGN_STRINGS:
            assert not pattern.search(fixture), f"unexpected match for {fixture!r}"

    def test_does_not_match_the_existing_allowlist_placeholders(self):
        pattern = self._regex()
        config = tomllib.loads(GITLEAKS_TOML.read_text(encoding="utf-8"))
        for placeholder in config["allowlist"]["regexes"]:
            assert not pattern.search(placeholder), f"unexpected match for {placeholder!r}"
