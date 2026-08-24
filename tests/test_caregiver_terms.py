"""
"Parent" and "guardian" are interchangeable.

Plenty of children are raised by a grandparent, a foster carer or a legal
guardian. Both words reach the same handlers, carry the same permissions and
store the same value; only the label a family reads differs.
"""

from datetime import datetime, timedelta

import pytest
from fastapi import status

from app.database.models import (
    CAREGIVER_TERMS,
    DEFAULT_CAREGIVER_TERM,
    RequestedBy,
    ScheduledSession,
    User,
)
from app.services.ruleset_service import RuleSetService
from app.utils.auth import (
    get_password_hash,
    verify_guardian_account,
    verify_parent_account,
)
from app.utils.locale import Translator

from .conftest import _auth


class TestVocabulary:
    def test_both_words_are_the_same_persona(self):
        assert RequestedBy("guardian") is RequestedBy.PARENT
        assert RequestedBy("Guardian") is RequestedBy.PARENT
        assert RequestedBy("parent") is RequestedBy.PARENT
        # Stored as one value, so nothing downstream has to know which.
        assert RequestedBy("guardian").value == "parent"

    def test_an_unrelated_word_is_still_rejected(self):
        with pytest.raises(ValueError):
            RequestedBy("landlord")

    def test_the_two_terms_are_named_once(self):
        assert CAREGIVER_TERMS == ("parent", "guardian")
        assert DEFAULT_CAREGIVER_TERM == "parent"

    def test_the_same_permission_check_answers_to_both_names(self):
        assert verify_guardian_account is verify_parent_account

    def test_every_locale_has_both_words(self):
        for code in ("en", "es", "hi", "ar"):
            translator = Translator(code)
            assert translator.caregiver("parent")
            assert translator.caregiver("guardian")

    def test_an_unknown_term_falls_back_rather_than_guessing(self):
        translator = Translator("en")

        assert translator.caregiver("guardian") == "Guardian"
        assert translator.caregiver("landlord") == "Parent"
        assert translator.caregiver(None) == "Parent"
        assert translator.caregiver("  GUARDIAN  ") == "Guardian"


class TestRoutes:
    """Every /parent path answers on /guardian too, and vice versa."""

    @pytest.mark.parametrize(
        "path",
        ["/approvals/pending", "/approvals/inbox", "/approvals/history", "/log", "/week"],
    )
    def test_both_prefixes_reach_the_same_handler(self, client, family, path):
        parent_response = client.get("/parent" + path, headers=_auth(family["parent"]))
        guardian_response = client.get("/guardian" + path, headers=_auth(family["parent"]))

        assert parent_response.status_code == status.HTTP_200_OK
        assert guardian_response.status_code == parent_response.status_code
        assert guardian_response.json() == parent_response.json()

    def test_a_decision_made_on_the_guardian_path_is_the_same_decision(
        self, client, db_session, family, rules, session_row
    ):
        parked = client.post(
            "/requests",
            json={
                "session_id": session_row.id,
                "kind": "move",
                "new_start": session_row.start_utc.replace(hour=17).isoformat(),
            },
            headers=_auth(family["provider_login"]),
        ).json()

        response = client.post(
            f"/guardian/approvals/{parked['request_id']}/choose",
            json={"alternative_index": 0},
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_200_OK
        chosen = datetime.fromisoformat(parked["alternatives"][0]["start"])
        db_session.refresh(session_row)
        assert session_row.start_utc == chosen

    def test_a_kid_is_refused_on_both_paths(self, client, family):
        for prefix in ("/parent", "/guardian"):
            response = client.get(prefix + "/approvals/pending", headers=_auth(family["kid"]))
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_the_refusal_names_both_words(self, client, family):
        response = client.get("/parent/approvals/pending", headers=_auth(family["kid"]))

        detail = response.json()["detail"].lower()
        assert "parent" in detail and "guardian" in detail

    def test_both_screens_are_served(self, client):
        parent_screen = client.get("/app/parent")
        guardian_screen = client.get("/app/guardian")

        assert parent_screen.status_code == status.HTTP_200_OK
        assert guardian_screen.status_code == status.HTTP_200_OK
        # The path a person opened decides the word they see first.
        assert 'data-caregiver-term="parent"' in parent_screen.text
        assert 'data-caregiver-term="guardian"' in guardian_screen.text
        assert ">Guardian<" in guardian_screen.text


class TestFamilyChoice:
    def test_rules_default_to_parent(self, client, family):
        body = client.get("/rules", headers=_auth(family["parent"])).json()

        assert body["caregiver_term"] == "parent"
        assert body["caregiver_label"] == "Parent"

    def test_a_family_can_choose_guardian(self, client, family):
        body = client.put(
            "/rules", json={"caregiver_term": "guardian"}, headers=_auth(family["parent"])
        ).json()

        assert body["caregiver_term"] == "guardian"
        assert body["caregiver_label"] == "Guardian"

    def test_the_choice_survives_and_reads_in_the_readers_language(self, client, family):
        client.put("/rules", json={"caregiver_term": "guardian"}, headers=_auth(family["parent"]))

        headers = _auth(family["parent"])
        headers["Accept-Language"] = "es-MX,es;q=0.9"
        body = client.get("/rules", headers=headers).json()

        assert body["caregiver_term"] == "guardian"
        assert body["caregiver_label"] == "Tutor o tutora"

    def test_an_unknown_term_is_refused_rather_than_stored(self, client, family):
        response = client.put(
            "/rules", json={"caregiver_term": "landlord"}, headers=_auth(family["parent"])
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_choosing_a_word_changes_nothing_else(self, client, family, rules):
        before = client.get("/rules", headers=_auth(family["parent"])).json()
        after = client.put(
            "/rules", json={"caregiver_term": "guardian"}, headers=_auth(family["parent"])
        ).json()

        for field in (
            "min_notice_hours",
            "latest_end",
            "buffer_minutes",
            "require_same_provider_person",
            "cancellation_needs_approval",
        ):
            assert before[field] == after[field], field

    def test_the_word_reaches_the_inbox_card(self, client, db_session, family, rules):
        """A card raised by the caregiver themselves is labelled their way."""
        client.put("/rules", json={"caregiver_term": "guardian"}, headers=_auth(family["parent"]))

        start = (datetime.utcnow() + timedelta(days=3)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        row = ScheduledSession(
            child_id=family["kid"].id,
            provider_org_id=family["org"].id,
            provider_person_id=family["dana"].id,
            title="ABA session",
            activity_type="aba",
            start_utc=start,
            duration_minutes=90,
        )
        db_session.add(row)
        db_session.commit()
        db_session.refresh(row)

        # The caregiver asks for a swap, which their own rules park.
        client.post(
            "/requests",
            json={
                "session_id": row.id,
                "kind": "swap_provider",
                "new_start": start.isoformat(),
                "new_provider_person_id": family["jordan"].id,
            },
            headers=_auth(family["parent"]),
        )

        card = client.get("/guardian/approvals/inbox", headers=_auth(family["parent"])).json()[0]

        assert card["requested_by"] == "parent"  # one stored value
        assert card["source_label"] == "Guardian"  # the family's own word

    def test_the_service_falls_back_when_no_rules_exist_yet(self, db_session, parent_only):
        assert RuleSetService(db_session).caregiver_term(parent_only.id) == "parent"


@pytest.fixture
def parent_only(db_session):
    user = User(
        email="alone@example.com",
        username="alone",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_kid_account=False,
    )
    db_session.add(user)
    db_session.commit()
    return user
