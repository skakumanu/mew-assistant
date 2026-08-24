"""
Setting up, and signing in.

"One person sets it up: the parent. Fifteen minutes, once." And the screens
take an email and a password like anything else, rather than a pasted token.
"""

import httpx
from fastapi import status

from app.database.models import ProviderPerson, RuleSet, ScheduledSession, User
from app.utils.auth import SESSION_COOKIE, get_password_hash

from .conftest import _auth

ICS = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:aba-100
SUMMARY:ABA session
DTSTART:20260910T153000Z
DTEND:20260910T170000Z
END:VEVENT
END:VCALENDAR
"""


def _feed(monkeypatch, body=ICS, status_code=200):
    import app.integrations.calendar_sync.ics as ics_module

    real = ics_module.IcsFeedAdapter

    def patched(url, client=None):
        transport = httpx.MockTransport(lambda request: httpx.Response(status_code, text=body))
        return real(url, client=httpx.AsyncClient(transport=transport))

    monkeypatch.setattr("app.services.calendar_sync_service.IcsFeedAdapter", patched)


class TestSetup:
    def test_one_call_produces_a_working_family(self, client, db_session, family, monkeypatch):
        _feed(monkeypatch)

        response = client.post(
            "/onboarding/setup",
            json={
                "child": {"display_name": "Ellie", "age": 8},
                "providers": [
                    {
                        "name": "Willow Speech",
                        "kind": "speech",
                        "calendar_provider": "ics",
                        "calendar_account_id": "https://example.test/feed.ics",
                        "people": [{"display_name": "Marcus L."}],
                    }
                ],
            },
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()

        child = db_session.query(User).filter(User.id == body["child_id"]).one()
        assert child.is_kid_account is True and child.parent_id == family["parent"].id

        # Rules exist with the design's defaults, so the loop can run at once.
        ruleset = db_session.query(RuleSet).filter(RuleSet.id == body["ruleset_id"]).one()
        assert ruleset.min_notice_hours == 24

        org = body["providers"][0]
        assert org["calendar_connected"] is True
        assert org["sessions_imported"] == 1
        assert [p["display_name"] for p in org["people"]] == ["Marcus L."]

        assert db_session.query(ScheduledSession).count() == 1

    def test_rules_can_be_set_during_setup(self, client, db_session, family):
        response = client.post(
            "/onboarding/setup",
            json={
                "child": {"display_name": "Ellie"},
                "rules": {"min_notice_hours": 48, "caregiver_term": "guardian"},
            },
            headers=_auth(family["parent"]),
        )

        ruleset = (
            db_session.query(RuleSet).filter(RuleSet.id == response.json()["ruleset_id"]).one()
        )
        assert ruleset.min_notice_hours == 48
        assert ruleset.caregiver_term == "guardian"

    def test_running_setup_again_does_not_duplicate_anything(
        self, client, db_session, family, monkeypatch
    ):
        _feed(monkeypatch)
        payload = {
            "child": {"display_name": "Ellie"},
            "providers": [
                {
                    "name": "Willow Speech",
                    "kind": "speech",
                    "calendar_provider": "ics",
                    "calendar_account_id": "https://example.test/feed.ics",
                    "people": [{"display_name": "Marcus L."}],
                }
            ],
        }

        first = client.post(
            "/onboarding/setup", json=payload, headers=_auth(family["parent"])
        ).json()
        second = client.post(
            "/onboarding/setup", json=payload, headers=_auth(family["parent"])
        ).json()

        assert first["child_id"] == second["child_id"]
        assert first["providers"][0]["id"] == second["providers"][0]["id"]
        assert (
            db_session.query(User)
            .filter(User.parent_id == family["parent"].id, User.display_name == "Ellie")
            .count()
            == 1
        )
        assert (
            db_session.query(ProviderPerson)
            .filter(ProviderPerson.display_name == "Marcus L.")
            .count()
            == 1
        )
        assert db_session.query(ScheduledSession).count() == 1

    def test_a_child_without_an_email_still_gets_an_account(self, client, db_session, family):
        """A tablet that is simply already signed in is the normal case."""
        body = client.post(
            "/onboarding/setup",
            json={"child": {"display_name": "Sam"}},
            headers=_auth(family["parent"]),
        ).json()

        child = db_session.query(User).filter(User.id == body["child_id"]).one()
        assert child.email.endswith("@kid.mew.local")
        assert child.hashed_password  # set, but to something nobody knows

    def test_an_unsupported_calendar_is_refused(self, client, family):
        response = client.post(
            "/onboarding/setup",
            json={
                "child": {"display_name": "Ellie"},
                "providers": [{"name": "Somewhere", "calendar_provider": "carrier-pigeon"}],
            },
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_a_kid_cannot_run_setup(self, client, family):
        response = client.post(
            "/onboarding/setup",
            json={"child": {"display_name": "Ellie"}},
            headers=_auth(family["kid"]),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_a_calendar_that_fails_is_reported_not_swallowed(self, client, family, monkeypatch):
        _feed(monkeypatch, status_code=502)

        body = client.post(
            "/onboarding/setup",
            json={
                "child": {"display_name": "Ellie"},
                "providers": [
                    {
                        "name": "Willow Speech",
                        "calendar_provider": "ics",
                        "calendar_account_id": "https://example.test/feed.ics",
                    }
                ],
            },
            headers=_auth(family["parent"]),
        ).json()

        org = body["providers"][0]
        assert org["sessions_imported"] == 0
        assert org["calendar_error"]


class TestSignIn:
    def test_the_form_is_served(self, client):
        response = client.get("/app/sign-in")

        assert response.status_code == status.HTTP_200_OK
        assert 'name="password"' in response.text

    def test_signing_in_sets_an_httponly_cookie(self, client, db_session):
        user = User(
            email="signin@example.com",
            username="signin",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_kid_account=False,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/app/sign-in",
            data={"email": "signin@example.com", "password": "password123"},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["location"] == "/app/parent"
        cookie = response.headers["set-cookie"]
        assert SESSION_COOKIE in cookie
        assert "HttpOnly" in cookie  # page script must not be able to read it
        assert "samesite=lax" in cookie.lower()

    def test_the_cookie_authenticates_api_calls(self, client, db_session, family):
        client.post(
            "/app/sign-in",
            data={"email": family["parent"].email, "password": "password123"},
        )

        # No Authorization header at all - just the cookie the client kept.
        response = client.get("/rules")

        assert response.status_code == status.HTTP_200_OK

    def test_a_wrong_password_says_only_that_it_did_not_match(self, client, family):
        response = client.post(
            "/app/sign-in",
            data={"email": family["parent"].email, "password": "wrong"},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert "error=1" in response.headers["location"]
        assert SESSION_COOKIE not in response.headers.get("set-cookie", "")

    def test_an_unknown_account_is_indistinguishable_from_a_wrong_password(self, client, family):
        unknown = client.post(
            "/app/sign-in",
            data={"email": "nobody@example.com", "password": "whatever"},
            follow_redirects=False,
        )
        wrong = client.post(
            "/app/sign-in",
            data={"email": family["parent"].email, "password": "wrong"},
            follow_redirects=False,
        )

        assert unknown.headers["location"] == wrong.headers["location"]

    def test_signing_out_drops_the_cookie(self, client, family):
        client.post(
            "/app/sign-in",
            data={"email": family["parent"].email, "password": "password123"},
        )

        response = client.post("/app/sign-out", follow_redirects=False)

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert client.get("/rules").status_code == status.HTTP_401_UNAUTHORIZED

    def test_an_offsite_next_is_discarded(self, client, family):
        """`next` is attacker-controlled, so anything non-local is dropped."""
        response = client.post(
            "/app/sign-in",
            data={
                "email": family["parent"].email,
                "password": "password123",
                "next": "https://evil.example/steal",
            },
            follow_redirects=False,
        )

        assert response.headers["location"] == "/app/parent"

    def test_a_protocol_relative_next_is_discarded(self, client, family):
        response = client.post(
            "/app/sign-in",
            data={
                "email": family["parent"].email,
                "password": "password123",
                "next": "//evil.example/steal",
            },
            follow_redirects=False,
        )

        assert response.headers["location"] == "/app/parent"

    def test_a_local_next_is_honoured(self, client, family):
        response = client.post(
            "/app/sign-in",
            data={
                "email": family["parent"].email,
                "password": "password123",
                "next": "/app/kid",
            },
            follow_redirects=False,
        )

        assert response.headers["location"] == "/app/kid"

    def test_a_bearer_header_still_wins(self, client, family):
        """API clients are never silently downgraded to a cookie."""
        response = client.get("/rules", headers=_auth(family["parent"]))

        assert response.status_code == status.HTTP_200_OK
