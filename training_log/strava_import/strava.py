import requests
import os
from dotenv import dotenv_values
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

from .models import StravaTypeMapping, StravaAuth
from .schemas import StravaSession
from . import strava_authentication
from training.models import TrainingSession, Discipline, TrainingType

config = dotenv_values(os.path.join(settings.BASE_DIR, '.env'))


# TODO: Where to keep these constants?
PER_PAGE = 100
ACTIVITIES_URL = 'https://www.strava.com/api/v3/athlete/' \
                 'activities?per_page={per_page}'.format(per_page=PER_PAGE)


def strava_sync():
    print("Syncing")
    for strava_auth in StravaAuth.objects.all():
        if strava_auth.auto_import:
            print("Running auto import for ", strava_auth.user)
            get_activities(strava_auth.user)

def get_activities(user: User):
    strava_auth = strava_authentication.get_authentication(user)
    if not strava_auth:
        # TODO: Better exception
        raise Exception('No strava authentication')

    headers = {
        'Authorization': f'Bearer {strava_auth.access_token}'
    }

    response = requests.get(ACTIVITIES_URL, headers=headers)
    activities = response.json()

    # TODO: Handle bad response
    if response.status_code == 401:
        print('Not authorized. Time to refresh token.')
        # TODO: If we don't have refresh token, we need to get authorization again
        # refresh_token(strava_auth)
        # TODO: Can we call this function again without infinite recursion?
        # get_activities(strava_auth)
        return

    print("We've imported ", len(activities), " activities")
    # print("Activities: ", activities)
    imported_sessions = []
    for activity in activities:
        new_session = import_activity(activity, user=strava_auth.user)
        if new_session:
            imported_sessions.append(new_session)

    return imported_sessions


def get_discipline(activity):
    discipline = StravaTypeMapping.objects.filter(
        strava_type=activity.type).first()

    if not discipline:
        print("No discipline found for strava type ", activity.type)
        print("Adding this to database")
        discipline = StravaTypeMapping(strava_type=activity.type)
        discipline.save()

    return discipline


def import_activity(activity, user):
    strava_session_1 = StravaSession.model_validate(activity)

    print("Activity type: ", strava_session_1.type)
    print("Activity sport type: ", strava_session_1.sport_type)
    print("Activity: ", strava_session_1)

    # TODO: Should we move this to not query the database for every activity?
    if TrainingSession.objects.filter(strava_id=strava_session_1.id).exists():
        print("Activity already imported from strava")
        return

    discipline = get_discipline(strava_session_1)

    if not discipline.discipline:
        print("No discipline found for strava type ", strava_session_1.type)
        return

    format_string = "%Y-%m-%dT%H:%M:%SZ"

    # if Session.objects.filter()
    # TODO: How to deal with missing fields?

    # TODO: Make better conversion. We can make the schema have aliases and
    #       then the schema has the same field names as the model
    strava_session = TrainingSession.objects.create(
        user=user,
        discipline=discipline.discipline,
        date=datetime.strptime(strava_session_1.start_date_local, format_string).date(),
        total_duration=strava_session_1.elapsed_time,
        moving_duration=strava_session_1.moving_time,
        distance=strava_session_1.distance,
        training_type=None,
        date_added=timezone.now(),
        average_hr=strava_session_1.average_heartrate,
        max_hr=strava_session_1.max_heartrate,
        average_speed=strava_session_1.average_speed,
        max_speed=strava_session_1.max_speed,
        strava_updated=timezone.now(),
        strava_id=strava_session_1.id
    )
    strava_session.save()
    print("Imported session from strava with name ", strava_session_1.name)
    return strava_session

    # If not, create activity

    # TODO: Add logic to suplement activity data with strava data
