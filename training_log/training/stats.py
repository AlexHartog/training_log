from datetime import datetime, timedelta
from enum import Enum
import pandas as pd

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db.models import F, Q, Sum
from django.utils import timezone

from .models import TrainingSession

DEFAULT_START_DATE = datetime(2023, 5, 1)
LONG_SWIM_DURATION = 60
LONG_RIDE_DURATION = 180
LONG_RUN_DURATION = 90


class StatsPeriod(Enum):
    """This enum gives the different periods to calculate stats for."""

    WEEK = "week"
    MONTH = "month"
    THREE_MONTHS = "three_months"
    ALL = "all"

    @staticmethod
    def get_enum_from_string(value_str):
        """Try to find a StatsPeriod enum from a string.

        :param value_str: The string value

        """
        for member in StatsPeriod.__members__.values():
            if member.value == value_str:
                return member
        raise ValueError(
            f"No member found for '{value_str}' in enum {StatsPeriod.__name__}"
        )


class AllPlayerStats:
    """This class has overall statistics for all players."""

    def __init__(self, period: StatsPeriod = StatsPeriod.ALL):
        self.users = User.objects.all()
        self.players = [user.username.capitalize() for user in self.users]
        self.stats = {}
        self.training_sessions = []
        self.period = period
        self.start_date = None
        self.end_date = None
        self.get_start_end_dates()
        self.get_training_sessions()
        self.calculate_stats()

    def get_training_sessions(self):
        """Get the training sessions ot be used in the stats."""
        filter_condition = Q(date__gte=self.start_date)

        if self.end_date:
            filter_condition &= Q(date__lte=self.end_date)

        self.training_sessions = TrainingSession.objects.filter(filter_condition)

    def get_start_end_dates(self):
        """Get start and end dates based on the period."""
        self.end_date = None
        match self.period:
            case StatsPeriod.WEEK:
                self.start_date = datetime.now() - relativedelta(weeks=1)
            case StatsPeriod.MONTH:
                self.start_date = datetime.now() - relativedelta(months=1)
            case StatsPeriod.THREE_MONTHS:
                self.start_date = datetime.now() - relativedelta(months=3)
            case StatsPeriod.ALL:
                self.start_date = DEFAULT_START_DATE

    def add_stat(self, name, value):
        """Add a stat to the stats dictionary.

        :param name: Name of the stat
        :param value: Value of the stat

        """
        if name in self.stats:
            self.stats[name].append(value)
        else:
            self.stats[name] = [value]

    @staticmethod
    def formatted_duration(duration):
        """Format duration in nicer format

        :param duration: The duration in seconds

        """
        if duration is None:
            return "N/A"

        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        return f"{hours}h {minutes}m"

    @staticmethod
    def formatted_distance(distance):
        """Format distance in a nicer format

        :param distance: The distance in meters

        """
        if distance is None:
            return "N/A"

        return f"{distance/1000:.2f} km"

    def get_sum(self, field, player, discipline=None):
        """Get the sum of a field for a player and optional discipline.

        :param field: The field we want the sum
        :param player: The player we want to filter on
        :param discipline: The discipline we want to filter on,
        optional (Default value = None)
        :returns: The sum of field for the filtered data

        """
        if discipline:
            return self.training_sessions.filter(
                user=player, discipline__name=discipline
            ).aggregate(Sum(field))[field + "__sum"]
        else:
            return self.training_sessions.filter(user=player).aggregate(Sum(field))[
                field + "__sum"
            ]

    def count_sessions(self, user, discipline=None, min_duration=None):
        """Count the number of sessions for a user. Optional to filter on
        discipline and min_duration.

        :param user: The user to count for
        :param min_duration: The minimum duration of the sessions (in minutes)
        (Default value = None)
        :param discipline: The discipline to filter on (Default value = None)
        :returns: The number of sessions for the filtered data

        """
        filtered_sessions = self.training_sessions.filter(user=user)
        if discipline:
            filtered_sessions = filtered_sessions.filter(discipline__name=discipline)

        if min_duration:
            filtered_sessions = filtered_sessions.filter(
                moving_duration__gte=min_duration * 60
            )

        return filtered_sessions.count()

    def longest_session(self, user, discipline, field):
        """Find the longest value for a field for a user and discipline.

        :param user: The user to filter on
        :param field: The field we want to find
        :param discipline: The discipline we want to filter on
        :returns: The maximum value for the field for the filtered data

        """
        longest_session = (
            self.training_sessions.filter(user=user, discipline__name=discipline)
            .exclude(**{field: None})
            .order_by(field)
            .reverse()
            .first()
        )

        if longest_session is None:
            return None

        return getattr(longest_session, field)

    def calculate_weekly_hours(self, user):
        """Calculate the weekly hours for a user.

        :param user: The user to filter on
        :returns: The weekly hours

        """
        total_time = self.get_sum("moving_duration", user)
        weeks_trained = ((self.end_date or datetime.now()) - self.start_date).days / 7

        return (total_time or 0) / weeks_trained

    def time_since_last_training(self, user):
        """Calculate the time since the last training ended for a user.

        :param user: The user to filter on

        """
        last_training = (
            self.training_sessions.filter(user=user)
            .order_by(F("start_date").desc(nulls_last=True))
            .first()
        )
        if last_training and last_training.start_date:
            end_time = last_training.start_date + timedelta(
                seconds=last_training.total_duration or 0
            )
            return self.format_timedelta(timezone.localtime(timezone.now()) - end_time)
        else:
            return None

    def get_rides_with_end_date(self, user):
        """Get all rides for a user as a dataframe. Filter out null start dates, calculate
        end date sort by the end date."""
        rides = (
            self.training_sessions.filter(user=user)
            .filter(discipline__name="Cycling")
            .filter(start_date__isnull=False)
            .all()
        )

        if len(rides) == 0:
            return None

        rides_df = pd.DataFrame.from_records(rides.values())

        rides_df["end_date"] = rides_df["start_date"] + pd.to_timedelta(
            rides_df["total_duration"], unit="s"
        )
        rides_df.sort_values("end_date", inplace=True)
        rides_df = rides_df.add_suffix("_ride")
        return rides_df

    def get_runs_df(self, user):
        """Get all runs for a user as a dataframe. Filter out null start dates
        and sort by start date."""
        runs = (
            self.training_sessions.filter(user=user)
            .filter(discipline__name="Running")
            .filter(start_date__isnull=False)
            .all()
        )

        if len(runs) == 0:
            return None

        runs_df = pd.DataFrame.from_records(runs.values())
        runs_df.sort_values("start_date", inplace=True)
        runs_df = runs_df.add_suffix("_run")
        return runs_df

    def count_brick_sessions(self, user):
        """Count the number of brick sessions done by the user.

        :param user: The user to filter on

        """
        rides = self.get_rides_with_end_date(user)
        runs = self.get_runs_df(user)

        if rides is None or runs is None:
            return 0

        results = pd.merge_asof(
            rides,
            runs,
            left_on="end_date_ride",
            right_on="start_date_run",
            direction="forward",
        )

        results["time_between"] = (
            results["start_date_run"] - results["end_date_ride"]
        ).dt.total_seconds() / 60

        results = results.loc[results["time_between"] <= 30]

        return len(results.index)

    @staticmethod
    def format_timedelta(delta):
        """Format timedelta in a nice format

        :param delta: The timedelta

        """
        days = delta.days
        seconds = delta.seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        formatted_string = f"{days}d " if days > 0 else ""
        formatted_string += f"{hours}h " if hours > 0 or days > 0 else ""
        formatted_string += f"{minutes}m"

        return formatted_string

    def calculate_stats(self):
        """Calculate the stats for all players."""
        for user in self.users:
            self.add_stat(
                "Time since last training", self.time_since_last_training(user)
            )
            self.add_stat(
                "Total time trained",
                self.formatted_duration(self.get_sum("moving_duration", user)),
            )
            self.add_stat(
                "Average weekly hours",
                self.formatted_duration(self.calculate_weekly_hours(user)),
            )
            self.add_stat("Number of swims", self.count_sessions(user, "Swimming"))
            self.add_stat("Number of rides", self.count_sessions(user, "Cycling"))
            self.add_stat("Number of runs", self.count_sessions(user, "Running"))
            self.add_stat("Number of brick workouts", self.count_brick_sessions(user))
            self.add_stat(
                "Total swimming time",
                self.formatted_duration(
                    self.get_sum("moving_duration", user, "Swimming")
                ),
            )
            self.add_stat(
                "Total cycling time",
                self.formatted_duration(
                    self.get_sum("moving_duration", user, "Cycling")
                ),
            )
            self.add_stat(
                "Total running time",
                self.formatted_duration(
                    self.get_sum("moving_duration", user, "Running")
                ),
            )
            self.add_stat(
                "Longest swim (time)",
                self.formatted_duration(
                    self.longest_session(user, "Swimming", "moving_duration")
                ),
            )
            self.add_stat(
                "Longest ride (time)",
                self.formatted_duration(
                    self.longest_session(user, "Cycling", "moving_duration")
                ),
            )
            self.add_stat(
                "Longest run (time)",
                self.formatted_duration(
                    self.longest_session(user, "Running", "moving_duration")
                ),
            )
            self.add_stat(
                "Longest swim (km)",
                self.formatted_distance(
                    self.longest_session(user, "Swimming", "distance")
                ),
            )
            self.add_stat(
                "Longest ride (km)",
                self.formatted_distance(
                    self.longest_session(user, "Cycling", "distance")
                ),
            )
            self.add_stat(
                "Longest run (km)",
                self.formatted_distance(
                    self.longest_session(user, "Running", "distance")
                ),
            )
            self.add_stat(
                "Long swims (>" + str(LONG_SWIM_DURATION) + " mins)",
                self.count_sessions(user, "Swimming", LONG_SWIM_DURATION),
            )
            self.add_stat(
                "Long rides (>" + str(LONG_RIDE_DURATION) + " mins)",
                self.count_sessions(user, "Cycling", LONG_RIDE_DURATION),
            )
            self.add_stat(
                "Long runs (>" + str(LONG_RUN_DURATION) + " mins)",
                self.count_sessions(user, "Running", LONG_RUN_DURATION),
            )
