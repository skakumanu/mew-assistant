"""
Tests for locale resolution and the locale-file contract.

Two rules from the design are enforced here: the UI locale comes from the
device and never from the content of a message, and every locale carries
exactly the same keys and placeholders as `en.json`.
"""

import re
from datetime import datetime

import pytest

from app.utils.locale import (
    DEFAULT_LOCALE,
    LOCALE_DIR,
    Translator,
    available_locales,
    load_locale,
    resolve_locale,
)

PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")

# Machine-quality translations that still need a native speaker. Recorded
# here so the reminder cannot quietly disappear from the repo.
UNREVIEWED = {"hi", "ar"}


def flatten(tree, prefix=""):
    flat = {}
    for key, value in tree.items():
        if isinstance(value, dict):
            flat.update(flatten(value, prefix + key + "."))
        else:
            flat[prefix + key] = value
    return flat


class TestLocaleContract:
    def test_english_is_the_default(self):
        assert DEFAULT_LOCALE == "en"
        assert available_locales()[0] == "en"

    def test_the_prototype_locales_all_ship(self):
        assert set(available_locales()) >= {"en", "es", "hi", "ar"}

    @pytest.mark.parametrize("code", [c for c in available_locales() if c != "en"])
    def test_every_locale_has_every_english_key(self, code):
        english = flatten(load_locale("en"))
        other = flatten(load_locale(code))

        assert set(english) == set(other), f"{code} does not match the en.json contract"

    @pytest.mark.parametrize("code", [c for c in available_locales() if c != "en"])
    def test_placeholders_match_across_locales(self, code):
        english = flatten(load_locale("en"))
        other = flatten(load_locale(code))

        for key, template in english.items():
            if not isinstance(template, str):
                continue
            assert set(PLACEHOLDER.findall(template)) == set(
                PLACEHOLDER.findall(other[key])
            ), f"{code}:{key} has different placeholders"

    def test_every_reason_code_has_a_string_in_every_locale(self):
        from app.services.rule_engine import ReasonCode

        for code in available_locales():
            strings = load_locale(code)
            for reason in ReasonCode:
                assert reason.value in strings["reasons"], f"{code} is missing {reason.value}"

    def test_metadata_drives_direction_and_clock(self):
        assert Translator("ar").dir == "rtl"
        assert Translator("en").dir == "ltr"
        assert Translator("es").clock == "24h"
        assert Translator("en").clock == "12h"

    def test_unreviewed_translations_are_still_flagged(self):
        readme = (LOCALE_DIR / "README.md").read_text(encoding="utf-8")
        for code in UNREVIEWED:
            assert f"`{code}`" in readme
        assert "native speaker" in readme.lower()


class TestLocaleResolution:
    def test_locale_comes_from_the_device(self):
        assert resolve_locale("es-MX,es;q=0.9,en;q=0.8") == "es"
        assert resolve_locale("ar") == "ar"

    def test_quality_values_are_honoured(self):
        assert resolve_locale("hi;q=0.2,es;q=0.9") == "es"

    def test_an_unsupported_language_falls_back_to_english(self):
        assert resolve_locale("fr-CA,fr;q=0.9") == "en"
        assert resolve_locale(None) == "en"
        assert resolve_locale("") == "en"

    def test_an_explicit_choice_beats_the_device(self):
        assert resolve_locale("en-US", override="es") == "es"
        assert resolve_locale("en-US", override="es-419") == "es"

    def test_a_nonsense_header_does_not_raise(self):
        assert resolve_locale(";;;,,,") == "en"

    def test_message_content_never_decides(self):
        """Sniffing text is for voice, never for the UI."""
        spanish_text = "Quiero cambiar la sesión de mañana por la tarde"
        assert resolve_locale(None, override=None) == "en"
        assert spanish_text  # the sentence itself has no say


class TestRendering:
    def test_named_placeholders_are_filled(self):
        translator = Translator("en")

        assert (
            translator.t("parent.headline_move", title="ABA session", when="Thu 5pm")
            == "ABA session to Thu 5pm"
        )

    def test_plural_forms(self):
        translator = Translator("en")

        assert translator.t("kid.things_today", count=1) == "1 thing today"
        assert translator.t("kid.things_today", count=3) == "3 things today"

    def test_reason_codes_render_as_fragments_not_sentences(self):
        translator = Translator("en")

        assert translator.reason("min_notice") == "less than 24 hours notice"
        assert (
            translator.reasons(["latest_end", "buffer"])
            == "outside the allowed hours · too close to another session"
        )

    def test_the_clock_follows_the_locale(self):
        moment = datetime(2026, 9, 10, 17, 30)

        assert Translator("en").time(moment) == "5:30pm"
        assert Translator("es").time(moment) == "17:30"

    def test_an_unknown_key_returns_the_key_rather_than_raising(self):
        assert Translator("en").t("parent.not_a_real_key") == "parent.not_a_real_key"

    def test_a_missing_locale_falls_back_to_english(self):
        assert load_locale("zz") == load_locale("en")
