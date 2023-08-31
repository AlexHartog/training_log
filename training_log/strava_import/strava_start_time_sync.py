import requests
from django.contrib.auth.models import User

from training.models import TrainingSession

from . import strava_authentication
from .models import StravaAuth
from .schemas import StravaSession
from .strava import get_activities_url

SYNC_PAGE_COUNT = 200


def strava_start_time_sync():
    """Gets strava start times for all users."""
    print("Syncing")
    for strava_auth in StravaAuth.objects.all():
        if strava_auth.auto_import:
            print("Syncing start times for ", strava_auth.user)
            get_strava_start_time(strava_auth.user, SYNC_PAGE_COUNT)


def get_strava_start_time(user: User, result_per_page: int):
    """Request activities from strava and sync their start date."""
    strava_auth = strava_authentication.get_authentication(user)
    if not strava_auth:
        raise strava_authentication.NoAuthorizationException()

    headers = {"Authorization": f"Bearer {strava_auth.access_token}"}
    response = requests.get(get_activities_url(result_per_page), headers=headers)
    activities = response.json()

    if response.status_code != 200:
        print("Strava API returned error: ", response.json())
        return

    print("We've imported ", len(activities), " activities to update start time")

    for activity in activities:
        sync_start_time(user, activity)


def sync_start_time(user, activity):
    """Get the start time for a strava session and add it to a
    training session if found"""
    strava_session = StravaSession.model_validate(activity)

    training_session = TrainingSession.objects.filter(
        strava_id=strava_session.strava_id
    ).first()

    if not training_session:
        return

    print("Updating for training session ", training_session)
    training_session.start_date = strava_session.start_date
    training_session.save()
