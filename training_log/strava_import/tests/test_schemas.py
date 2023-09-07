from datetime import datetime

import pytz
from django.test import TestCase
from django.utils import timezone
from strava_import.schemas import StravaSession


class StravaSessionTest(TestCase):
    start_date_local_format = "%Y-%m-%dT%H:%M:%SZ"

    def create_strava_session(
        self, start_date_local=None, timezone="(GMT+01:00) Europe/Amsterdam"
    ):
        if start_date_local is None:
            start_date_local = datetime.now().strftime(self.start_date_local_format)

        return StravaSession(
            name="test",
            type="test",
            sport_type="test",
            start_date_local=start_date_local,
            timezone=timezone,
            elapsed_time=60,
            moving_time=60,
            distance=100,
            has_heartrate=True,
            average_heartrate=100,
            max_heartrate=100,
            average_speed=100,
            max_speed=100,
            id=1,
        )

    def test_date(self):
        """Create a strava session and test if the date property is correct.
        Remove the microseconds for comparison, because Strava Session does
        not have those.
        """
        start_datetime = datetime.now()

        strava_session = self.create_strava_session(
            start_date_local=start_datetime.strftime(self.start_date_local_format)
        )

        self.assertEqual(
            strava_session.date.replace(microsecond=0),
            timezone.make_aware(start_datetime.replace(microsecond=0)),
        )

    def test_proper_timezone(self):
        """Create a strava session and test if the proper timezone is set."""
        strava_session = self.create_strava_session(
            timezone="(GMT+01:00) Europe/Amsterdam"
        )
        self.assertEqual(
            strava_session.proper_timezone, pytz.timezone("Europe/Amsterdam")
        )
