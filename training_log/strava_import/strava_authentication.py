import requests
import os
from dotenv import dotenv_values
from datetime import datetime
import enum

from django.conf import settings
from django.utils import timezone
from pydantic import BaseModel

from .models import StravaAuth
from .schemas import StravaTokenResponse
from django.contrib.auth.models import User
from training.models import TrainingSession, Discipline, TrainingType

config = dotenv_values(os.path.join(settings.BASE_DIR, '.env'))

ACCESS_TOKEN_VALIDITY = 3600
ACCESS_TOKEN_URL = 'https://www.strava.com/oauth/token'
REDIRECT_URI = 'http://localhost:8000/strava/auth'
AUTHORIZATION_URL = 'https://www.strava.com/oauth/' \
                    'authorize?client_id={client_id}&' \
                    'redirect_uri={redirect_uri}&response_type=code' \
                    '&scope=activity:read_all'


class AuthenticationStatus(enum.Enum):
    AUTHENTICATED = 1
    NOT_AUTHENTICATED = 2
    EXPIRED = 3


def get_authentication_status(user: User):
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


def is_authenticated(user: User):
    return get_authentication_status(user) == \
        AuthenticationStatus.AUTHENTICATED


def needs_authorization(user: User):
    print("Checking authorization")
    try:
        strava_auth = StravaAuth.objects.get(user=user)
        print("Found strava auth")
    except StravaAuth.DoesNotExist:
        return True

    print("Needs auth ", strava_auth.needs_authorization())
    return strava_auth.needs_authorization()


def get_authentication(user: User):
    strava_auth = StravaAuth.objects.get(user=user)
    if not strava_auth:
        return None

    if strava_auth.has_valid_access_token():
        return strava_auth

    if strava_auth.is_access_token_expired:
        refresh_token(strava_auth)

        if strava_auth.has_valid_access_token():
            return strava_auth

    return None


def get_authorization_url():
    return AUTHORIZATION_URL.format(
        client_id=config['STRAVA_CLIENT_ID'],
        redirect_uri=REDIRECT_URI,
    )


def refresh_token(strava_auth: StravaAuth):
    payload = {
        'client_id': config['STRAVA_CLIENT_ID'],
        'client_secret': config['STRAVA_CLIENT_SECRET'],
        'refresh_token': strava_auth.refresh_token,
        'grant_type': 'refresh_token',
    }
    print("Payload: ", payload)
    response = requests.post(ACCESS_TOKEN_URL, data=payload)

    # TODO: Handle bad response
    if response.status_code != 200:
        print(f'Token request failed {response.status_code}.')
        print(f'Errors: {response.content.decode("utf-8")}')

    # TODO: Do we need to handle bad response?
    strava_token_response = StravaTokenResponse(**response.json())
    strava_auth.update_token(strava_token_response)


def request_access_token(strava_auth):
    payload = {
        'client_id': config['STRAVA_CLIENT_ID'],
        'client_secret': config['STRAVA_CLIENT_SECRET'],
        'code': strava_auth.code,
        'grant_type': 'authorization_code',
    }
    print("Payload: ", payload)
    response = requests.post(ACCESS_TOKEN_URL, data=payload)

    # TODO: Handle bad response
    if response.status_code != 200:
        print(f'Token request failed {response.status_code}.')
        print(f'Errors: {response.content.decode("utf-8")}')
        return

    strava_token_response = StravaTokenResponse(**response.json())

    strava_auth.update_token(strava_token_response)


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
        scope=scope,
        auto_import=True,
    )
    StravaAuth.objects.filter(user=request.user).delete()
    strava_auth.save()

    request_access_token(strava_auth)