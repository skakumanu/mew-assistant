"""
What's left of app/routers/auth.py once sign-in itself moved to WorkOS
AuthKit: a "who am I" / profile-update pair, guarded by the same
get_current_user every other endpoint uses.
"""

from fastapi import status

from .conftest import _auth


class TestCurrentUserProfile:
    def test_get_returns_the_signed_in_users_profile(self, client, family):
        response = client.get("/auth/me", headers=_auth(family["parent"]))

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == family["parent"].email

    def test_get_requires_a_session(self, client):
        assert client.get("/auth/me").status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_rejects_an_invalid_token(self, client):
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_updates_profile_fields(self, client, family):
        response = client.patch(
            "/auth/me",
            json={
                "full_name": "Updated Name",
                "phone": "+15550001234",
                "timezone": "America/New_York",
            },
            headers=_auth(family["parent"]),
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["full_name"] == "Updated Name"
        assert body["phone"] == "+15550001234"
        assert body["timezone"] == "America/New_York"
