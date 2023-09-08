import re
from datetime import datetime

import pytz
from django.utils import timezone
from pydantic import BaseModel, Field, computed_field


class StravaTokenResponse(BaseModel):
    """Class to parse strava token responses."""

    access_token: str
    expires_at: int
    refresh_token: str

    @property
    def expires_at_datetime(self) -> datetime:
        """Get a datetime from the expires_at timestamp."""
        return timezone.make_aware(datetime.fromtimestamp(self.expires_at))


class StravaSession(BaseModel):
    """Class to parse strava sessions."""

    name: str = Field(exclude=True)
    type: str = Field(exclude=True)
    sport_type: str = Field(exclude=True)
    discipline_id: int | None = Field(default=None)
    start_date_local: str = Field(exclude=True)
    timezone: str = Field(exclude=True)
    total_duration: int = Field(..., alias="elapsed_time")
    moving_duration: int = Field(..., alias="moving_time")
    distance: float
    has_heartrate: bool = Field(exclude=True)
    average_hr: float | None = Field(default=None, alias="average_heartrate")
    max_hr: float | None = Field(default=None, alias="max_heartrate")
    average_speed: float
    max_speed: float
    strava_id: int = Field(..., alias="id")

    @computed_field
    @property
    def date(self) -> datetime:
        """Add date for converting to model."""
        return self.start_date

    @computed_field
    @property
    def start_date(self) -> datetime:
        """Get start_date as datetime from start_date_local string."""
        return timezone.make_aware(
            datetime.strptime(self.start_date_local, "%Y-%m-%dT%H:%M:%SZ")
        )

    @property
    def proper_timezone(self):
        """Convert IANA timezone to pytz timezone."""
        iana_timezone_identifier = re.search(
            r"\(([^)]+)\)\s+(.+)", self.timezone
        ).group(2)
        return pytz.timezone(iana_timezone_identifier)
