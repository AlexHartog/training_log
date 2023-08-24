from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from .schemas import StravaTokenResponse


class StravaAuth(models.Model):
    """A strava authentication saved for importing."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=200)
    access_token = models.CharField(max_length=200, blank=True)
    access_token_expires_at = models.DateTimeField(blank=True, null=True)
    refresh_token = models.CharField(max_length=200, blank=True)
    scope = ArrayField(models.CharField(max_length=200, blank=True))
    auto_import = models.BooleanField(default=False)

    def needs_authorization(self):
        """Return true if the user needs to authorize."""
        return not self.access_token

    def is_access_token_expired(self):
        """Return true if the access token is expired."""
        return self.access_token_expires_at < timezone.now()

    def has_valid_access_token(self):
        """Return true if the access token is valid."""
        return self.access_token and not self.is_access_token_expired()

    def update_token(self, token_response: StravaTokenResponse):
        """Update the token with the response from strava."""
        self.access_token = token_response.access_token
        self.refresh_token = token_response.refresh_token
        self.access_token_expires_at = token_response.expires_at_datetime
        self.save()

    def has_valid_scope(self):
        """Return true if the scope is valid."""
        return "activity:read" in self.scope

    def __str__(self):
        """Return a string representation of the model."""
        return (
            f"{self.user.username.capitalize()} "
            f"{'has' if self.has_valid_access_token() else 'does not have'} "
            f"valid access token"
        )


class StravaTypeMapping(models.Model):
    """A mapping between a strava activity type and a discipline."""

    strava_type = models.CharField(max_length=200)
    discipline = models.ForeignKey(
        "training.Discipline", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        """Return a string representation of the model."""
        return (
            f"{self.strava_type} ->"
            f" {self.discipline.name if self.discipline else 'None'}"
        )
