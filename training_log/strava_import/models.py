from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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


class StravaActivityImport(models.Model):
    """A model for saving the json data from strava."""

    ACTIVITY = "activity"
    ACTIVITY_ZONES = "activity_zones"

    strava_id = models.BigIntegerField()
    type = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    json_data = models.JSONField()
    imported_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        """Return a string representation of the model."""
        return (
            f"{self.type.capitalize()} for "
            f"{self.user.username.capitalize() or 'no user'} with id {self.strava_id}"
        )


class StravaRateLimit(models.Model):
    """A model for saving the rate limit from strava."""

    SHORT_LIMIT_PLENTY = 20
    DAILY_LIMIT_PLENTY = 200

    short_limit = models.IntegerField()
    daily_limit = models.IntegerField()
    short_limit_usage = models.IntegerField()
    daily_limit_usage = models.IntegerField()
    updated_at = models.DateTimeField(auto_now_add=True)

    @property
    def remaining_short_limit(self):
        """Calculate the remaining short limit."""
        if self.is_same_quarter_hour(self.updated_at, timezone.now()):
            return self.short_limit - self.short_limit_usage
        else:
            return self.short_limit

    @staticmethod
    def is_same_quarter_hour(datetime_1: datetime, datetime_2: datetime):
        """Check if two datetimes are in the same quarter hour on the same day."""
        return (
            datetime_1.minute // 15 == datetime_2.minute // 15
            and datetime_1.hour == datetime_2.hour
            and datetime_1.date() == datetime_2.date()
        )

    @property
    def remaining_daily_limit(self):
        """Calculate the remaining daily limit."""
        if self.updated_at.date() == timezone.now().date():
            return self.daily_limit - self.daily_limit_usage
        else:
            return self.daily_limit

    def have_usage_remaining(self):
        """Check if we have any usage remaining."""
        return self.remaining_short_limit > 0 and self.remaining_daily_limit > 0

    def have_plenty_usage_remaining(self):
        """Check if we have plenty of usage remaining."""
        return (
            self.remaining_short_limit > self.SHORT_LIMIT_PLENTY
            and self.remaining_daily_limit > self.DAILY_LIMIT_PLENTY
        )

    def __str__(self):
        """Return a string representation of the model."""
        return (
            f"Short: {self.short_limit_usage}/{self.short_limit} - "
            f"{self.remaining_short_limit} left, "
            f"Daily: {self.daily_limit_usage}/{self.daily_limit} - "
            f"{self.remaining_daily_limit} left "
            f"at {self.updated_at}"
        )


class StravaSubscription(models.Model):
    """A model for saving the strava subscription."""

    class SubscriptionState(models.TextChoices):
        ACTIVE = "AC", _("Active")
        VALIDATED = "VA", _("Validated")
        CREATED = "CR", _("Created")

    enabled = models.BooleanField(default=False)
    callback_url = models.URLField(null=True, blank=True)
    verify_token = models.CharField(max_length=200, null=True, blank=True)
    state = models.CharField(
        max_length=2,
        choices=SubscriptionState.choices,
    )
    strava_id = models.BigIntegerField(null=True, blank=True)

    # TODO: How to check if still active?


class StravaUser(models.Model):
    """A model for saving strava user data."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    strava_id = models.BigIntegerField()
    username = models.CharField(max_length=200, null=True, blank=True)
    firstname = models.CharField(max_length=200, null=True, blank=True)
    lastname = models.CharField(max_length=200, null=True, blank=True)
    resource_state = models.IntegerField(null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)
    sex = models.CharField(max_length=200, null=True, blank=True)
    premium = models.BooleanField(null=True, blank=True)
    summit = models.BooleanField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)

    def __str__(self):
        """Return a string representation of the model."""
        return f"{self.strava_id} - {self.user.username.capitalize()}"
