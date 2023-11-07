from datetime import datetime, timedelta

import responses
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from strava_import import strava_authentication
from strava_import.models import StravaAuth


class StravaAuthenticationTest(TestCase):
    expired_datetime = datetime.now() - timedelta(hours=1)
    not_expired_datetime = datetime.now() + timedelta(hours=1)

    def setUp(self):
        self.user = User.objects.create(username="testuser")

        # Data for token refreshes
        self.refreshed_expires_in = 20566
        self.refreshed_expires_at = timezone.make_aware(
            datetime.now().replace(microsecond=0)
            + timedelta(seconds=self.refreshed_expires_in)
        )
        self.refreshed_access_token = "a9b723"
        self.refreshed_refresh_token = "b5c569"

    def create_strava_auth(
        self,
        scope=None,
        code="testcode",
        access_token="testtoken",
        access_token_expires_at=None,
        refresh_token="refreshtoken",
        user=None,
    ):
        if scope is None:
            scope = ["read", "activity:read"]

        if access_token_expires_at is None:
            access_token_expires_at = self.not_expired_datetime

        if user is None:
            user = self.user

        return StravaAuth.objects.create(
            user=user,
            code=code,
            scope=scope,
            access_token=access_token,
            access_token_expires_at=timezone.make_aware(access_token_expires_at),
            refresh_token=refresh_token,
            auto_import=False,
        )

    def mock_successful_refresh_response(self):
        mock_response = {
            "token_type": "Bearer",
            "access_token": self.refreshed_access_token,
            "expires_at": int(self.refreshed_expires_at.timestamp()),
            "expires_in": self.refreshed_expires_in,
            "refresh_token": self.refreshed_refresh_token,
        }

        refresh_url = strava_authentication.ACCESS_TOKEN_URL

        responses.add(responses.POST, refresh_url, json=mock_response, status=200)

    def test_strava_user_not_authenticated(self):
        """We should get NOT_AUTHENTICATED when user has no Strava Auth."""
        result = strava_authentication.get_authentication_status(self.user)
        self.assertEqual(
            result, strava_authentication.AuthenticationStatus.NOT_AUTHENTICATED
        )

    def test_strava_no_user_authenticated(self):
        """We should get NOT_AUTHENTICATED when user is None."""
        result = strava_authentication.get_authentication_status(None)
        self.assertEqual(
            result, strava_authentication.AuthenticationStatus.NOT_AUTHENTICATED
        )

    def test_strava_user_authenticated(self):
        """We should get AUTHENTICATED when a user has a valid Strava Auth."""
        self.create_strava_auth()
        result = strava_authentication.get_authentication_status(self.user)
        self.assertEqual(
            result, strava_authentication.AuthenticationStatus.AUTHENTICATED
        )

    def test_strava_authentication_no_access_token(self):
        """We should get NOT_AUTHENTICATED when a user has no access token."""
        self.create_strava_auth(access_token="")
        result = strava_authentication.get_authentication_status(self.user)
        self.assertEqual(
            result, strava_authentication.AuthenticationStatus.NOT_AUTHENTICATED
        )

    def test_strava_authentication_token_expired(self):
        """We should get EXPIRED WHEN a user has an expired access token."""
        self.create_strava_auth(access_token_expires_at=self.expired_datetime)
        result = strava_authentication.get_authentication_status(self.user)
        self.assertEqual(result, strava_authentication.AuthenticationStatus.EXPIRED)

    def test_strava_needs_authorization_no_strava_auth(self):
        """We need authorization when user does not have a strava auth."""
        result = strava_authentication.needs_authorization(self.user)
        self.assertTrue(result)

    def test_strava_needs_authorization_no_access_token(self):
        """We need authorization when user does not have an access token."""
        self.create_strava_auth(access_token="")
        result = strava_authentication.needs_authorization(self.user)
        self.assertTrue(result)

    def test_strava_does_not_need_authorization(self):
        """We do not need authorization when user has an access token."""
        self.create_strava_auth(access_token="testtoken")
        result = strava_authentication.needs_authorization(self.user)
        self.assertFalse(result)

    @responses.activate
    def test_token_refresh(self):
        """Request a token refresh via Strava API and test if user auth is updated."""
        self.mock_successful_refresh_response()
        strava_auth = self.create_strava_auth()

        strava_authentication.refresh_token(strava_auth)

        self.assertEqual(strava_auth.access_token, "a9b723")
        self.assertEqual(strava_auth.refresh_token, "b5c569")
        self.assertEqual(strava_auth.access_token_expires_at, self.refreshed_expires_at)

    @responses.activate
    def test_refresh_token_if_not_expired(self):
        self.mock_successful_refresh_response()
        access_token = "not_refreshed"
        strava_auth = self.create_strava_auth(
            access_token_expires_at=self.not_expired_datetime, access_token=access_token
        )

        strava_authentication.refresh_token_if_expired(strava_auth)

        self.assertEqual(strava_auth.access_token, access_token)

    @responses.activate
    def test_refresh_token_if_expired(self):
        self.mock_successful_refresh_response()
        access_token = "not_refreshed"
        strava_auth = self.create_strava_auth(
            access_token_expires_at=self.expired_datetime, access_token=access_token
        )

        strava_authentication.refresh_token_if_expired(strava_auth)

        self.assertEqual(strava_auth.access_token, self.refreshed_access_token)
