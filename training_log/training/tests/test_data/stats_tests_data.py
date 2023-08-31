from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from training.models import Discipline, TrainingSession


class StatsTestData:
    def __init__(self):
        self.test_user = "testuser"
        self.date = datetime.today() - timedelta(days=1)
        self.start_date = timezone.make_aware(self.date + timedelta(hours=12))

        # Stats values
        self.total_time_trained = None
        self.weekly_time_trained = None

    def create_discipline(self, name="test"):
        return Discipline.objects.create(name=name)

    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return User.objects.create(username=username)

    def get_discipline(self, discipline_name):
        try:
            return Discipline.objects.get(name=discipline_name)
        except Discipline.DoesNotExist:
            return Discipline.objects.create(name=discipline_name)

    def create_session(
        self,
        username=None,
        discipline="test",
        date="2023-08-23",
        start_date=None,
        distance=100,
        moving_duration=3600,
        total_duration=4000,
    ):
        if username is None:
            username = self.test_user

        return TrainingSession.objects.create(
            user=self.get_user(username),
            discipline=self.get_discipline(discipline),
            date=date,
            start_date=start_date,
            distance=distance,
            moving_duration=moving_duration,
            total_duration=total_duration,
        )

    def load_regular_data(self):
        days_back = 2
        self.create_session(
            discipline="Swimming",
            date=self.date - timedelta(days=days_back),
            start_date=self.start_date - timedelta(days=days_back),
            moving_duration=3500,
            total_duration=3700,
            distance=1500,
        )

        days_back = 1
        self.create_session(
            discipline="Swimming",
            date=self.date - timedelta(days=days_back),
            start_date=self.start_date - timedelta(days=days_back),
            moving_duration=3600,
            total_duration=4000,
            distance=2000,
        )

        days_back = 7
        self.create_session(
            discipline="Running",
            date=self.date - timedelta(days=days_back),
            start_date=self.start_date - timedelta(days=days_back),
            moving_duration=4200,
            total_duration=4400,
            distance=None,
        )

        days_back = 20
        self.create_session(
            discipline="Running",
            date=self.date - timedelta(days=days_back),
            start_date=self.start_date - timedelta(days=days_back),
            moving_duration=7200,
            total_duration=8000,
            distance=21000,
        )

        days_back = 30
        self.create_session(
            discipline="Cycling",
            date=self.date - timedelta(days=days_back),
            start_date=self.start_date - timedelta(days=days_back),
            moving_duration=1800,
            total_duration=2000,
            distance=4000,
        )

        days_back = 8
        self.create_session(
            discipline="Running",
            date=self.date - timedelta(days=days_back),
            start_date=self.start_date - timedelta(days=days_back),
            moving_duration=None,
            total_duration=None,
            distance=None,
        )

        days_back = 15
        self.create_session(
            username="testuser_2",
            discipline="Running",
            date=self.date - timedelta(days=days_back),
            start_date=self.start_date - timedelta(days=days_back),
            moving_duration=1850,
            total_duration=2050,
            distance=4000,
        )

        days_back = 40
        self.create_session(
            username="testuser_2",
            discipline="Swimming",
            date=self.date - timedelta(days=days_back),
            start_date=self.start_date - timedelta(days=days_back),
            moving_duration=18000,
            total_duration=21000,
            distance=5000,
        )

        self.total_time_trained = 20280
        self.time_since_last_session = (
            timezone.now()
            - (self.start_date - timedelta(days=1) + timedelta(seconds=4000))
        ).total_seconds()

        self.number_of_swims = 2
        self.number_of_runs = 3
        self.number_of_rides = 1

        self.total_swimming_time = 7080
        self.total_running_time = 11400
        self.total_cycling_time = 1800

        self.longest_swim_time = 3600
        self.longest_run_time = 7200
        self.longest_ride_time = 1800

        self.longest_swim_distance = 2000
        self.longest_run_distance = 21000
        self.longest_ride_distance = 4000
