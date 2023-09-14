import enum
import os
import logging

import requests
from django.conf import settings
from django.contrib.auth.models import User
from dotenv import dotenv_values

from .models import StravaAuth, StravaUser
from .schemas import StravaAthleteData, StravaTokenResponse

logger = logging.getLogger(__name__)

config = dotenv_values(os.path.join(settings.BASE_DIR, ".env"))

ACCESS_TOKEN_VALIDITY = 3600
ACCESS_TOKEN_URL = "https://www.strava.com/oauth/token"
REDIRECT_URI = "http://{http_host}/strava/save_auth"
AUTHORIZATION_URL = (
    "https://www.strava.com/oauth/"
    "authorize?client_id={client_id}&"
    "redirect_uri={redirect_uri}&response_type=code"
    "&scope=activity:read_all"
)


class AuthenticationStatus(enum.Enum):
    """Enum for the authentication status of a user."""

    AUTHENTICATED = 1
    NOT_AUTHENTICATED = 2
    EXPIRED = 3


class NoAuthorizationException(Exception):
    """Exception for when a user is not authorized with strava."""

    pass


def get_authentication_status(user: User):
    """Returns the authentication status for a user."""
    try:
        strava_auth = StravaAuth.objects.get(user=user)
    except StravaAuth.DoesNotExist:
        return AuthenticationStatus.NOT_AUTHENTICATED

    if strava_auth.has_valid_access_token():
        return AuthenticationStatus.AUTHENTICATED

    if not strava_auth.access_token:
        return AuthenticationStatus.NOT_AUTHENTICATED

    if strava_auth.is_access_token_expired():
        return AuthenticationStatus.EXPIRED


def is_authenticated(user: User):
    """Checks if a user is authenticated with strava."""
    return get_authentication_status(user) == AuthenticationStatus.AUTHENTICATED


def needs_authorization(user: User):
    """Checks if a user needs to authorize strava."""
    try:
        strava_auth = StravaAuth.objects.get(user=user)
    except StravaAuth.DoesNotExist:
        return True

    return strava_auth.needs_authorization()


def get_authentication(user: User):
    """Returns the strava authentication for a user if it exists and is valid.
    If token is expired, it will try to refresh it."""
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


def get_authorization_url(http_host):
    """Returns the url to authorize strava."""
    if not os.getenv("STRAVA_CLIENT_ID"):
        return

    return AUTHORIZATION_URL.format(
        client_id=os.getenv("STRAVA_CLIENT_ID"),
        redirect_uri=REDIRECT_URI.format(http_host=http_host),
    )


def refresh_token_if_expired(strava_auth: StravaAuth):
    """Checks if the access token for a user is expired and refreshes it if it is."""
    if strava_auth.is_access_token_expired():
        logger.info(
            "Access token expired for ", strava_auth.user.username, ". Refreshing token"
        )
        refresh_token(strava_auth)


def _get_token_payload(strava_auth: StravaAuth, refresh=False):
    """Creates the payload for a token request. Either initial or refresh."""
    # TODO: Raise error if no client id or secret is set
    if not os.getenv("STRAVA_CLIENT_ID") or not os.getenv("STRAVA_CLIENT_SECRET"):
        return

    payload = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
    }

    if refresh:
        payload["refresh_token"] = strava_auth.refresh_token
        payload["grant_type"] = "refresh_token"
    else:
        payload["code"] = strava_auth.code
        payload["grant_type"] = "authorization_code"

    return payload


def _access_token_update(strava_auth: StravaAuth, refresh=False):
    """Updates the access token for a user. This can either be an initial request or
    a refresh request."""
    payload = _get_token_payload(strava_auth, refresh=refresh)

    response = requests.post(ACCESS_TOKEN_URL, data=payload)

    logger.debug("Access Token Response: ", response.json())

    # TODO: Deal with invalid client secret (weird reponse from strava)
    if response.status_code != 200:
        logger.error(f"Token request failed {response.status_code}.")
        logger.error(f'Errors: {response.content.decode("utf-8")}')
        return

    strava_token_response = StravaTokenResponse(**response.json())
    strava_auth.update_token(strava_token_response)

    update_strava_user(strava_auth.user, strava_token_response.athlete)


def update_strava_user(user: User, strava_athlete: StravaAthleteData):
    strava_user = StravaUser.objects.filter(strava_id=strava_athlete.strava_id).first()

    if not strava_user:
        StravaUser.objects.create(user=user, strava_id=strava_athlete.strava_id)
        StravaUser.save()


def refresh_token(strava_auth: StravaAuth):
    """Refreshes the access token for a user."""
    _access_token_update(strava_auth, refresh=True)


def request_access_token(strava_auth: StravaAuth):
    """Requests an access token for a user."""
    _access_token_update(strava_auth, refresh=False)


def save_auth(request):
    if "code" not in request.GET:
        logger.error("No code in request")
        return

    code = request.GET["code"]
    scope = request.GET["scope"].split(",") if "scope" in request.GET else []

    # access_token = get_access_token(code)
    # TODO: Check if scope is alright, need read_all
    # TODO: Handle denied

    strava_auth = StravaAuth.objects.create(
        user=request.user,
        code=code,
        scope=scope,
        auto_import=True,
    )
    StravaAuth.objects.filter(user=request.user).delete()
    strava_auth.save()

    request_access_token(strava_auth)
