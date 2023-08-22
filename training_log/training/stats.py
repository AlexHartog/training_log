from datetime import datetime, timedelta
from enum import Enum

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
    WEEK = "week"
    MONTH = "month"
    ALL = "all"

    @staticmethod
    def get_enum_from_string(value_str):
        """Try to find a StatsPeriod enum from a string."""
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
        filter_condition = Q(date__gte=self.start_date)

        if self.end_date:
            filter_condition &= Q(date__lte=self.end_date)

        self.training_sessions = TrainingSession.objects.filter(filter_condition)

    def get_start_end_dates(self):
        match self.period:
            case StatsPeriod.WEEK:
                self.start_date = datetime.now() - relativedelta(weeks=1)
                self.end_date = None
            case StatsPeriod.MONTH:
                self.start_date = datetime.now() - relativedelta(months=1)
                self.end_date = None
            case StatsPeriod.ALL:
                self.start_date = DEFAULT_START_DATE
                self.end_date = None

    def add_stat(self, name, value):
        """Add a stat to the stats dictionary."""
        if name in self.stats:
            self.stats[name].append(value)
        else:
            self.stats[name] = [value]

    @staticmethod
    def formatted_duration(duration):
        """Return the duration as a nicely formatted string."""
        if duration is None:
            return "N/A"

        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        return f"{hours}h {minutes}m"

    @staticmethod
    def formatted_distance(distance):
        """Return the distance as a nicely formatted string."""
        if distance is None:
            return "N/A"

        return f"{distance/1000:.2f} km"

    def get_sum(self, field, player, discipline=None):
        """Return the sum of the given field for the given player.
        If discipline is given, only return the sum for that discipline."""
        if discipline:
            return self.training_sessions.filter(
                user=player, discipline__name=discipline
            ).aggregate(Sum(field))[field + "__sum"]
        else:
            return self.training_sessions.filter(user=player).aggregate(Sum(field))[
                field + "__sum"
            ]

    def count_sessions(self, user, discipline=None, min_duration=None):
        """Return the number of sessions for the given user. Optional discipline
        and min_duration (in minutes) can be used to filter the sessions."""
        filtered_sessions = self.training_sessions.filter(user=user)
        if discipline:
            filtered_sessions = filtered_sessions.filter(discipline__name=discipline)

        if min_duration:
            filtered_sessions = filtered_sessions.filter(
                total_duration__gte=min_duration * 60
            )

        return filtered_sessions.count()

    def longest_session(self, user, discipline, field):
        """Return the longest session for the given user and discipline. Field
        can be used to specify which field to return."""
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
        """Return the average weekly hours for the given user based on the time
        since TRAINING_START_DATE."""
        total_time = self.get_sum("total_duration", user)
        weeks_trained = ((self.end_date or datetime.now()) - self.start_date).days / 7

        return (total_time or 0) / weeks_trained

    def time_since_last_training(self, user):
        """Return the time since the last training for the given user."""
        last_training = (
            self.training_sessions.filter(user=user)
            .order_by(F("start_date").desc(nulls_last=True))
            .first()
        )
        if last_training:
            end_time = last_training.start_date + timedelta(
                seconds=last_training.total_duration
            )
            return self.format_timedelta(timezone.localtime(timezone.now()) - end_time)
        else:
            return None

    @staticmethod
    def format_timedelta(delta):
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
                self.formatted_duration(self.get_sum("total_duration", user)),
            )
            self.add_stat(
                "Average weekly hours",
                self.formatted_duration(self.calculate_weekly_hours(user)),
            )
            self.add_stat("Number of swims", self.count_sessions(user, "Swimming"))
            self.add_stat("Number of rides", self.count_sessions(user, "Cycling"))
            self.add_stat("Number of runs", self.count_sessions(user, "Running"))
            self.add_stat(
                "Total swimming time",
                self.formatted_duration(
                    self.get_sum("total_duration", user, "Swimming")
                ),
            )
            self.add_stat(
                "Total cycling time",
                self.formatted_duration(
                    self.get_sum("total_duration", user, "Cycling")
                ),
            )
            self.add_stat(
                "Total running time",
                self.formatted_duration(
                    self.get_sum("total_duration", user, "Running")
                ),
            )
            self.add_stat(
                "Longest swim (time)",
                self.formatted_duration(
                    self.longest_session(user, "Swimming", "total_duration")
                ),
            )
            self.add_stat(
                "Longest ride (time)",
                self.formatted_duration(
                    self.longest_session(user, "Cycling", "total_duration")
                ),
            )
            self.add_stat(
                "Longest run (time)",
                self.formatted_duration(
                    self.longest_session(user, "Running", "total_duration")
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
