"""
Setting up, and signing in.

"One person sets it up: the parent. Fifteen minutes, once." Signing in
itself happens at WorkOS AuthKit's hosted UI (see tests/test_workos_auth.py
for that flow) - what's tested here is everything downstream of it: the
redirect that gets a browser there, the safety of the `next` parameter,
and what the resulting session cookie can do.
"""

import httpx
from fastapi import status

from app.database.models import (
    ProviderOrgConnection,
    ProviderPerson,
    RuleSet,
    ScheduledSession,
    User,
)
from app.utils.auth import SESSION_COOKIE, create_access_token

from .conftest import _auth


def _sign_in_as(client, user):
    """
    Set the session cookie directly, the way the WorkOS callback would -
    without needing a real WorkOS round trip in a test that isn't about
    sign-in itself.

    The domain must match the domain httpx actually stores for a
    server-issued cookie against TestClient's host ("testserver.local", not
    "testserver") - otherwise this cookie and a later server-issued
    Set-Cookie (e.g. from signing out) land in the client's cookie jar as
    two distinct entries instead of one overriding the other.
    """
    token = create_access_token({"sub": user.email, "user_id": user.id})
    client.cookies.set(SESSION_COOKIE, token, domain="testserver.local")


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

    def test_setup_records_this_familys_ownership_of_the_provider(
        self, client, db_session, family
    ):
        """
        So the new Providers tab (GET /calendar-sync/orgs) can show what
        this family actually added, without ProviderOrg's global naming
        leaking another family's providers into the list.
        """
        body = client.post(
            "/onboarding/setup",
            json={
                "child": {"display_name": "Ellie"},
                "providers": [{"name": "Willow Speech", "kind": "speech"}],
            },
            headers=_auth(family["parent"]),
        ).json()

        org_id = body["providers"][0]["id"]
        connection = (
            db_session.query(ProviderOrgConnection)
            .filter(
                ProviderOrgConnection.org_id == org_id,
                ProviderOrgConnection.parent_id == family["parent"].id,
            )
            .one()
        )
        assert connection is not None

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
    def test_get_redirects_to_workos(self, client):
        """No password form anymore - WorkOS's hosted UI is the whole flow."""
        response = client.get("/app/sign-in", follow_redirects=False)

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["location"].startswith("/auth/workos/login?next=")

    def test_the_wizard_page_is_served(self, client):
        response = client.get("/app/setup")

        assert response.status_code == status.HTTP_200_OK
        assert "wizard-child-name" in response.text

    def test_the_cookie_authenticates_api_calls(self, client, family):
        _sign_in_as(client, family["parent"])

        # No Authorization header at all - just the cookie the client kept.
        response = client.get("/rules")

        assert response.status_code == status.HTTP_200_OK

    def test_signing_out_drops_the_cookie(self, client, family):
        _sign_in_as(client, family["parent"])

        response = client.post("/app/sign-out", follow_redirects=False)

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert client.get("/rules").status_code == status.HTTP_401_UNAUTHORIZED

    def test_an_offsite_next_is_discarded(self, client):
        """`next` is attacker-controlled, so anything non-local is dropped."""
        response = client.get(
            "/app/sign-in",
            params={"next": "https://evil.example/steal"},
            follow_redirects=False,
        )

        assert response.headers["location"] == "/auth/workos/login?next=/app/parent"

    def test_a_protocol_relative_next_is_discarded(self, client):
        response = client.get(
            "/app/sign-in",
            params={"next": "//evil.example/steal"},
            follow_redirects=False,
        )

        assert response.headers["location"] == "/auth/workos/login?next=/app/parent"

    def test_a_local_next_is_honoured(self, client):
        response = client.get(
            "/app/sign-in",
            params={"next": "/app/kid"},
            follow_redirects=False,
        )

        assert response.headers["location"] == "/auth/workos/login?next=/app/kid"

    def test_a_bearer_header_still_wins(self, client, family):
        """API clients are never silently downgraded to a cookie."""
        response = client.get("/rules", headers=_auth(family["parent"]))

        assert response.status_code == status.HTTP_200_OK
