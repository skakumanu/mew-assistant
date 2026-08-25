"""
The WorkOS AuthKit callback itself (app/routers/oauth_workos.py).

Everything downstream of a successful callback - the cookie, the `next`
safety, the setup-wizard redirect - is covered in
tests/test_onboarding_and_signin.py. What's tested here is the callback's
own logic: what it does with what WorkOS hands back, without a real
network round trip to WorkOS.
"""

from types import SimpleNamespace

from fastapi import status

from app.database.models import User, UserRole

from .conftest import _auth


class _FakeUserManagement:
    def __init__(self, response=None, exc=None):
        self._response = response
        self._exc = exc

    async def authenticate_with_code(self, *, code):
        if self._exc:
            raise self._exc
        return self._response


class _FakeWorkOSClient:
    def __init__(self, response=None, exc=None):
        self.user_management = _FakeUserManagement(response=response, exc=exc)


def _workos_response(email, email_verified=True, name="Pat Parent"):
    return SimpleNamespace(
        user=SimpleNamespace(email=email, email_verified=email_verified, name=name)
    )


def _patch_client(monkeypatch, fake_client):
    monkeypatch.setattr("app.routers.oauth_workos.get_workos_client", lambda: fake_client)


class TestWorkosCallback:
    def test_a_new_user_gets_an_account_a_cookie_and_the_wizard(
        self, client, db_session, monkeypatch
    ):
        _patch_client(
            monkeypatch, _FakeWorkOSClient(response=_workos_response("new.parent@example.com"))
        )

        response = client.get(
            "/auth/workos/callback",
            params={"code": "fake-code", "state": "/app/parent"},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        # A brand-new account has no child yet, so the wizard wins over
        # whatever `next` originally asked for.
        assert response.headers["location"] == "/app/setup"
        assert "mew_session" in response.cookies

        created = db_session.query(User).filter(User.email == "new.parent@example.com").one()
        assert created.role == UserRole.PARENT
        assert created.full_name == "Pat Parent"

    def test_an_existing_user_is_matched_by_email_and_sent_to_the_dashboard(
        self, client, db_session, monkeypatch, family
    ):
        _patch_client(
            monkeypatch,
            _FakeWorkOSClient(response=_workos_response(family["parent"].email)),
        )

        response = client.get(
            "/auth/workos/callback",
            params={"code": "fake-code", "state": "/app/parent"},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["location"] == "/app/parent"
        assert "mew_session" in response.cookies
        # No duplicate account was created for the matched email.
        assert (
            db_session.query(User).filter(User.email == family["parent"].email).count() == 1
        )

    def test_an_unverified_email_is_rejected(self, client, monkeypatch, db_session):
        _patch_client(
            monkeypatch,
            _FakeWorkOSClient(
                response=_workos_response("sneaky@example.com", email_verified=False)
            ),
        )

        response = client.get(
            "/auth/workos/callback",
            params={"code": "fake-code", "state": "/app/parent"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert db_session.query(User).filter(User.email == "sneaky@example.com").first() is None

    def test_a_workos_error_bounces_back_to_sign_in_with_no_cookie_set(self, client):
        response = client.get(
            "/auth/workos/callback",
            params={"error": "access_denied", "state": "/app/parent"},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["location"] == "/app/sign-in?error=1"
        assert "mew_session" not in response.cookies

    def test_a_missing_code_also_bounces_back_to_sign_in(self, client):
        response = client.get("/auth/workos/callback", follow_redirects=False)

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["location"] == "/app/sign-in?error=1"
        assert "mew_session" not in response.cookies

    def test_a_failed_code_exchange_bounces_back_without_raising(self, client, monkeypatch):
        _patch_client(monkeypatch, _FakeWorkOSClient(exc=RuntimeError("WorkOS is down")))

        response = client.get(
            "/auth/workos/callback",
            params={"code": "fake-code", "state": "/app/parent"},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["location"] == "/app/sign-in?error=1"
        assert "mew_session" not in response.cookies

    def test_the_cookie_the_callback_sets_actually_authenticates_later_calls(
        self, client, db_session, monkeypatch, family
    ):
        """Regression guard: a cookie that looks right but that
        get_current_user can't actually resolve is worse than no cookie -
        the earlier Google-OAuth cookie bug this session was exactly this
        shape."""
        _patch_client(
            monkeypatch,
            _FakeWorkOSClient(response=_workos_response(family["parent"].email)),
        )

        client.get(
            "/auth/workos/callback",
            params={"code": "fake-code", "state": "/app/parent"},
        )

        response = client.get("/rules")

        assert response.status_code == status.HTTP_200_OK

    def test_a_bearer_header_still_works_independently_of_the_callback(self, client, family):
        """Sanity check that the callback isn't the only way in - API
        clients using a bearer token are unaffected by this migration."""
        response = client.get("/rules", headers=_auth(family["parent"]))

        assert response.status_code == status.HTTP_200_OK
