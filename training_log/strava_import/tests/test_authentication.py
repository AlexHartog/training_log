from datetime import datetime, timedelta

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
