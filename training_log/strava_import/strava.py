import requests
import os
from dotenv import dotenv_values
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from .models import StravaAuth
from training.models import Session, Discipline, TrainingType

config = dotenv_values(os.path.join(settings.BASE_DIR, '.env'))


# TODO: Where to keep these constants?
ACTIVITIES_URL = 'https://www.strava.com/api/v3/athlete/activities?per_page=1'
ACCESS_TOKEN_VALIDITY = 3600


def get_authorization():
    client_id = config['STRAVA_CLIENT_ID']
    redirect_uri = 'http://127.0.0.1:8000/strava'

    authorization_url = f'https://www.strava.com/oauth/' \
                        f'authorize?client_id={client_id}&' \
                        f'redirect_uri={redirect_uri}&response_type=code' \
                        f'&scope=activity:read_all'

    return authorization_url


def refresh_token(strava_auth):
    access_token_url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': config['STRAVA_CLIENT_ID'],
        'client_secret': config['STRAVA_CLIENT_SECRET'],
        'refresh_token': strava_auth.refresh_token,
        'grant_type': 'refresh_token',
    }
    print("Payload: ", payload)
    response = requests.post(access_token_url, data=payload)

    # TODO: Handle bad response
    if response.status_code != 200:
        print(f'Token request failed {response.status_code}.')
        print(f'Errors: {response.content.decode("utf-8")}')

    # TODO: Use pydance to parse response
    json_response = response.json()
    print("response.json(): ", response.json())
    strava_auth.access_token = json_response['access_token']
    naive_datetime = datetime.fromtimestamp(json_response['expires_at'])
    aware_datetime = timezone.make_aware(naive_datetime,
                                         timezone.get_current_timezone())

    strava_auth.access_token_expires_at = aware_datetime
    strava_auth.refresh_token = json_response['refresh_token']

    strava_auth.save()


def get_access_token(strava_auth):
    access_token_url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': config['STRAVA_CLIENT_ID'],
        'client_secret': config['STRAVA_CLIENT_SECRET'],
        'code': strava_auth.code,
        'grant_type': 'authorization_code',
    }
    print("Payload: ", payload)
    response = requests.post(access_token_url, data=payload)

    # TODO: Handle bad response
    if response.status_code != 200:
        print(f'Token request failed {response.status_code}.')
        print(f'Errors: {response.content.decode("utf-8")}')
        return

    json_response = response.json()
    # print("response.json(): ", response.json())
    strava_auth.access_token = json_response['access_token']
    print("Expires at: ", json_response['expires_at'])
    print("Expires at: ", datetime.fromtimestamp(json_response['expires_at']))
    print("Seconds until expiry", json_response['expires_in'])
    naive_datetime = datetime.fromtimestamp(json_response['expires_at'])
    aware_datetime = timezone.make_aware(naive_datetime,
                                         timezone.get_current_timezone())

    strava_auth.access_token_expires_at = aware_datetime
    strava_auth.refresh_token = json_response['refresh_token']
    strava_auth.save()


def save_auth(request):
    if 'code' not in request.GET:
        print('No code in request')
        return

    code = request.GET['code']
    scope = request.GET['scope'].split(
        ',') if 'scope' in request.GET else []

    # access_token = get_access_token(code)
    print("We received code ", code)
    # TODO: Check if scope is alright, need read_all
    # TODO: Handle denied

    strava_auth = StravaAuth.objects.create(
        user=request.user,
        code=code,
        # access_token=access_token,
        # access_token_retrieved_at=datetime.now(),
        scope=scope
    )
    StravaAuth.objects.filter(user=request.user).delete()
    strava_auth.save()

    get_access_token(strava_auth)


def get_activities(strava_auth):
    if not strava_auth.access_token:
        print('No access token')
        # TODO: Request access token
        # TODO: Need better error handling
        raise Exception('No access token')

    aware_datetime = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
    if strava_auth.access_token_expires_at < aware_datetime:
        print('Access token expired, refreshing')
        # TODO: Handle failure
        refresh_token(strava_auth)

    headers = {
        'Authorization': f'Bearer {strava_auth.access_token}'
    }
    print("Strava auth: ", strava_auth)
    print("Expires at: ", strava_auth.access_token_expires_at)

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
    for activity in activities:
        import_activity(activity, user=strava_auth.user)


def import_activity(activity, user):
    print("Importing")
    # Check if activity already exists
    # print("Found activity: ", activity)
    print("id ",  activity['id'])
    print("Activity",  Session.objects.filter(strava_id=activity['id']))

    if Session.objects.filter(strava_id=activity['id']).exists():
        print("Activity already imported from strava")
        return

    print("Function was ok")

    format_string = "%Y-%m-%dT%H:%M:%SZ"

    # if Session.objects.filter()
    # Session.objects.filter()
    # TODO: How to deal with missing fields?
    # TODO Create conversion from strava activity type to discipline
    strava_session = Session.objects.create(
        user=user,
        discipline=Discipline.objects.get(name='Swimming'),
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

    # If not, create activity

    # TODO: Add logic to suplement activity data with strava data
