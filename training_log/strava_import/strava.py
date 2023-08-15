import requests
import os
from dotenv import dotenv_values

from django.conf import settings
from django.contrib.auth.models import User

from .models import StravaTypeMapping, StravaAuth
from .schemas import StravaSession
from . import strava_authentication
from training.models import TrainingSession

config = dotenv_values(os.path.join(settings.BASE_DIR, ".env"))


# TODO: Where to keep these constants?
ACTIVITIES_URL = (
    "https://www.strava.com/api/v3/athlete/" "activities?per_page={per_page}"
)
SYNC_PAGE_COUNT = 5


def strava_sync():
    """Syncs activities for all users with auto import enabled."""
    print("Syncing")
    for strava_auth in StravaAuth.objects.all():
        if strava_auth.auto_import:
            print("Running auto import for ", strava_auth.user)
            get_activities(strava_auth.user, SYNC_PAGE_COUNT)


def get_activities_url(result_per_page: int):
    """Builds the url to get activities from strava."""
    return ACTIVITIES_URL.format(per_page=result_per_page)


def get_activities(user: User, result_per_page: int):
    """Request activities from strava and import them into the database."""
    strava_auth = strava_authentication.get_authentication(user)
    if not strava_auth:
        raise strava_authentication.NoAuthorizationException()

    headers = {"Authorization": f"Bearer {strava_auth.access_token}"}
    response = requests.get(get_activities_url(result_per_page), headers=headers)
    activities = response.json()

    if response.status_code != 200:
        print("Strava API returned error: ", response.json())
        return

    print("We've imported ", len(activities), " activities")

    imported_sessions = []
    for activity in activities:
        new_session = import_activity(activity, user=strava_auth.user)
        if new_session:
            imported_sessions.append(new_session)

    return imported_sessions


def get_discipline(activity):
    """Get the discipline for a strava activity by looking up the type in the
    StraTypeMapping table. If no mapping exists, create a new one."""
    discipline = StravaTypeMapping.objects.filter(strava_type=activity.type).first()

    if not discipline:
        print("No discipline found for strava type ", activity.type)
        print("Adding this to database")
        discipline = StravaTypeMapping(strava_type=activity.type)
        discipline.save()

    return discipline


def import_activity(activity, user):
    """Convert a strava activity to a TrainingSession and import it into the
    database, if the strava_id does not exist."""
    strava_session = StravaSession.model_validate(activity)

    # TODO: Should we move this to not query the database for every activity?
    if TrainingSession.objects.filter(strava_id=strava_session.strava_id).exists():
        print("Activity already imported from strava")
        return

    discipline = get_discipline(strava_session)
    if not discipline.discipline:
        print("No discipline found for strava type ", strava_session.type)
        return

    training_session = TrainingSession(**strava_session.model_dump())
    training_session.user = user
    training_session.discipline = discipline.discipline
    training_session.save()

    print("Imported session from strava with name ", strava_session.name)
    return training_session

    # TODO: Add logic to suplement activity data with strava data
