from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from scipy import constants


class Discipline(models.Model):
    """A discipline that can be practiced."""

    class SpeedType(models.TextChoices):
        KILOMETER_PER_HOUR = "KM", _("km/h")
        MIN_PER_100M = "MM", _("min/100m")
        MIN_PER_KM = "MK", _("min/km")

    name = models.CharField(max_length=200)
    speed_type = models.CharField(
        max_length=2,
        choices=SpeedType.choices,
        default=SpeedType.KILOMETER_PER_HOUR,
    )

    def __str__(self):
        """Return a string representation of the model."""
        return self.name


class TrainingType(models.Model):
    """A type of training."""

    name = models.CharField(max_length=200)

    def __str__(self):
        """Return a string representation of the model."""
        return self.name


class TrainingSession(models.Model):
    """A training session with all training data."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    date = models.DateField()
    start_date = models.DateTimeField(blank=True, null=True)
    moving_duration = models.IntegerField(blank=True, null=True)
    total_duration = models.IntegerField(blank=True, null=True)
    distance = models.FloatField(blank=True, null=True)
    training_type = models.ForeignKey(
        TrainingType, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    average_hr = models.FloatField(blank=True, null=True)
    max_hr = models.FloatField(blank=True, null=True)
    average_speed = models.FloatField(blank=True, null=True)
    max_speed = models.FloatField(blank=True, null=True)
    polyline = models.CharField(blank=True, null=True)
    summary_polyline = models.CharField(blank=True, null=True)
    strava_updated = models.DateTimeField(blank=True, null=True)
    strava_id = models.BigIntegerField(blank=True, null=True)
    excluded = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date"]

    @property
    def formatted_duration(self):
        """Format duration nicely."""
        if self.moving_duration:
            hours = int(self.moving_duration // constants.hour)
            minutes = int((self.moving_duration % constants.hour) // constants.minute)
            return f"{hours}h {minutes}m"
        else:
            return "N/A"

    @property
    def formatted_distance(self):
        """Format distance nicely"""
        if self.distance:
            return f"{self.distance / constants.kilo:.2f} km"
        else:
            return "N/A"

    @property
    def formatted_average_speed(self):
        """Format average speed based on the speed type of the discipline."""
        if self.average_speed is None:
            return "N/A"

        return self.formatted_speed(self.average_speed, self.discipline)

    @property
    def formatted_max_speed(self):
        """Format max speed based on the speed type of the discipline."""
        if self.average_speed is None:
            return "N/A"

        return self.formatted_speed(self.max_speed, self.discipline)

    @staticmethod
    def formatted_speed(speed, discipline, include_label=True):
        """Format speed based on the speed type of the discipline."""
        match discipline.speed_type:
            case Discipline.SpeedType.KILOMETER_PER_HOUR:
                return (
                    f"{TrainingSession.convert_mps_to_kmph(speed):.1f}"
                    f"{' km/h' if include_label else ''}"
                )
            case Discipline.SpeedType.MIN_PER_100M:
                min_per_100m = (
                    TrainingSession.convert_meters_per_second_to_minutes_per_100m(speed)
                )
                return (
                    f"{int(min_per_100m)}:"
                    f"{(min_per_100m % 1) * constants.minute :02.0f}"
                    f"{' min/100m' if include_label else ''}"
                )
            case Discipline.SpeedType.MIN_PER_KM:
                min_per_km = (
                    TrainingSession.convert_meters_per_second_to_minutes_per_km(speed)
                )
                return (
                    f"{int(min_per_km)}:{(min_per_km % 1) * constants.minute :02.0f}"
                    f"{' min/km' if include_label else ''}"
                )

    @staticmethod
    def convert_meters_per_second_to_minutes_per_km(meters_per_second: float):
        """Convert meters per second to minutes per km."""
        if not meters_per_second:
            return 0

        return (1 / meters_per_second) * constants.kilo / constants.minute

    @staticmethod
    def convert_meters_per_second_to_minutes_per_100m(meters_per_second: float):
        """Convert meters per second to minutes per 100m."""
        if not meters_per_second:
            return 0

        return (1 / meters_per_second) * constants.hecto / constants.minute

    @staticmethod
    def convert_mps_to_kmph(meters_per_second: float):
        """Convert meters per second to km per hour."""
        return meters_per_second / constants.kilo * constants.hour

    @property
    def strava_link(self):
        return f"https://www" f".strava.com/activities/{self.strava_id}"

    def __str__(self):
        """Return a string representation of the model."""
        return (
            f"{self.user.username.capitalize()} did "
            f"{self.discipline} on {self.date} "
            f"({self.formatted_distance} in {self.formatted_duration})"
        )


class SessionZones(models.Model):
    """The zones of a training session."""

    class ZoneType(models.TextChoices):
        HEART_RATE = "HR", _("Heart rate")
        POWER = "PW", _("Power")
        PACE = "PC", _("Pace")

    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE)
    resource_state = models.IntegerField(blank=True, null=True)
    points = models.FloatField(blank=True, null=True)
    sensor_based = models.BooleanField(default=True)
    zone_type = models.CharField(
        max_length=2,
        choices=ZoneType.choices,
    )
    score = models.IntegerField(blank=True, null=True)
    custom_zones = models.BooleanField(blank=True, null=True)

    def zones_data(self):
        """Creates zones data with proper labels."""
        labels = []
        values = []
        for zone in self.zone_set.all():
            if self.zone_type == self.ZoneType.PACE:
                if zone.max != -1:
                    min_pace = TrainingSession.formatted_speed(
                        zone.min, self.session.discipline, include_label=False
                    )
                    max_pace = TrainingSession.formatted_speed(
                        zone.max, self.session.discipline, include_label=False
                    )
                    labels.append(f"{min_pace} - " f"{max_pace}")
                else:
                    min_pace = TrainingSession.formatted_speed(
                        zone.min, self.session.discipline, include_label=False
                    )
                    labels.append(f"< {min_pace}")

            else:
                if zone.max != -1:
                    labels.append(f"{zone.min : .0f} - {zone.max: .0f}")
                else:
                    labels.append(f"> {zone.min : .1f}")
            values.append(zone.time / constants.minute)
        return {"labels": labels, "values": values}

    def __str__(self):
        """Return a string representation of the model."""
        return f"{ str(self.get_zone_type_display()) } zones for session {self.session}"


class Zone(models.Model):
    """A zone of a training session."""

    min = models.FloatField()
    max = models.FloatField()
    time = models.IntegerField()
    session_zones = models.ForeignKey(SessionZones, on_delete=models.CASCADE)

    def __str__(self):
        """Return a string representation of the model."""
        return (
            f"{int(self.time / int(constants.minute))} minutes "
            f"in {self.min} - {self.max}"
        )


class MunicipalityVisits(models.Model):
    """A municipality visited by a user."""

    municipality = models.CharField()
    training_session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE)

    def __str__(self):
        """Return a string representation of the model."""
        return (
            f"{self.training_session.user.username.capitalize()} visited {self.municipality} - "
            f"{self.training_session.discipline} on {self.training_session.date} "
        )
