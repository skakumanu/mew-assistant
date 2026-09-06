"""
Tests for pushing a kid's schedule into their own personal Google Calendar.

Push-only, one-way: Mew writes into a calendar the parent connected on the
kid's behalf, and never reads from it. The recurring theme, same as the
provider-calendar tests, is ownership: every test here that matters is
really asking "does this leak across families" or "does this authorize
against the calling parent, not just any child_id in the URL."
"""

from datetime import datetime

import httpx
import pytest
from fastapi import status
from jose import jwt

from app.database.models import (
    ChangeKind,
    KidCalendarConnection,
    OAuthProvider,
    ProviderOrgConnection,
    ScheduledSession,
    User,
)
from app.services.calendar_sync_service import CalendarSyncService
from app.services.change_request_service import ChangeRequestService
from app.utils.auth import (
    ALGORITHM,
    create_access_token,
    create_calendar_connect_state,
    get_password_hash,
)

from .conftest import _auth

_REAL_ASYNC_CLIENT = httpx.AsyncClient


class TestKidCalendarConnectFlow:
    def _mock_google(self, monkeypatch, email="parent@example.com"):
        import app.routers.kid_calendar_oauth as kid_calendar_oauth

        def handler(request):
            if request.url.path == "/token":
                return httpx.Response(
                    200,
                    json={
                        "access_token": "g-access-kid-1",
                        "refresh_token": "g-refresh-kid-1",
                        "expires_in": 3600,
                    },
                )
            return httpx.Response(200, json={"id": "google-sub-1", "email": email})

        transport = httpx.MockTransport(handler)
        monkeypatch.setattr(
            kid_calendar_oauth.httpx,
            "AsyncClient",
            lambda *args, **kwargs: _REAL_ASYNC_CLIENT(transport=transport),
        )

    def test_connect_redirects_to_google_with_a_signed_state(self, client, family):
        response = client.get(
            "/calendar-sync/google/kid/connect",
            params={"child_id": family["kid"].id},
            headers=_auth(family["parent"]),
            follow_redirects=False,
        )

        assert response.status_code in (302, 307)
        location = response.headers["location"]
        assert "accounts.google.com" in location
        assert "state=" in location

    def test_connect_for_a_child_that_is_not_the_callers_is_rejected(
        self, client, db_session, family
    ):
        other_parent = User(
            email="other-parent@example.com",
            username="other-parent",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(other_parent)
        db_session.commit()

        response = client.get(
            "/calendar-sync/google/kid/connect",
            params={"child_id": family["kid"].id},
            headers=_auth(other_parent),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_callback_rejects_a_tampered_state(self, client, family):
        forged = jwt.encode(
            {
                "user_id": family["parent"].id,
                "child_id": family["kid"].id,
                "type": "calendar_connect",
            },
            "wrong-secret",
            algorithm=ALGORITHM,
        )
        response = client.get(
            "/calendar-sync/google/kid/callback",
            params={"code": "abc123", "state": forged},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_callback_rejects_a_state_of_the_wrong_type(self, client, family):
        """An ordinary access token must not double as connect-flow state."""
        wrong_type_token = create_access_token({"sub": family["parent"].email})
        response = client.get(
            "/calendar-sync/google/kid/callback",
            params={"code": "abc123", "state": wrong_type_token},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_happy_path_stores_the_token_and_the_connection(
        self, client, db_session, family, monkeypatch
    ):
        self._mock_google(monkeypatch)
        state = create_calendar_connect_state(
            user_id=family["parent"].id, child_id=family["kid"].id
        )

        response = client.get(
            "/calendar-sync/google/kid/callback",
            params={"code": "abc123", "state": state},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["location"] == (
            f"/app/parent?tab=providers&choose_kid_calendar={family['kid'].id}"
        )

        link = (
            db_session.query(OAuthProvider)
            .filter(OAuthProvider.user_id == family["parent"].id, OAuthProvider.provider == "google")
            .one()
        )
        assert link.access_token == "g-access-kid-1"

        connection = (
            db_session.query(KidCalendarConnection)
            .filter(KidCalendarConnection.child_id == family["kid"].id)
            .one()
        )
        assert connection.parent_id == family["parent"].id
        assert connection.connected_by_user_id == family["parent"].id
        # Push-only: nothing was ever pulled or created from this call.
        assert connection.calendar_account_id is None

    def test_reconnecting_updates_the_same_row_never_a_second_one(
        self, client, db_session, family, monkeypatch
    ):
        self._mock_google(monkeypatch)
        for _ in range(2):
            state = create_calendar_connect_state(
                user_id=family["parent"].id, child_id=family["kid"].id
            )
            client.get(
                "/calendar-sync/google/kid/callback",
                params={"code": "abc123", "state": state},
                follow_redirects=False,
            )

        rows = (
            db_session.query(KidCalendarConnection)
            .filter(KidCalendarConnection.child_id == family["kid"].id)
            .all()
        )
        assert len(rows) == 1


class TestListKids:
    def test_lists_only_this_parents_kids(self, client, db_session, family):
        other_parent = User(
            email="other-parent2@example.com",
            username="other-parent2",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(other_parent)
        db_session.commit()

        response = client.get("/calendar-sync/google/kid/list", headers=_auth(family["parent"]))
        assert response.status_code == status.HTTP_200_OK
        names = [row["name"] for row in response.json()]
        assert names == ["Ellie"]

        other_response = client.get(
            "/calendar-sync/google/kid/list", headers=_auth(other_parent)
        )
        assert other_response.json() == []


class TestListKidCalendars:
    def _connect(self, client, family, monkeypatch):
        TestKidCalendarConnectFlow()._mock_google(monkeypatch)
        state = create_calendar_connect_state(
            user_id=family["parent"].id, child_id=family["kid"].id
        )
        client.get(
            "/calendar-sync/google/kid/callback",
            params={"code": "abc123", "state": state},
            follow_redirects=False,
        )

    def _mock_calendar_list(self, monkeypatch, items=None, status_code=200):
        import app.routers.kid_calendar_oauth as kid_calendar_oauth

        payload = {"items": items if items is not None else []}
        transport = httpx.MockTransport(lambda request: httpx.Response(status_code, json=payload))
        monkeypatch.setattr(
            kid_calendar_oauth.httpx,
            "AsyncClient",
            lambda *args, **kwargs: _REAL_ASYNC_CLIENT(transport=transport),
        )

    def test_returns_the_connected_accounts_writable_calendars(
        self, client, family, monkeypatch
    ):
        self._connect(client, family, monkeypatch)
        self._mock_calendar_list(
            monkeypatch,
            items=[{"id": "parent@example.com", "summary": "My Calendar", "primary": True}],
        )

        response = client.get(
            "/calendar-sync/google/kid/calendars",
            params={"child_id": family["kid"].id},
            headers=_auth(family["parent"]),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["calendars"][0]["id"] == "parent@example.com"

    def test_404_when_no_connection_exists_yet(self, client, family):
        response = client.get(
            "/calendar-sync/google/kid/calendars",
            params={"child_id": family["kid"].id},
            headers=_auth(family["parent"]),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_another_family_cannot_list_this_kids_calendars(
        self, client, db_session, family, monkeypatch
    ):
        self._connect(client, family, monkeypatch)

        other_parent = User(
            email="other-parent3@example.com",
            username="other-parent3",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(other_parent)
        db_session.commit()

        response = client.get(
            "/calendar-sync/google/kid/calendars",
            params={"child_id": family["kid"].id},
            headers=_auth(other_parent),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestConnectKidCalendarEndpoint:
    def test_a_parent_can_point_their_kids_push_target_at_a_calendar(self, client, family):
        response = client.put(
            f"/calendar-sync/kids/{family['kid'].id}/calendar",
            json={"calendar_provider": "google", "calendar_account_id": "kid@group.calendar.google.com"},
            headers=_auth(family["parent"]),
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body == {
            "child_id": family["kid"].id,
            "ok": True,
            "calendar_connected": True,
            "calendar_display_name": None,
        }

    def test_calendar_display_name_is_saved_and_returned(self, client, family):
        """
        A raw calendar id means nothing on the Providers tab - this is the
        human-readable name shown instead, so it must round-trip through
        both this save response and the kid/list endpoint the card renders
        from.
        """
        response = client.put(
            f"/calendar-sync/kids/{family['kid'].id}/calendar",
            json={
                "calendar_provider": "google",
                "calendar_account_id": "kid@group.calendar.google.com",
                "calendar_display_name": "Sindhu's Calendar",
            },
            headers=_auth(family["parent"]),
        )
        assert response.json()["calendar_display_name"] == "Sindhu's Calendar"

        listed = client.get("/calendar-sync/google/kid/list", headers=_auth(family["parent"])).json()
        assert listed[0]["calendar_display_name"] == "Sindhu's Calendar"

    def test_a_parent_cannot_point_another_familys_kid(self, client, db_session, family):
        other_parent = User(
            email="other-parent4@example.com",
            username="other-parent4",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(other_parent)
        db_session.commit()

        response = client.put(
            f"/calendar-sync/kids/{family['kid'].id}/calendar",
            json={"calendar_provider": "google", "calendar_account_id": "x"},
            headers=_auth(other_parent),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_only_google_is_accepted(self, client, family):
        response = client.put(
            f"/calendar-sync/kids/{family['kid'].id}/calendar",
            json={"calendar_provider": "ics", "calendar_account_id": "https://example.test/feed.ics"},
            headers=_auth(family["parent"]),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pointing_at_a_calendar_the_family_already_pulls_from_is_rejected(
        self, client, db_session, family
    ):
        """
        Regression guard for a real production incident: a kid's push
        target pointed at the same calendar a provider org pulls from,
        which fed a pull-creates-a-session/push-mirrors-it/pull-sees-the-
        mirror loop that duplicated a class in Google Calendar on every
        sync. This must be refused at the door, not merely survived.
        """
        org = family["org"]
        org.calendar_provider = "google"
        org.calendar_account_id = "shared@group.calendar.google.com"
        db_session.add(
            ProviderOrgConnection(
                org_id=org.id, parent_id=family["parent"].id, connected_by_user_id=family["parent"].id
            )
        )
        db_session.commit()

        response = client.put(
            f"/calendar-sync/kids/{family['kid'].id}/calendar",
            json={
                "calendar_provider": "google",
                "calendar_account_id": "shared@group.calendar.google.com",
            },
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            db_session.query(KidCalendarConnection)
            .filter(KidCalendarConnection.child_id == family["kid"].id)
            .first()
            is None
        )

    def test_resaving_the_same_calendar_to_the_same_kid_is_not_a_false_collision(
        self, client, family
    ):
        """The exclude-this-record check must not flag a record against itself."""
        payload = {
            "calendar_provider": "google",
            "calendar_account_id": "kid@group.calendar.google.com",
        }
        first = client.put(
            f"/calendar-sync/kids/{family['kid'].id}/calendar",
            json=payload,
            headers=_auth(family["parent"]),
        )
        second = client.put(
            f"/calendar-sync/kids/{family['kid'].id}/calendar",
            json=payload,
            headers=_auth(family["parent"]),
        )

        assert first.status_code == status.HTTP_200_OK
        assert second.status_code == status.HTTP_200_OK

    def test_another_familys_matching_calendar_does_not_block_this_one(
        self, client, db_session, family
    ):
        """The collision check is scoped per family, not global."""
        other_parent = User(
            email="other-parent5@example.com",
            username="other-parent5",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(other_parent)
        db_session.commit()
        other_kid = User(
            email="other-kid5@example.com",
            username="other-kid5",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_kid_account=True,
            parent_id=other_parent.id,
        )
        db_session.add(other_kid)
        db_session.commit()
        db_session.add(
            KidCalendarConnection(
                child_id=other_kid.id,
                parent_id=other_parent.id,
                calendar_provider="google",
                calendar_account_id="shared@group.calendar.google.com",
            )
        )
        db_session.commit()

        response = client.put(
            f"/calendar-sync/kids/{family['kid'].id}/calendar",
            json={
                "calendar_provider": "google",
                "calendar_account_id": "shared@group.calendar.google.com",
            },
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_200_OK


class TestPushToKidCalendar:
    def _connection(self, db_session, family):
        db_session.add(
            OAuthProvider(
                user_id=family["parent"].id,
                provider="google",
                provider_user_id="g-1",
                access_token="token",
            )
        )
        connection = KidCalendarConnection(
            child_id=family["kid"].id,
            parent_id=family["parent"].id,
            connected_by_user_id=family["parent"].id,
            calendar_provider="google",
            calendar_account_id="kid@group.calendar.google.com",
        )
        db_session.add(connection)
        db_session.commit()
        return connection

    def _patch_google(self, monkeypatch, handler):
        import app.services.calendar_sync_service as module

        real = module.GoogleCalendarAdapter

        def patched(*args, **kwargs):
            kwargs["client"] = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            return real(*args, **kwargs)

        monkeypatch.setattr(module, "GoogleCalendarAdapter", patched)

    @pytest.mark.asyncio
    async def test_no_connection_is_a_no_op(self, db_session, family):
        row = ScheduledSession(
            child_id=family["kid"].id,
            title="ABA session",
            activity_type="aba",
            start_utc=datetime(2026, 9, 10, 15, 30),
            duration_minutes=60,
            source="manual",
        )
        db_session.add(row)
        db_session.commit()

        assert await CalendarSyncService(db_session).push_to_kid_calendar(row, ChangeKind.MOVE) is False

    @pytest.mark.asyncio
    async def test_first_push_creates_and_stores_the_mirrored_event_id(
        self, db_session, family, monkeypatch
    ):
        self._connection(db_session, family)
        row = ScheduledSession(
            child_id=family["kid"].id,
            title="ABA session",
            activity_type="aba",
            start_utc=datetime(2026, 9, 10, 15, 30),
            duration_minutes=60,
            source="manual",
        )
        db_session.add(row)
        db_session.commit()

        seen = {}

        def handler(request):
            seen["method"] = request.method
            return httpx.Response(200, json={"id": "kid-evt-1"})

        self._patch_google(monkeypatch, handler)

        ok = await CalendarSyncService(db_session).push_to_kid_calendar(row, ChangeKind.MOVE)

        assert ok is True
        assert seen["method"] == "POST"
        assert row.kid_calendar_event_id == "kid-evt-1"

    @pytest.mark.asyncio
    async def test_a_second_push_updates_rather_than_recreates(
        self, db_session, family, monkeypatch
    ):
        self._connection(db_session, family)
        row = ScheduledSession(
            child_id=family["kid"].id,
            title="ABA session",
            activity_type="aba",
            start_utc=datetime(2026, 9, 10, 15, 30),
            duration_minutes=60,
            source="manual",
            kid_calendar_event_id="kid-evt-1",
        )
        db_session.add(row)
        db_session.commit()

        seen = {}

        def handler(request):
            seen["method"] = request.method
            return httpx.Response(200, json={})

        self._patch_google(monkeypatch, handler)

        ok = await CalendarSyncService(db_session).push_to_kid_calendar(row, ChangeKind.MOVE)

        assert ok is True
        assert seen["method"] == "PATCH"
        assert row.kid_calendar_event_id == "kid-evt-1"  # unchanged, not recreated

    @pytest.mark.asyncio
    async def test_a_cancel_with_no_id_ever_set_is_a_no_op(self, db_session, family, monkeypatch):
        self._connection(db_session, family)
        row = ScheduledSession(
            child_id=family["kid"].id,
            title="ABA session",
            activity_type="aba",
            start_utc=datetime(2026, 9, 10, 15, 30),
            duration_minutes=60,
            source="manual",
        )
        db_session.add(row)
        db_session.commit()

        assert await CalendarSyncService(db_session).push_to_kid_calendar(row, ChangeKind.CANCEL) is False

    @pytest.mark.asyncio
    async def test_a_cancel_deletes_and_clears_the_stored_id(self, db_session, family, monkeypatch):
        self._connection(db_session, family)
        row = ScheduledSession(
            child_id=family["kid"].id,
            title="ABA session",
            activity_type="aba",
            start_utc=datetime(2026, 9, 10, 15, 30),
            duration_minutes=60,
            source="manual",
            kid_calendar_event_id="kid-evt-1",
            is_cancelled=True,
        )
        db_session.add(row)
        db_session.commit()

        def handler(request):
            return httpx.Response(200, json={})

        self._patch_google(monkeypatch, handler)

        ok = await CalendarSyncService(db_session).push_to_kid_calendar(row, ChangeKind.CANCEL)

        assert ok is True
        assert row.kid_calendar_event_id is None


class TestWriteBackHooksAreIndependent:
    @pytest.mark.asyncio
    async def test_a_failing_provider_push_never_blocks_the_kid_push(
        self, db_session, family, monkeypatch
    ):
        """
        change_request_service's write-back calls push() and
        push_to_kid_calendar() independently - one raising must never stop
        the other from running.
        """
        self._connection = KidCalendarConnection(
            child_id=family["kid"].id,
            parent_id=family["parent"].id,
            connected_by_user_id=family["parent"].id,
            calendar_provider="google",
            calendar_account_id="kid@group.calendar.google.com",
        )
        db_session.add(
            OAuthProvider(
                user_id=family["parent"].id,
                provider="google",
                provider_user_id="g-1",
                access_token="token",
            )
        )
        db_session.add(self._connection)

        row = ScheduledSession(
            child_id=family["kid"].id,
            title="ABA session",
            activity_type="aba",
            start_utc=datetime(2026, 9, 10, 15, 30),
            duration_minutes=60,
            source="manual",
        )
        db_session.add(row)
        db_session.commit()

        from app.services.calendar_sync_service import CalendarSyncService

        async def boom(self, session, kind):
            raise RuntimeError("provider calendar is on fire")

        kid_push_called = {}

        async def fake_kid_push(self, session, kind):
            kid_push_called["yes"] = True
            return True

        monkeypatch.setattr(CalendarSyncService, "push", boom)
        monkeypatch.setattr(CalendarSyncService, "push_to_kid_calendar", fake_kid_push)

        await ChangeRequestService(db_session)._write_back_to_calendar(row, ChangeKind.MOVE)

        assert kid_push_called == {"yes": True}
