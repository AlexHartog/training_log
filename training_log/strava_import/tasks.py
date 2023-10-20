from huey import crontab
from huey.contrib.djhuey import periodic_task

from strava_import.strava import strava_sync


@periodic_task(crontab(hour="3"))
def strava_sync_task():
    strava_sync()
