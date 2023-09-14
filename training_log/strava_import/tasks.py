from huey import crontab
from huey.contrib.djhuey import periodic_task
from strava_import.strava import strava_sync


@periodic_task(crontab(minute="29"))
def strava_sync_task():
    strava_sync()
