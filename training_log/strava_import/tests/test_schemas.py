import json
import os
from datetime import datetime

import pytz
from django.test import TestCase
from django.utils import timezone
from strava_import.schemas import (
    AspectTypeEnum,
    ObjectTypeEnum,
    StravaEventData,
    StravaSession,
    StravaSessionZones,
)
from training.models import SessionZones


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


class StravaJSONReaderTest(TestCase):
    def setUp(self):
        """Set json location and empty list for zones"""
        self.json_location = os.path.join(
            "training_log",
            "strava_import",
            "tests",
            "test_data",
        )

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


class StravaZonesSchemaTest(StravaJSONReaderTest):
    def setUp(self):
        self.zones = []
        super().setUp()

    def read_zones_json(self):
        """Read strava_zones data from json file."""
        json_data = self.read_json_file("strava_zones.json")
        for zones in json_data:
            self.zones.append(StravaSessionZones.model_validate(zones))

    def test_session_zones_import(self):
        """Test imported data for the session zones object."""
        self.read_zones_json()
        self.assertEqual(len(self.zones), 3)
        self.assertEqual(self.zones[0].custom_zones, False)
        self.assertEqual(self.zones[0].resource_state, 3)
        self.assertEqual(self.zones[1].zone_type, SessionZones.ZoneType.PACE.value)

    def test_zones_import(self):
        """Test imported data for specific zones."""
        self.read_zones_json()
        first_zones = self.zones[0].zones
        self.assertEqual(len(first_zones), 5)
        self.assertEqual(first_zones[0].time, 2561)
        self.assertEqual(first_zones[1].max, 153)
        self.assertEqual(first_zones[2].min, 153)

    def test_convert_zones_to_session_zones(self):
        self.read_zones_json()

        session_zones = SessionZones(**self.zones[0].model_dump())

        self.assertEqual(session_zones.zone_type, SessionZones.ZoneType.HEART_RATE)


class StravaEventDataTest(StravaJSONReaderTest):
    def test_event_data_create(self):
        """Read event data create and check if data is correct."""
        json_data = self.read_json_file("event_data_create.json")
        event_data = StravaEventData.model_validate(json_data)

        expected = StravaEventData(
            object_type=ObjectTypeEnum.ACTIVITY,
            object_id=9841144171,
            aspect_type=AspectTypeEnum.CREATE,
            event_time=1694611869,
            updates={},
            owner_id=17716848,
            subscription_id=247939,
        )
        self.assertEqual(event_data, expected)

    def test_event_data_update(self):
        """Read event data update and check if data is correct."""
        json_data = self.read_json_file("event_data_update.json")
        event_data = StravaEventData.model_validate(json_data)

        expected = StravaEventData(
            object_type=ObjectTypeEnum.ACTIVITY,
            object_id=9834770609,
            aspect_type=AspectTypeEnum.UPDATE,
            event_time=1694607943,
            updates={"title": "New Title"},
            owner_id=17716848,
            subscription_id=247939,
        )
        self.assertEqual(event_data, expected)
