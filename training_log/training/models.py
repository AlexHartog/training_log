from django.contrib.auth.models import User
from django.db import models


class Discipline(models.Model):
    """A discipline that can be practiced."""

    name = models.CharField(max_length=200)

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
    strava_updated = models.DateTimeField(blank=True, null=True)
    strava_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        """ """

        ordering = ["-date"]

    @property
    def formatted_duration(self):
        """Format duration nicely."""
        if self.moving_duration:
            hours = self.moving_duration // 3600
            minutes = (self.moving_duration % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            return "N/A"

    @property
    def formatted_distance(self):
        """Format distance nicely"""
        if self.distance:
            return f"{self.distance/1000:.2f} km"
        else:
            return "N/A"

    def __str__(self):
        """Return a string representation of the model."""
        return (
            f"{self.user.username.capitalize()} did "
            f"{self.discipline} on {self.date} "
            f"({self.formatted_distance} in {self.formatted_duration})"
        )
