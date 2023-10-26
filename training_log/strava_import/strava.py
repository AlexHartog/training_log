import logging
import os

import requests
from django.conf import settings
from django.contrib.auth.models import User
from dotenv import dotenv_values
from training import maps
from training.models import MunicipalityVisits, SessionZones, TrainingSession, Zone

from . import strava_authentication
from .models import (
    StravaActivityImport,
    StravaAuth,
    StravaRateLimit,
    StravaTypeMapping,
    StravaUser,
)
from .schemas import StravaAthleteData, StravaSession, StravaSessionZones, StravaZone

logger = logging.getLogger(__name__)
config = dotenv_values(os.path.join(settings.BASE_DIR, ".env"))


# TODO: Where to keep these constants?
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities?per_page={per_page}"
ACITIVITY_URL = "https://www.strava.com/api/v3/activities/{activity_id}"
ACITIVITY_ZONES_URL = "https://www.strava.com/api/v3/activities/{activity_id}/zones"
ATHLETE_URL = "https://www.strava.com/api/v3/athlete"
SYNC_PAGE_COUNT = os.getenv("STRAVA_SYNC_COUNT") or 1


def strava_sync():
    """Syncs activities for all users with auto import enabled."""
    for strava_auth in StravaAuth.objects.all():
        if strava_auth.auto_import:
            logger.info(
                f"Running auto import ({SYNC_PAGE_COUNT} page(s)) "
                f"for {strava_auth.user}"
            )
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


def get_athlete_url():
    """Builds the url to get the athlete from strava."""
    return ATHLETE_URL


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
        logger.info("No rate limits left, so skipping request")
        return

    headers = {"Authorization": f"Bearer {strava_auth.access_token}"}
    logger.info(f"Headers: {headers}")
    response = requests.get(get_activities_url(result_per_page), headers=headers)

    update_rate_limits(response.headers)

    if response.status_code != 200:
        logger.error(f"Strava API returned error: {response.json()}")
        return

    activities = response.json()
    logger.info(f"We've imported {len(activities)} activities")

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
        logger.info("Not enough rate limits left, so skipping activity zones request")
        return

    headers = {"Authorization": f"Bearer {strava_auth.access_token}"}
    response = requests.get(get_activity_zones_url(strava_id), headers=headers)

    update_rate_limits(response.headers)

    if response.status_code != 200:
        logger.error(f"Strava API returned error: {response.json()}")
        return

    activity_zones = response.json()

    return activity_zones


def get_discipline(activity: StravaSession):
    """Get the discipline for a strava activity by looking up the type in the
    StraTypeMapping table. If no mapping exists, create a new one."""
    discipline = StravaTypeMapping.objects.filter(strava_type=activity.type).first()

    if not discipline:
        logger.info(f"No discipline found for strava type {activity.type}")
        logger.info("Adding this to database")
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
    if TrainingSession.objects.filter(strava_id=strava_session.strava_id).exists():
        logger.info(
            f"Activity with id {strava_session.strava_id} already imported from strava"
        )
        return

    discipline = get_discipline(strava_session)
    if not discipline.discipline:
        logger.info(f"No discipline found for strava type {strava_session.type}")
        return

    training_session = TrainingSession(**strava_session.model_dump())
    training_session.user = user
    training_session.discipline = discipline.discipline
    training_session.save()

    logger.info(f"Imported session from strava with name {strava_session.name}")
    return training_session


def import_session_zones(strava_id: int, user: User):
    """If zones do not exist, import them from strava and save them to the database."""
    strava_user = StravaUser.objects.filter(user=user).first()

    if not strava_user:
        logger.warning(f"No user found for strava id {strava_id}. Not importing zones.")
        return

    if not strava_user.premium:
        logger.info(
            f"User {strava_user.name} does not have premium. " f"Not importing zones."
        )
        return

    try:
        session_id = TrainingSession.objects.get(strava_id=strava_id).id
    except TrainingSession.DoesNotExist:
        logger.warning(
            f"No session found for strava id {strava_id}. Cannot import zones."
        )
        return

    if (zones_count := SessionZones.objects.filter(session_id=session_id).count()) > 0:
        logger.info(
            f"{zones_count} session zones already imported "
            f"from strava for id {strava_id}"
        )
        return

    activity_zones_json = get_activity_zones(user, strava_id)

    if activity_zones_json:
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

        logger.info(
            f"Imported {len(activity_zones_json)} zones "
            f"for activity with id {strava_id}"
        )


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
        logger.info("No rate limits left, so skipping request")
        return

    headers = {"Authorization": f"Bearer {strava_auth.access_token}"}
    response = requests.get(get_activity_url(activity_id), headers=headers)

    update_rate_limits(response.headers)

    if response.status_code != 200:
        logger.error(f"Strava API returned error: {response.json()}")
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

    if not training_session:
        return

    import_session_zones(strava_session.strava_id, user)

    update_map(training_session)

    return training_session


def update_rate_limits(headers):
    """Update the rate limits of the strava api."""
    StravaRateLimit.objects.all().delete()

    RATE_LIMIT_LIMIT = "X-RateLimit-Limit"
    RATE_LIMIT_USAGE = "X-RateLimit-Usage"
    if RATE_LIMIT_LIMIT not in headers or RATE_LIMIT_USAGE not in headers:
        logger.warning("Could not update rate limits, missing headers")
        return

    short_limit_limit, daily_limit_limit = headers[RATE_LIMIT_LIMIT].split(",")
    short_limit_usage, daily_limit_usage = headers[RATE_LIMIT_USAGE].split(",")

    StravaRateLimit.objects.create(
        short_limit=int(short_limit_limit),
        daily_limit=int(daily_limit_limit),
        short_limit_usage=int(short_limit_usage),
        daily_limit_usage=int(daily_limit_usage),
    ).save()


def update_strava_user(user: User, strava_athlete: StravaAthleteData):
    """Create or update the strava user data."""
    strava_user, created = StravaUser.objects.get_or_create(
        user=user, defaults=strava_athlete
    )

    if not created:
        for field in strava_athlete.model_fields:
            setattr(strava_user, field, getattr(strava_athlete, field))

        strava_user.save()

    logger.info(
        f"Strava user {strava_user} was { 'created' if created else 'updated' }"
    )


def get_athlete_data(strava_auth: StravaAuth):
    """Get athlete data from strava."""
    if not strava_auth:
        raise strava_authentication.NoAuthorizationException()

    if not check_rate_limits_left():
        logger.warning("No rate limits left, so skipping request")
        return

    headers = {"Authorization": f"Bearer {strava_auth.access_token}"}
    response = requests.get(get_athlete_url(), headers=headers)

    update_rate_limits(response.headers)

    if response.status_code != 200:
        logger.error(f"Strava API returned error: {response.json()}")
        return

    athlete = response.json()
    athlete_data = StravaAthleteData.model_validate(athlete)

    update_strava_user(strava_auth.user, athlete_data)


def parse_activity_data(user_to_parse_for: User):
    """Parse activity without communicating with Strava."""
    sessions = TrainingSession.objects.filter(user=user_to_parse_for).all()

    training_map = maps.TrainingMap()

    municipality_visits_added = 0

    for session in sessions:
        if update_map(session, training_map):
            municipality_visits_added += 1

    return {"Municipality Visits Added": municipality_visits_added}


def update_map(session: TrainingSession, training_map: maps.TrainingMap = None):
    """Update the map of the session."""
    if not session.summary_polyline:
        strava_activity_data = StravaActivityImport.objects.filter(
            strava_id=session.strava_id,
            type=StravaActivityImport.ACTIVITY,
        ).first()

        if not strava_activity_data:
            return

        strava_session = StravaSession.model_validate(strava_activity_data.json_data)

        if not strava_session.summary_polyline:
            return

        session.summary_polyline = strava_session.summary_polyline
        session.polyline = strava_session.polyline
        session.save()

    municipality_visits = (
        MunicipalityVisits.objects.filter(training_session=session).all().count()
    )

    if municipality_visits == 0:
        if not training_map:
            training_map = maps.TrainingMap()

        munis = training_map.get_municipalities(session.summary_polyline)

        if not munis:
            return

        for mun in munis:
            municipality_visit = MunicipalityVisits(
                training_session=session, municipality=mun
            )
            municipality_visit.save()

        logger.info(f"Added municipality visits for session {session.strava_id}")

        return True
