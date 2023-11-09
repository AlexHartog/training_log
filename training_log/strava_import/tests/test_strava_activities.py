import json
import os
from datetime import datetime, timedelta

import responses
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from strava_import import strava
from strava_import.models import StravaAuth, StravaTypeMapping, StravaUser
from strava_import.strava_authentication import NoAuthorizationException
from training.models import Discipline, SessionZones, TrainingSession


class StravaAuthenticationTest(TestCase):
    expired_datetime = datetime.now() - timedelta(hours=1)
    not_expired_datetime = datetime.now() + timedelta(hours=1)

    def setUp(self):
        """Set up environment variables and other data."""
        os.environ["STRAVA_CLIENT_ID"] = "testclient"
        os.environ["STRAVA_CLIENT_SECRET"] = "testsecret"

        self.user = User.objects.create(username="testuser")
        self.results_per_page = 10
        self.strava_athlete_id = 17716848
        self.activity_ids = [10169464102, 10158708225, 10158408247]

        self.json_location = os.path.join(
            settings.BASE_DIR,
            "strava_import",
            "tests",
            "test_data",
        )

        self.create_disciplines()
        self.activities_sample = self.read_json_file("activities.json")
        self.zones_sample = self.read_json_file("zones.json")

    def create_strava_auth(
        self,
        scope=None,
        code="testcode",
        access_token="testtoken",
        access_token_expires_at=None,
        refresh_token="refreshtoken",
        user=None,
    ):
        """Create a strava authentication."""
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

    @staticmethod
    def create_disciplines():
        """Create default disciplines with strava mapping."""
        running_discipline = Discipline.objects.create(
            name="Running",
        )
        running_discipline.save()

        running_type_mapping = StravaTypeMapping.objects.create(
            strava_type="Run",
            discipline=running_discipline,
        )
        running_type_mapping.save()

        cycling_discipline = Discipline.objects.create(
            name="Cycling",
        )
        cycling_discipline.save()

        cycling_type_mapping = StravaTypeMapping.objects.create(
            strava_type="Ride",
            discipline=cycling_discipline,
        )
        cycling_type_mapping.save()

        swimming_discipline = Discipline.objects.create(
            name="Swimming",
        )
        swimming_discipline.save()

        swimming_type_mapping = StravaTypeMapping.objects.create(
            strava_type="Swim",
            discipline=swimming_discipline,
        )
        swimming_type_mapping.save()

    def read_json_file(self, file_name):
        """Read a json file with specified file name and default json location."""
        file_path = os.path.join(self.json_location, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"File not found {file_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error - {e}")
            raise

    def mock_get_activities_response(self):
        """Create a mock response for a successful activities request."""
        mock_response = self.activities_sample

        get_activities_url = strava.get_activities_url(self.results_per_page)

        responses.add(responses.GET, get_activities_url, json=mock_response, status=200)

    def mock_get_zones_response(self):
        """Create a mock response for a successful zones request."""
        mock_response = self.zones_sample

        for activity_id in self.activity_ids:
            get_zones_url = strava.get_activity_zones_url(activity_id)
            responses.add(responses.GET, get_zones_url, json=mock_response, status=200)

    def assert_line_in_logs(self, line, log):
        """Assert that a line was found in the log."""
        line_found = any(line in message for message in log.output)
        self.assertTrue(
            line_found,
            f'Line "{line}" wasn\'t found in the log messages',
        )

    def test_get_activities_url(self):
        """Test if the activities url is properly built."""
        activities_url = strava.get_activities_url(self.results_per_page)
        self.assertEqual(
            activities_url,
            f"https://www.strava.com/api/v3/athlete/activities?per_page={self.results_per_page}",
        )

    def test_get_activity_url(self):
        """Test if the activity url is properly built."""
        activity_id = 11
        activity_url = strava.get_activity_url(activity_id)
        self.assertEqual(
            activity_url,
            f"https://www.strava.com/api/v3/activities/{activity_id}",
        )

    def test_get_activity_zones_url(self):
        """Test if the activity zones url is properly built."""
        activity_id = 11
        zones_url = strava.get_activity_zones_url(activity_id)
        self.assertEqual(
            zones_url,
            f"https://www.strava.com/api/v3/activities/{activity_id}/zones",
        )

    def test_get_athlete_url(self):
        """Test if the athlete url is properly built."""
        athlete_url = strava.get_athlete_url()
        self.assertEqual(
            athlete_url,
            "https://www.strava.com/api/v3/athlete",
        )

    def test_get_activities_not_authenticated(self):
        """Test if a NoAuthorizationException is raised when not authorized."""
        with self.assertRaises(NoAuthorizationException):
            strava.get_activities(self.user, self.results_per_page)

    @responses.activate
    def test_get_activities(self):
        """Test if activities are properly imported."""
        self.mock_get_activities_response()
        self.create_strava_auth()
        strava.get_activities(self.user, self.results_per_page)

        training_sessions = TrainingSession.objects.all()

        self.assertEqual(training_sessions.count(), len(self.activities_sample))

    @responses.activate
    def test_import_zones(self):
        """Test if zones are properly imported for premium users."""
        self.mock_get_activities_response()
        self.mock_get_zones_response()
        self.create_strava_auth()
        StravaUser.objects.create(
            user=self.user, strava_id=self.strava_athlete_id, premium=True
        )

        strava.get_activities(self.user, self.results_per_page)

        training_session = TrainingSession.objects.get(
            user=self.user,
            strava_id=self.activity_ids[0],
        )
        zones = SessionZones.objects.get(session=training_session)
        self.assertIsNotNone(zones)

    @responses.activate
    def test_zone_import_non_premium(self):
        """Test if zones are not imported for non-premium users."""
        StravaUser.objects.create(user=self.user, strava_id=self.strava_athlete_id)

        with self.assertLogs(level="INFO") as log:
            strava.import_session_zones(self.activity_ids[0], self.user)
            self.assert_line_in_logs("does not have premium", log)
