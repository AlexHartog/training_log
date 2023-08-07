from datetime import datetime
from django.utils import timezone


def get_timezone_aware_dt(dt) -> datetime:
    return timezone.make_aware(dt, timezone.get_current_timezone())
