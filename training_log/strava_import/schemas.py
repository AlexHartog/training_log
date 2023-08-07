from datetime import datetime
from django.utils import timezone

from pydantic import BaseModel


class StravaTokenResponse(BaseModel):
    access_token: str
    expires_at: int
    refresh_token: str

    @property
    def expires_at_datetime(self) -> datetime:
        return timezone.make_aware(datetime.fromtimestamp(self.expires_at),
                                   timezone.get_current_timezone())

    # class Config:
    #     extra = "allow"


class StravaSession(BaseModel):
    name: str
    type: str
    sport_type: str
    start_date_local: str
    elapsed_time: int
    moving_time: int
    distance: float
    has_heartrate: bool
    average_heartrate: float | None = None
    max_heartrate: float | None = None
    average_speed: float
    max_speed: float
    id: int
