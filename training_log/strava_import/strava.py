import os

import requests
from django.conf import settings
from django.contrib.auth.models import User
from dotenv import dotenv_values
from training.models import TrainingSession, SessionZones, Zone

from . import strava_authentication
from .models import (
    StravaAuth,
    StravaTypeMapping,
    StravaActivityImport,
    StravaRateLimit,
    StravaUser,
)
from .schemas import (
    StravaSession,
    StravaSessionZones,
    StravaZone,
    StravaEventData,
    ObjectTypeEnum,
    AspectTypeEnum,
)

config = dotenv_values(os.path.join(settings.BASE_DIR, ".env"))


# TODO: Where to keep these constants?
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities?per_page={per_page}"
ACITIVITY_URL = "https://www.strava.com/api/v3/activities/{activity_id}"
ACITIVITY_ZONES_URL = "https://www.strava.com/api/v3/activities/{activity_id}/zones"
CALLBACK_URL = "{http_host}/strava/activity_feed"
SUBSCRIPTION_CREATION_URL = "https://www.strava.com/api/v3/push_subscriptions"
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


def get_activity_url(activity_id: int):
    """Builds the url to get a single activity from strava."""
    return ACITIVITY_URL.format(activity_id=activity_id)


def get_activity_zones_url(strava_id: int):
    """Builds the url to get activity zones from strava."""
    return ACITIVITY_ZONES_URL.format(activity_id=strava_id)


def check_rate_limits_left(plenty: bool = False):
    """Check if we still have enough space in the rate limits."""
    rate_limits = StravaRateLimit.objects.first()
    if rate_limits is None:
        return True

    if plenty:
        return rate_limits.have_plenty_usage_remaining()
    else:
        return rate_limits.have_usage_remaining()


def get_activities(user: User, result_per_page: int):
    """Request activities from strava and import them into the database."""
    strava_auth = strava_authentication.get_authentication(user)
    if not strava_auth:
        raise strava_authentication.NoAuthorizationException()

    if not check_rate_limits_left(plenty=True):
        print("No rate limits left, so skipping request")
        return

    headers = {"Authorization": f"Bearer {strava_auth.access_token}"}
    response = requests.get(get_activities_url(result_per_page), headers=headers)

    update_rate_limits(response.headers)

    if response.status_code != 200:
        print("Strava API returned error: ", response.json())
        return

    activities = response.json()
    print("We've imported ", len(activities), " activities")

    imported_sessions = []
    for activity in activities:
        new_session = import_activity(activity, user=strava_auth.user)
        if new_session:
            imported_sessions.append(new_session)

    return imported_sessions


def get_activity_zones(user: User, strava_id: int):
    """Request activity zones from strava and import them into the database."""
    strava_auth = strava_authentication.get_authentication(user)
    if not strava_auth:
        raise strava_authentication.NoAuthorizationException()

    if not check_rate_limits_left(plenty=True):
        print("Not enough rate limits left, so skipping activity zones request")
        return

    headers = {"Authorization": f"Bearer {strava_auth.access_token}"}
    response = requests.get(get_activity_zones_url(strava_id), headers=headers)

    update_rate_limits(response.headers)

    if response.status_code != 200:
        print("Strava API returned error: ", response.json())
        return

    activity_zones = response.json()

    return activity_zones


def get_discipline(activity: StravaSession):
    """Get the discipline for a strava activity by looking up the type in the
    StraTypeMapping table. If no mapping exists, create a new one."""
    discipline = StravaTypeMapping.objects.filter(strava_type=activity.type).first()

    if not discipline:
        print("No discipline found for strava type ", activity.type)
        print("Adding this to database")
        discipline = StravaTypeMapping(strava_type=activity.type)
        discipline.save()

    return discipline


def save_activity_json(activity: dict, user: User, strava_id: int, data_type: str):
    """Save the json data from strava to the database if it does not exist."""
    if not StravaActivityImport.objects.filter(
        strava_id=strava_id, type=data_type
    ).exists():
        StravaActivityImport.objects.create(
            strava_id=strava_id,
            user=user,
            type=data_type,
            json_data=activity,
        )


def import_training_session(strava_session: StravaSession, user: User):
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


def import_session_zones(strava_id: int, user: User):
    """If zones do not exist, import them from strava and save them to the database."""
    try:
        session_id = TrainingSession.objects.get(strava_id=strava_id).id
    except TrainingSession.DoesNotExist:
        print("No session found for strava id ", strava_id, ". Cannot import zones.")
        return

    if (zones_count := SessionZones.objects.filter(session_id=session_id).count()) > 0:
        print(
            zones_count,
            "session zones already imported from strava for id",
            strava_id,
        )
        return

    activity_zones_json = get_activity_zones(user, strava_id)

    save_activity_json(
        activity_zones_json, user, strava_id, StravaActivityImport.ACTIVITY_ZONES
    )

    for activity_zone in activity_zones_json:
        strava_activity_zones = StravaSessionZones.model_validate(activity_zone)
        session_zones = SessionZones(**strava_activity_zones.model_dump())
        session_zones.session_id = session_id
        session_zones.save()

        for strava_zone in strava_activity_zones.zones:
            save_strava_zone(strava_zone, session_zones.id)


def save_strava_zone(strava_zone: StravaZone, session_zones_id: int):
    """Convert a strava zone to a zone and save it to the database."""
    zone = Zone(**strava_zone.model_dump())
    zone.session_zones_id = session_zones_id
    zone.save()


def request_and_import_activity(activity_id: int, user: User):
    strava_auth = strava_authentication.get_authentication(user)
    if not strava_auth:
        raise strava_authentication.NoAuthorizationException()

    if not check_rate_limits_left():
        print("No rate limits left, so skipping request")
        return

    headers = {"Authorization": f"Bearer {strava_auth.access_token}"}
    response = requests.get(get_activity_url(activity_id), headers=headers)

    update_rate_limits(response.headers)

    if response.status_code != 200:
        print("Strava API returned error: ", response.json())
        return

    activity = response.json()

    new_session = import_activity(activity, user=user)

    return new_session


def import_activity(activity: dict, user: User):
    """Import activity by saving it to the database and importing the zones."""
    strava_session = StravaSession.model_validate(activity)

    save_activity_json(
        activity, user, strava_session.strava_id, StravaActivityImport.ACTIVITY
    )
    training_session = import_training_session(strava_session, user)

    import_session_zones(strava_session.strava_id, user)

    return training_session


def update_rate_limits(headers):
    """Update the rate limits of the strava api."""
    StravaRateLimit.objects.all().delete()

    RATE_LIMIT_LIMIT = "X-RateLimit-Limit"
    RATE_LIMIT_USAGE = "X-RateLimit-Usage"
    if RATE_LIMIT_LIMIT not in headers or RATE_LIMIT_USAGE not in headers:
        print("Could not update rate limits, missing headers")
        return

    short_limit_limit, daily_limit_limit = headers[RATE_LIMIT_LIMIT].split(",")
    short_limit_usage, daily_limit_usage = headers[RATE_LIMIT_USAGE].split(",")

    StravaRateLimit.objects.create(
        short_limit=int(short_limit_limit),
        daily_limit=int(daily_limit_limit),
        short_limit_usage=int(short_limit_usage),
        daily_limit_usage=int(daily_limit_usage),
    ).save()


def get_subscription_payload(verify_token: str, http_host: str):
    if not os.getenv("STRAVA_CLIENT_ID") or not os.getenv("STRAVA_CLIENT_SECRET"):
        return

    return {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "callback_url": CALLBACK_URL.format(http_host=http_host),
        "verify_token": verify_token,
    }


def start_subscription(request):
    print("Starting subscription")

    if os.getenv("HOST_OVERRIDE"):
        http_host = os.getenv("HOST_OVERRIDE")
    else:
        http_host = f'http://{request.META["HTTP_HOST"]}'

    verify_token = "123TeST"
    # TODO: Create small algo for verify token

    payload = get_subscription_payload(verify_token, http_host)
    print("Payload: ", payload)

    # return

    response = requests.post(
        SUBSCRIPTION_CREATION_URL,
        data=payload,
    )

    if response.status_code != 201:
        print(f"Subscription request failed {response.status_code}.")
        print(f'Errors: {response.content.decode("utf-8")}')
        print(f"Response: {response.json()}")
        return
    else:
        print("Successfully subscribed to strava.")

    pass


def view_subscription(request):
    pass


def handle_event_data(strava_event_data):
    event_data = StravaEventData.model_validate(strava_event_data)
    print("Read event data: ", event_data)

    if (
        event_data.object_type == ObjectTypeEnum.ACTIVITY
        and event_data.aspect_type == AspectTypeEnum.CREATE
    ):
        strava_user = StravaUser.objects.filter(strava_id=event_data.owner_id).first()

        if strava_user is None:
            print("Could not find strava user for id ", event_data.object_id)
            return

        new_session = request_and_import_activity(
            event_data.object_id, strava_user.user
        )
        print("Imported session from strava: ", new_session)
    else:
        print(
            f"Received event of type {event_data.object_type} and aspect {event_data.aspect_type}. "
            f"Not handling at the moment."
        )


# def subscribe():
#     """Subscribe to strava notifications."""
#     verify_token = "123TeST"
#     # TODO: Create small algo for verify token
#
#     payload = get_subscription_payload(verify_token)
#     print("Payload: ", payload)
#
#     return
#     assert False
#     response = requests.post(
#         SUBSCRIPTION_CREATION_URL,
#         data=(payload := get_subscription_payload(verify_token)),
#     )
#
#     if response.status_code != 200:
#         print(f"Subscription request failed {response.status_code}.")
#         print(f'Errors: {response.content.decode("utf-8")}')
#         print(f"Response: {response.json()}")
#         return
#     else:
#         print("Successfully subscribed to strava.")
#
#     pass
#
#
# def subscribe_if_needed():
#     if not os.getenv("SUBSCRIBE_STRAVA"):
#         return
#
#     subscribe()
