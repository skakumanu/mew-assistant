"""
Tests for the parent-facing calendar-connection surface: connecting a
provider's calendar through the UI, listing a family's own providers, and
the Google Calendar OAuth connect flow.

The recurring theme is family scoping: ProviderOrg is a global table (two
families can reference an org with the same name), so every test here that
matters is really asking "does this leak across families" or "does this
authorize against the calling parent, not just any child_id in the URL."
"""

from datetime import datetime, timedelta

import httpx
from fastapi import status
from jose import jwt

from app.database.models import (
    KidCalendarConnection,
    OAuthProvider,
    ProviderOrg,
    ProviderOrgConnection,
    User,
)
from app.integrations.calendar_sync.google import GoogleCalendarAdapter
from app.services.calendar_sync_service import CalendarSyncService
from app.utils.auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_calendar_connect_state,
    get_password_hash,
)

from .conftest import _auth

# Captured once, before any test monkeypatches httpx.AsyncClient - grabbing
# it fresh inside each mock helper would instead pick up a *previous*
# test's patched value when two mocks are chained in the same test.
_REAL_ASYNC_CLIENT = httpx.AsyncClient

ICS = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:aba-100
SUMMARY:ABA session
DTSTART:20260910T153000Z
DTEND:20260910T170000Z
END:VEVENT
END:VCALENDAR
"""


def _serve_ics(monkeypatch, body=ICS, status_code=200):
    import app.integrations.calendar_sync.ics as ics_module

    real = ics_module.IcsFeedAdapter

    def patched(url, client=None):
        transport = httpx.MockTransport(lambda request: httpx.Response(status_code, text=body))
        return real(url, client=httpx.AsyncClient(transport=transport))

    monkeypatch.setattr("app.services.calendar_sync_service.IcsFeedAdapter", patched)


class TestConnectOrgCalendar:
    def test_a_parent_cannot_point_it_at_another_familys_child(self, client, db_session, family):
        """
        The exact pre-existing bug this feature would have made trivially
        reachable: PUT .../calendar took child_id and pulled into that
        child's schedule with no ownership check at all.
        """
        other_parent = User(
            email="other-parent@example.com",
            username="other-parent",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(other_parent)
        db_session.commit()

        response = client.put(
            f"/calendar-sync/orgs/{family['org'].id}/calendar",
            params={"child_id": family["kid"].id},
            json={"calendar_provider": "ics", "calendar_account_id": "https://example.test/feed.ics"},
            headers=_auth(other_parent),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_omitting_child_id_defaults_to_the_callers_own_children(
        self, client, family, monkeypatch
    ):
        _serve_ics(monkeypatch)

        response = client.put(
            f"/calendar-sync/orgs/{family['org'].id}/calendar",
            json={"calendar_provider": "ics", "calendar_account_id": "https://example.test/feed.ics"},
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["ok"] is True
        assert body["created"] == 1

    def test_connecting_records_the_family_ownership(self, client, db_session, family, monkeypatch):
        _serve_ics(monkeypatch)

        client.put(
            f"/calendar-sync/orgs/{family['org'].id}/calendar",
            json={"calendar_provider": "ics", "calendar_account_id": "https://example.test/feed.ics"},
            headers=_auth(family["parent"]),
        )

        connection = (
            db_session.query(ProviderOrgConnection)
            .filter(
                ProviderOrgConnection.org_id == family["org"].id,
                ProviderOrgConnection.parent_id == family["parent"].id,
            )
            .one()
        )
        assert connection is not None

    def test_calendar_display_name_is_saved_and_listed(self, client, family, monkeypatch):
        """
        A raw calendar_account_id (a primary calendar's own email address,
        or an opaque group-calendar id) tells a parent nothing on the
        Providers tab - this is the human-readable name shown instead, so
        it must round-trip through save and the /orgs listing.
        """
        _serve_ics(monkeypatch)

        response = client.put(
            f"/calendar-sync/orgs/{family['org'].id}/calendar",
            json={
                "calendar_provider": "ics",
                "calendar_account_id": "https://example.test/feed.ics",
                "calendar_display_name": "Sindhu's Calendar",
            },
            headers=_auth(family["parent"]),
        )
        assert response.status_code == status.HTTP_200_OK

        listed = client.get("/calendar-sync/orgs", headers=_auth(family["parent"])).json()
        assert listed[0]["calendar_display_name"] == "Sindhu's Calendar"

    def test_pointing_at_a_calendar_the_family_already_pushes_to_is_rejected(
        self, client, db_session, family
    ):
        """
        The other half of the same production incident, from the pull
        side: a provider org's pull source must not be pointed at a
        calendar a kid already pushes to - same loop, same fix.
        """
        db_session.add(
            KidCalendarConnection(
                child_id=family["kid"].id,
                parent_id=family["parent"].id,
                connected_by_user_id=family["parent"].id,
                calendar_provider="google",
                calendar_account_id="shared@group.calendar.google.com",
            )
        )
        db_session.commit()

        response = client.put(
            f"/calendar-sync/orgs/{family['org'].id}/calendar",
            json={
                "calendar_provider": "google",
                "calendar_account_id": "shared@group.calendar.google.com",
            },
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        org = db_session.query(ProviderOrg).filter(ProviderOrg.id == family["org"].id).first()
        assert org.calendar_account_id is None

    def test_resaving_a_pre_existing_collision_unchanged_is_not_blocked(
        self, client, db_session, family
    ):
        """
        Regression guard: a family can have this collision already sitting
        in their data from before the safeguard shipped (or from before a
        kid's push target was actually moved away). Re-saving the org's own
        existing value - a plain reconnect/re-auth, nothing about the
        configuration changing - must not be treated as a NEW collision
        being created, even though the collision itself is real.
        """
        org = family["org"]
        org.calendar_provider = "google"
        org.calendar_account_id = "shared@group.calendar.google.com"
        db_session.add(
            ProviderOrgConnection(
                org_id=org.id, parent_id=family["parent"].id, connected_by_user_id=family["parent"].id
            )
        )
        db_session.add(
            KidCalendarConnection(
                child_id=family["kid"].id,
                parent_id=family["parent"].id,
                calendar_provider="google",
                calendar_account_id="shared@group.calendar.google.com",
            )
        )
        db_session.commit()

        response = client.put(
            f"/calendar-sync/orgs/{org.id}/calendar",
            json={
                "calendar_provider": "google",
                "calendar_account_id": "shared@group.calendar.google.com",
            },
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_200_OK

    def test_an_ics_pull_source_never_collides_with_a_kids_google_push_target(
        self, client, db_session, family, monkeypatch
    ):
        """The collision check is Google-specific - an ICS URL can never match one."""
        db_session.add(
            KidCalendarConnection(
                child_id=family["kid"].id,
                parent_id=family["parent"].id,
                calendar_provider="google",
                calendar_account_id="https://example.test/feed.ics",
            )
        )
        db_session.commit()
        _serve_ics(monkeypatch)

        response = client.put(
            f"/calendar-sync/orgs/{family['org'].id}/calendar",
            json={"calendar_provider": "ics", "calendar_account_id": "https://example.test/feed.ics"},
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_200_OK


class TestListMyOrgs:
    def test_returns_only_this_familys_connected_orgs(self, client, db_session, family, monkeypatch):
        _serve_ics(monkeypatch)
        client.put(
            f"/calendar-sync/orgs/{family['org'].id}/calendar",
            json={"calendar_provider": "ics", "calendar_account_id": "https://example.test/feed.ics"},
            headers=_auth(family["parent"]),
        )

        # A second family references an org with the *same name* - the
        # global-ProviderOrg case this whole redesign exists to guard.
        other_parent = User(
            email="other-parent2@example.com",
            username="other-parent2",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(other_parent)
        db_session.commit()

        response = client.get("/calendar-sync/orgs", headers=_auth(family["parent"]))
        assert response.status_code == status.HTTP_200_OK
        names = [org["name"] for org in response.json()]
        assert names == ["Bright Steps ABA"]

        other_response = client.get("/calendar-sync/orgs", headers=_auth(other_parent))
        assert other_response.json() == []

    def test_an_unconnected_org_does_not_appear(self, client, family):
        """family['org'] exists but nobody has connected it in this test."""
        response = client.get("/calendar-sync/orgs", headers=_auth(family["parent"]))
        assert response.json() == []


class TestGoogleCalendarConnectFlow:
    def _mock_google(self, monkeypatch, email="parent@example.com"):
        import app.routers.calendar_oauth as calendar_oauth

        def handler(request):
            if request.url.path == "/token":
                return httpx.Response(
                    200,
                    json={
                        "access_token": "g-access-1",
                        "refresh_token": "g-refresh-1",
                        "expires_in": 3600,
                    },
                )
            return httpx.Response(200, json={"id": "google-sub-1", "email": email})

        transport = httpx.MockTransport(handler)
        monkeypatch.setattr(
            calendar_oauth.httpx,
            "AsyncClient",
            lambda *args, **kwargs: _REAL_ASYNC_CLIENT(transport=transport),
        )

    def test_connect_redirects_to_google_with_a_signed_state(self, client, family):
        response = client.get(
            "/calendar-sync/google/connect",
            params={"org_id": family["org"].id},
            headers=_auth(family["parent"]),
            follow_redirects=False,
        )

        assert response.status_code in (302, 307)
        location = response.headers["location"]
        assert "accounts.google.com" in location
        assert "state=" in location

    def test_connect_for_an_org_that_does_not_exist_is_rejected(self, client, family):
        response = client.get(
            "/calendar-sync/google/connect",
            params={"org_id": 999999},
            headers=_auth(family["parent"]),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_callback_rejects_a_tampered_state(self, client, family):
        forged = jwt.encode(
            {
                "user_id": family["parent"].id,
                "org_id": family["org"].id,
                "type": "calendar_connect",
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            "wrong-secret",
            algorithm=ALGORITHM,
        )

        response = client.get(
            "/calendar-sync/google/callback",
            params={"code": "abc123", "state": forged},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_callback_rejects_an_expired_state(self, client, family):
        expired = jwt.encode(
            {
                "user_id": family["parent"].id,
                "org_id": family["org"].id,
                "type": "calendar_connect",
                "exp": datetime.utcnow() - timedelta(minutes=1),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        response = client.get(
            "/calendar-sync/google/callback",
            params={"code": "abc123", "state": expired},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_callback_rejects_a_state_of_the_wrong_type(self, client, family):
        """An ordinary access token must not double as connect-flow state."""
        wrong_type_token = create_access_token({"sub": family["parent"].email})

        response = client.get(
            "/calendar-sync/google/callback",
            params={"code": "abc123", "state": wrong_type_token},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_happy_path_stores_the_token_and_enables_a_pull(
        self, client, db_session, family, monkeypatch
    ):
        self._mock_google(monkeypatch)
        state = create_calendar_connect_state(
            user_id=family["parent"].id, org_id=family["org"].id
        )

        response = client.get(
            "/calendar-sync/google/callback",
            params={"code": "abc123", "state": state},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["location"] == f"/app/parent?tab=providers&choose_calendar_org={family['org'].id}"

        link = (
            db_session.query(OAuthProvider)
            .filter(OAuthProvider.user_id == family["parent"].id, OAuthProvider.provider == "google")
            .one()
        )
        assert link.access_token == "g-access-1"

        connection = (
            db_session.query(ProviderOrgConnection)
            .filter(
                ProviderOrgConnection.org_id == family["org"].id,
                ProviderOrgConnection.parent_id == family["parent"].id,
            )
            .one()
        )
        assert connection.connected_by_user_id == family["parent"].id

        # The whole point of the two-step flow: no specific calendar is
        # wired up yet - guessing "primary" here was exactly the wrong-
        # calendar dead end this design replaces. The parent still has to
        # pick one via GET .../calendars before adapter_for() can build
        # anything.
        org = db_session.query(ProviderOrg).filter(ProviderOrg.id == family["org"].id).first()
        assert org.calendar_account_id is None
        assert CalendarSyncService(db_session).adapter_for(org) is None

    def test_happy_path_but_a_second_family_still_sees_nothing(
        self, client, db_session, family, monkeypatch
    ):
        """Connecting Google for one family's use of an org must not leak to another."""
        self._mock_google(monkeypatch)
        state = create_calendar_connect_state(
            user_id=family["parent"].id, org_id=family["org"].id
        )
        client.get(
            "/calendar-sync/google/callback",
            params={"code": "abc123", "state": state},
            follow_redirects=False,
        )

        other_parent = User(
            email="other-parent3@example.com",
            username="other-parent3",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(other_parent)
        db_session.commit()

        response = client.get("/calendar-sync/orgs", headers=_auth(other_parent))
        assert response.json() == []


class TestGoogleAdapterFamilyScoping:
    """
    ProviderOrg is global (matched by name), so two unrelated families can
    both hold a ProviderOrgConnection on the very same org row. Before this
    was fixed, _google_adapter() picked whichever connected_by_user_id's
    token its query happened to find first - meaning a pull for one
    family could silently use another family's Google token.
    """

    def test_pull_uses_this_familys_token_not_another_familys(self, db_session, family):
        org = family["org"]
        org.calendar_account_id = "shared-calendar-id"
        db_session.commit()

        parent_a = family["parent"]
        db_session.add(
            OAuthProvider(
                user_id=parent_a.id, provider="google", provider_user_id="a", access_token="token-A"
            )
        )
        db_session.add(
            ProviderOrgConnection(org_id=org.id, parent_id=parent_a.id, connected_by_user_id=parent_a.id)
        )
        db_session.commit()

        parent_b = User(
            email="parent-b@example.com",
            username="parent-b",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(parent_b)
        db_session.commit()
        db_session.add(
            OAuthProvider(
                user_id=parent_b.id, provider="google", provider_user_id="b", access_token="token-B"
            )
        )
        db_session.add(
            ProviderOrgConnection(org_id=org.id, parent_id=parent_b.id, connected_by_user_id=parent_b.id)
        )
        db_session.commit()

        service = CalendarSyncService(db_session)
        adapter_for_b = service.adapter_for(org, parent_id=parent_b.id)
        assert adapter_for_b.access_token == "token-B"

        adapter_for_a = service.adapter_for(org, parent_id=parent_a.id)
        assert adapter_for_a.access_token == "token-A"

    async def test_pull_org_derives_the_scope_from_child_id_automatically(
        self, db_session, family, monkeypatch
    ):
        """A caller with no explicit parent_id (every real caller passes child_id
        already) still gets the right family's token, via the child's own
        parent_id - not just whichever token the query finds first."""
        org = family["org"]
        org.calendar_account_id = "shared-calendar-id"
        db_session.commit()

        parent_a = family["parent"]
        db_session.add(
            OAuthProvider(
                user_id=parent_a.id, provider="google", provider_user_id="a", access_token="token-A"
            )
        )
        db_session.add(
            ProviderOrgConnection(org_id=org.id, parent_id=parent_a.id, connected_by_user_id=parent_a.id)
        )
        db_session.commit()

        parent_b = User(
            email="parent-b2@example.com",
            username="parent-b2",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(parent_b)
        db_session.commit()
        kid_b = User(
            email="kid-b2@example.com",
            username="kid-b2",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_kid_account=True,
            parent_id=parent_b.id,
        )
        db_session.add(kid_b)
        db_session.commit()
        db_session.add(
            OAuthProvider(
                user_id=parent_b.id, provider="google", provider_user_id="b", access_token="token-B"
            )
        )
        db_session.add(
            ProviderOrgConnection(org_id=org.id, parent_id=parent_b.id, connected_by_user_id=parent_b.id)
        )
        db_session.commit()

        seen_tokens = []
        real_init = GoogleCalendarAdapter.__init__

        def capture_init(self, access_token, **kwargs):
            seen_tokens.append(access_token)
            return real_init(self, access_token, **kwargs)

        async def fake_list_events(self, start, end):
            return []

        monkeypatch.setattr(GoogleCalendarAdapter, "__init__", capture_init)
        monkeypatch.setattr(GoogleCalendarAdapter, "list_events", fake_list_events)

        await CalendarSyncService(db_session).pull_org(org, child_id=kid_b.id)

        assert seen_tokens == ["token-B"]


class TestListGoogleCalendars:
    def _connect(self, client, family, monkeypatch, email="parent@example.com"):
        TestGoogleCalendarConnectFlow()._mock_google(monkeypatch, email=email)
        state = create_calendar_connect_state(user_id=family["parent"].id, org_id=family["org"].id)
        client.get(
            "/calendar-sync/google/callback",
            params={"code": "abc123", "state": state},
            follow_redirects=False,
        )

    def _mock_calendar_list(self, monkeypatch, items=None, status_code=200):
        import app.routers.calendar_oauth as calendar_oauth

        payload = {"items": items if items is not None else []}

        def handler(request):
            return httpx.Response(status_code, json=payload)

        transport = httpx.MockTransport(handler)
        monkeypatch.setattr(
            calendar_oauth.httpx,
            "AsyncClient",
            lambda *args, **kwargs: _REAL_ASYNC_CLIENT(transport=transport),
        )

    def test_returns_the_parents_calendars_primary_first(self, client, family, monkeypatch):
        self._connect(client, family, monkeypatch)
        self._mock_calendar_list(
            monkeypatch,
            items=[
                {"id": "kid@group.calendar.google.com", "summary": "Ellie's Schedule"},
                {"id": "parent@example.com", "summary": "My Calendar", "primary": True},
            ],
        )

        response = client.get(
            "/calendar-sync/google/calendars",
            params={"org_id": family["org"].id},
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_200_OK
        calendars = response.json()["calendars"]
        assert calendars[0] == {"id": "parent@example.com", "summary": "My Calendar", "primary": True}
        assert calendars[1] == {
            "id": "kid@group.calendar.google.com",
            "summary": "Ellie's Schedule",
            "primary": False,
        }

    def test_404_when_no_google_connection_exists_yet(self, client, family):
        response = client.get(
            "/calendar-sync/google/calendars",
            params={"org_id": family["org"].id},
            headers=_auth(family["parent"]),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_another_family_cannot_list_this_familys_calendars(self, client, db_session, family, monkeypatch):
        self._connect(client, family, monkeypatch)
        self._mock_calendar_list(monkeypatch, items=[{"id": "a@b.com", "summary": "A"}])

        other_parent = User(
            email="other-parent4@example.com",
            username="other-parent4",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(other_parent)
        db_session.commit()

        response = client.get(
            "/calendar-sync/google/calendars",
            params={"org_id": family["org"].id},
            headers=_auth(other_parent),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_a_google_api_failure_is_a_502(self, client, family, monkeypatch):
        self._connect(client, family, monkeypatch)
        self._mock_calendar_list(monkeypatch, status_code=500)

        response = client.get(
            "/calendar-sync/google/calendars",
            params={"org_id": family["org"].id},
            headers=_auth(family["parent"]),
        )
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
