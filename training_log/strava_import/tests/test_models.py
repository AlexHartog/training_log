from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from strava_import.models import StravaAuth, StravaTypeMapping
from strava_import.schemas import StravaTokenResponse
from training.models import Discipline


class StravaAuthTest(TestCase):
    expired_datetime = datetime.now() - timedelta(hours=1)
    not_expired_datetime = datetime.now() + timedelta(hours=1)

    def create_strava_auth(
        self,
        scope=None,
        code="testcode",
        access_token="testtoken",
        access_token_expires_at=None,
        refresh_token="refreshtoken",
    ):
        if scope is None:
            scope = ["read", "activity:read"]

        if access_token_expires_at is None:
            access_token_expires_at = self.not_expired_datetime

        return StravaAuth.objects.create(
            user=User.objects.create(username="testuser"),
            code=code,
            scope=scope,
            access_token=access_token,
            access_token_expires_at=timezone.make_aware(access_token_expires_at),
            refresh_token=refresh_token,
            auto_import=False,
        )

    def test_strava_auth_creation(self):
        """Create a strava auth object and check if it works."""
        strava_auth = self.create_strava_auth()
        self.assertTrue(isinstance(strava_auth, StravaAuth))

    def test_valid_scope(self):
        """Check if the scope is valid."""
        strava_auth = self.create_strava_auth(scope=["read", "activity:read"])
        self.assertTrue(strava_auth.has_valid_scope())

    def test_invalid_scope(self):
        """Check if scope is invalid."""
        strava_auth = self.create_strava_auth(scope=["read"])
        self.assertFalse(strava_auth.has_valid_scope())

    def test_expired_access_token(self):
        """Set an expired access token and test if it is expired."""
        strava_auth = self.create_strava_auth(
            access_token_expires_at=self.expired_datetime
        )
        self.assertTrue(strava_auth.is_access_token_expired())

    def test_not_expired_access_token(self):
        """Create a valid access token and test if it is not expired."""
        strava_auth = self.create_strava_auth(
            access_token_expires_at=self.not_expired_datetime
        )
        self.assertFalse(strava_auth.is_access_token_expired())

    def test_valid_access_token(self):
        """Create a valid access token and test if it is valid."""
        strava_auth = self.create_strava_auth(
            access_token="testtoken", access_token_expires_at=self.not_expired_datetime
        )
        self.assertTrue(strava_auth.has_valid_access_token())

    def test_invalid_access_token(self):
        """Create an invalid access token and test if it is invalid."""
        strava_auth = self.create_strava_auth(
            access_token="", access_token_expires_at=self.not_expired_datetime
        )
        self.assertFalse(strava_auth.has_valid_access_token())

    def test_needs_authorization(self):
        """Create a strava auth object with an empty access token and
        test if it needs authorization."""
        strava_auth = self.create_strava_auth(access_token="")
        self.assertTrue(strava_auth.needs_authorization())

    def test_does_not_need_authorization(self):
        """Create a strava auth object with a valid access token and
        test if it does not need authorization."""
        strava_auth = self.create_strava_auth(access_token="testtoken")
        self.assertFalse(strava_auth.needs_authorization())

    def test_update_token(self):
        """Update the token with the response from strava."""
        strava_auth = self.create_strava_auth()

        access_token = "refreshed_access_token"

        print("Timestamp: ", self.not_expired_datetime.timestamp())

        token_response = StravaTokenResponse(
            access_token=access_token,
            expires_at=int(self.not_expired_datetime.timestamp()),
            refresh_token="refreshtoken",
        )

        strava_auth.update_token(token_response)

        self.assertEqual(strava_auth.access_token, access_token)
        self.assertTrue(strava_auth.has_valid_access_token())

    def test_string(self):
        """Return a string representation of the model."""
        strava_auth = self.create_strava_auth(
            access_token="testtoken", access_token_expires_at=self.not_expired_datetime
        )
        self.assertIn(strava_auth.user.username.capitalize(), str(strava_auth))
        self.assertIn("has valid access token", str(strava_auth))


class StravaTypeMappingTest(TestCase):
    def create_strava_type_mapping(self, strava_type="testtype", discipline="test"):
        return StravaTypeMapping.objects.create(
            strava_type=strava_type,
            discipline=Discipline.objects.create(name=discipline),
        )

    def test_creation(self):
        """Create a strava type mapping and check if it works."""
        strava_type = "testtype"
        type_mapping = self.create_strava_type_mapping(strava_type=strava_type)

        self.assertTrue(isinstance(type_mapping, StravaTypeMapping))
        self.assertEqual(type_mapping.strava_type, strava_type)

    def test_string(self):
        """Create a strava type mapping and test if the string function is correct."""
        strava_type = "testtype"
        discipline = "test_discipline"

        type_mapping = self.create_strava_type_mapping(
            strava_type=strava_type, discipline=discipline
        )

        self.assertEqual(str(type_mapping), f"{strava_type} -> {discipline}")
