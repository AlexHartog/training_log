import requests
import os
from dotenv import dotenv_values
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from .models import StravaAuth
from . import strava_authentication
from training.models import Session, Discipline, TrainingType

config = dotenv_values(os.path.join(settings.BASE_DIR, '.env'))


# TODO: Where to keep these constants?
ACTIVITIES_URL = 'https://www.strava.com/api/v3/athlete/activities?per_page=10'





def get_activities(user):
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


def import_activity(activity, user):
    if Session.objects.filter(strava_id=activity['id']).exists():
        print("Activity already imported from strava")
        return

    format_string = "%Y-%m-%dT%H:%M:%SZ"

    # if Session.objects.filter()
    # TODO: How to deal with missing fields?
    # TODO Create conversion from strava activity type to discipline
    strava_session = Session.objects.create(
        user=user,
        discipline=Discipline.objects.get(name='Running'),
        date=datetime.strptime(activity['start_date_local'], format_string).date(),
        total_duration=activity['elapsed_time'],
        moving_duration=activity['moving_time'],
        distance=activity['distance'],
        training_type=None,
        date_added=timezone.now(),
        average_hr=activity['average_heartrate'],
        max_hr=activity['max_heartrate'],
        average_speed=activity['average_speed'],
        max_speed=activity['max_speed'],
        strava_updated=timezone.now(),
        strava_id=activity['id']
    )
    strava_session.save()
    print("Imported session from strava with name ", activity['name'])
    return strava_session

    # If not, create activity

    # TODO: Add logic to suplement activity data with strava data
