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

from app.database.models import OAuthProvider, ProviderOrg, ProviderOrgConnection, User
from app.services.calendar_sync_service import CalendarSyncService
from app.utils.auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_calendar_connect_state,
    get_password_hash,
)

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
        real_async_client = httpx.AsyncClient
        monkeypatch.setattr(
            calendar_oauth.httpx,
            "AsyncClient",
            lambda *args, **kwargs: real_async_client(transport=transport),
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
        assert response.headers["location"] == "/app/parent?tab=providers"

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

        # The whole point: CalendarSyncService can now actually find a
        # usable Google token for this org. Regression guard - the callback
        # used to store the token and the connection but never flip the org
        # itself onto the google provider, so adapter_for() had no way to
        # build an adapter and a connected org would never sync anything.
        org = db_session.query(ProviderOrg).filter(ProviderOrg.id == family["org"].id).first()
        assert org.calendar_provider == "google"
        assert org.calendar_account_id == "primary"
        adapter = CalendarSyncService(db_session).adapter_for(org)
        assert adapter is not None
        assert adapter.access_token == "g-access-1"

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
