from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User


class StravaAuth(models.Model):
    """A strava authentication saved for importing."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=200)
    access_token = models.CharField(max_length=200)
    scope = ArrayField(models.CharField(max_length=200, blank=True))

    def __str__(self):
        """Return a string representation of the model."""
        return f"{self.user.username.capitalize()} authorization"
