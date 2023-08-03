import requests
import os
from dotenv import dotenv_values
from datetime import datetime
import enum

from django.conf import settings
from django.utils import timezone

from .models import StravaAuth
from training.models import Session, Discipline, TrainingType

config = dotenv_values(os.path.join(settings.BASE_DIR, '.env'))

ACCESS_TOKEN_VALIDITY = 3600


class AuthenticationStatus(enum.Enum):
    AUTHENTICATED = 1
    NOT_AUTHENTICATED = 2
    EXPIRED = 3


def get_authentication_status(user):
    try:
        strava_auth = StravaAuth.objects.get(user=user)
    except StravaAuth.DoesNotExist:
        return AuthenticationStatus.NOT_AUTHENTICATED

    if strava_auth.has_valid_access_token():
        return AuthenticationStatus.AUTHENTICATED

    if not strava_auth.access_token:
        print('No access token')
        return AuthenticationStatus.NOT_AUTHENTICATED

    if strava_auth.is_access_token_expired():
        return AuthenticationStatus.EXPIRED


def is_authenticated(user):
    return get_authentication_status(user) == \
        AuthenticationStatus.AUTHENTICATED


def needs_authorization(user):
    print("Checking authorization")
    try:
        strava_auth = StravaAuth.objects.get(user=user)
        print("Found strava auth")
    except StravaAuth.DoesNotExist:
        return True

    print("Needs auth ", strava_auth.needs_authorization())
    return strava_auth.needs_authorization()


def get_authentication(user):
    if is_authenticated(user):
        return StravaAuth.objects.get(user=user)
    else:
        if get_authentication_status(user) == AuthenticationStatus.EXPIRED:
            refresh_token(user)
            if is_authenticated(user):
                return StravaAuth.objects.get(user=user)

    return None





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


def request_access_token(strava_auth):
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

    request_access_token(strava_auth)