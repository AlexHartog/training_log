import json
import os
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from training.models import Discipline, TrainingSession
from training.stats import AllPlayerStats, StatsPeriod, DEFAULT_START_DATE


class TrainingStatsTest(TestCase):
    def setUp(self):
        self.json_location = os.path.join(
            "training",
            "tests",
            "test_data",
        )

        self.defaults = {
            "username": "testuser",
            "discipline": "test_discipline",
            "date": "2023-08-23",
            "start_date": "2023-08-23 00:00:00",
        }

    def read_training_data(self, training_file):
        file_path = os.path.join(self.json_location, training_file)
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                self.load_training_data(json.load(file))
        except FileNotFoundError:
            print(f"File not found {file_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error - {e}")
            raise

    def load_training_data(self, data):
        for training in data:
            self.create_session_from_json(training)

    def get_discipline(self, session_data):
        discipline_name = (
            session_data["discipline"]
            if "discipline" in session_data.keys()
            else self.defaults["discipline"]
        )
        try:
            return Discipline.objects.get(name=discipline_name)
        except Discipline.DoesNotExist:
            return Discipline.objects.create(name=discipline_name)

    def get_value_or_default(self, session_date, name):
        if name in session_date.keys():
            return session_date[name]
        else:
            if name in self.defaults.keys():
                return self.defaults[name]

    def get_user(self, session_data):
        username = (
            session_data["username"]
            if "username" in session_data.keys()
            else self.defaults["username"]
        )

        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return User.objects.create(username=username)

    def get_start_date_local(self, session_data):
        if "start_date" in session_data.keys():
            start_date = session_data["start_date"]
        else:
            start_date = self.defaults["start_date"]

        return timezone.make_aware(datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ"))

    def create_session_from_json(self, session_data):
        session = TrainingSession.objects.create(
            user=self.get_user(session_data),
            discipline=self.get_discipline(session_data),
            date=self.get_value_or_default(session_data, "date"),
            start_date=self.get_start_date_local(session_data),
            moving_duration=self.get_value_or_default(session_data, "moving_duration"),
            total_duration=self.get_value_or_default(session_data, "total_duration"),
        )
        session.save()

    def test_total_time_trained(self):
        self.read_training_data("training_data.json")

        all_player_stats = AllPlayerStats(period=StatsPeriod.ALL)

        self.assertEqual(
            all_player_stats.stats["Total time trained"][0],
            all_player_stats.formatted_duration(19800),
        )

    def test_time_since_last_training(self):
        self.read_training_data("training_data.json")

        all_player_stats = AllPlayerStats(period=StatsPeriod.ALL)
        expected = all_player_stats.format_timedelta(
            timezone.localtime(timezone.now())
            - (
                timezone.make_aware(datetime(2023, 8, 25, 0, 0, 0))
                + timedelta(seconds=4000)
            )
        )

        self.assertEqual(
            all_player_stats.stats["Time since last training"][0], expected
        )

    def test_calculate_weekly_hours(self):
        self.read_training_data("training_data.json")

        all_player_stats = AllPlayerStats(period=StatsPeriod.ALL)

        total_time_trained = 19800
        weeks_trained = (datetime.now() - DEFAULT_START_DATE).days / 7

        expected = all_player_stats.formatted_duration(
            total_time_trained / weeks_trained
        )

        self.assertEqual(all_player_stats.stats["Average weekly hours"][0], expected)

    # Test correct period
    # Test every stat
    # Test with NaN
    # Test multiple users
    # Make sure that if date is NaN it will be excluded
