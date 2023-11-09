import logging
import os
import random
import string

import requests

from . import strava
from .models import StravaSubscription, StravaUser
from .schemas import (ObjectTypeEnum, StravaEventData, SubscriptionCreation,
                      SubscriptionView)

logger = logging.getLogger(__name__)

SUBSCRIPTION_CREATION_URL = "https://www.strava.com/api/v3/push_subscriptions"
SUBSCRIPTION_VIEW_URL = (
    "https://www.strava.com/api/v3/push_subscriptions"
    "?client_id={client_id}&client_secret={client_secret}"
)
SUBSCRIPTION_DELETE_URL = (
    "https://www.strava.com/api/v3/push_subscriptions/{subscription_id}"
)

CALLBACK_URL = "{http_host}/strava/activity_feed"


def get_subscription_view_url():
    """Create view subscription url."""
    if not os.getenv("STRAVA_CLIENT_ID") or not os.getenv("STRAVA_CLIENT_SECRET"):
        logger.error(
            "No STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET"
        )  # TODO: Create nicer error message
        return

    return SUBSCRIPTION_VIEW_URL.format(
        client_id=os.getenv("STRAVA_CLIENT_ID"),
        client_secret=os.getenv("STRAVA_CLIENT_SECRET"),
    )


def get_subscription_delete_url(subscription_id):
    """Create delete subscription url."""
    return SUBSCRIPTION_DELETE_URL.format(
        subscription_id=subscription_id,
    )


def get_callback_url(http_host: str):
    """Create callback url."""
    return CALLBACK_URL.format(http_host=http_host)


def get_subscription_payload(verify_token: str, http_host: str):
    """Create payload for a subscription request."""
    if not os.getenv("STRAVA_CLIENT_ID") or not os.getenv("STRAVA_CLIENT_SECRET"):
        return

    return {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "callback_url": get_callback_url(http_host),
        "verify_token": verify_token,
    }


def get_subscription_delete_payload():
    """Create payload for a delete subscription request."""
    if not os.getenv("STRAVA_CLIENT_ID") or not os.getenv("STRAVA_CLIENT_SECRET"):
        return

    return {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
    }


def create_verify_token():
    """Create a random verify token."""
    token_length = 12
    return "".join(random.choices(string.ascii_letters, k=token_length))


def start_subscription(request):
    """Start a new strava subscription if we don't have an active one."""
    strava_subscription = get_current_subscription()

    if strava_subscription.enabled:
        logger.warning("We already have an active subscription")
        return

    if (current_subscription := view_subscription()) is not None:
        logger.info("We have an unknown subscription outstanding. Deleting this one")
        if delete_subscription(current_subscription.strava_id):
            logger.info("Successfully deleted subscription")
        else:
            logger.error("Failed to delete subscription")
            return

    if os.getenv("HOST_OVERRIDE"):
        http_host = os.getenv("HOST_OVERRIDE")
    else:
        http_host = f'http://{request.META["HTTP_HOST"]}'

    verify_token = create_verify_token()

    payload = get_subscription_payload(verify_token, http_host)

    change_subscription(
        state=StravaSubscription.SubscriptionState.CREATED,
        verify_token=verify_token,
        callback_url=get_callback_url(http_host),
    )

    response = requests.post(
        SUBSCRIPTION_CREATION_URL,
        data=payload,
    )

    if response.status_code != 201:
        logger.error(f"Subscription request failed {response.status_code}.")
        logger.error(f'Errors: {response.content.decode("utf-8")}')
        logger.error(f"Response: {response.json()}")
        return
    else:
        logger.info("Successfully subscribed to strava.")
        subscription_creation = SubscriptionCreation.model_validate(response.json())

        change_subscription(
            state=StravaSubscription.SubscriptionState.ACTIVE,
            enabled=True,
            strava_id=subscription_creation.strava_id,
        )


def change_subscription(
    state: StravaSubscription.SubscriptionState = None,
    enabled: bool = None,
    callback_url: str = None,
    verify_token: str = None,
    strava_id: int = None,
):
    """Update the current subscription."""
    strava_subscription = get_current_subscription()
    if state is not None:
        strava_subscription.state = state
    if enabled is not None:
        strava_subscription.enabled = enabled
    if callback_url is not None:
        strava_subscription.callback_url = callback_url
    if verify_token is not None:
        strava_subscription.verify_token = verify_token
    if strava_id is not None:
        strava_subscription.strava_id = strava_id
    strava_subscription.save()


def get_current_subscription():
    """Get current subscription or create a new one if none exists."""
    if StravaSubscription.objects.count() > 1:
        raise Exception("Too many subscriptions")

    strava_subscription = StravaSubscription.objects.first()

    if strava_subscription is None:
        return StravaSubscription(state=StravaSubscription.SubscriptionState.CREATED)

    return strava_subscription


def get_current_subscription_enabled(check=False):
    """Return if the current subscription is enabled. Optionally check with strava
    if this is the active subscription."""
    if check:
        check_subscription()
    return get_current_subscription().enabled


def check_subscription():
    """Check if subscription at strava is still valid."""
    current_subscription = get_current_subscription()

    strava_subscription = view_subscription()

    if strava_subscription is None:
        change_subscription(enabled=False)
    elif strava_subscription.strava_id != current_subscription.strava_id:
        logger.warning("Subscription at strava does not match.")
        change_subscription(enabled=False)
    elif strava_subscription.callback_url != current_subscription.callback_url:
        logger.error(
            f"Callback url does not match. "
            f"Current is {current_subscription.callback_url}, "
            f"but strava has {strava_subscription.callback_url}."
        )
        current_subscription.save()


def view_subscription():
    """View the current subscription."""
    response = requests.get(get_subscription_view_url())

    if response.status_code != 200:
        return

    response_json = response.json()

    if len(response_json) > 1:
        logger.error(
            f"Received {len(response_json)} responses. "
            f"We only support one subscription."
        )
        return

    if len(response_json) == 0:
        logger.info("No subscriptions found.")
        return

    return SubscriptionView.model_validate(response_json[0])


def delete_subscription(subscription_id: int):
    """Delete a strava subscription."""

    active_subscription = view_subscription()

    if active_subscription is None:
        logger.warning("No active subscription. Not deleting.")
        change_subscription(
            enabled=False, state=StravaSubscription.SubscriptionState.INVALID
        )
        return

    if active_subscription.strava_id != subscription_id:
        logger.warning("Our subscription is not the active one. Not deleting.")
        change_subscription(
            enabled=False, state=StravaSubscription.SubscriptionState.INVALID
        )
        return

    payload = get_subscription_delete_payload()
    response = requests.delete(
        get_subscription_delete_url(subscription_id), data=payload
    )

    if response.status_code != 204:
        logger.error(f"Subscription request failed {response.status_code}.")
        logger.error(f'Errors: {response.content.decode("utf-8")}')
        logger.error(f"Response: {response.json()}")
        return False
    else:
        logger.info("Successfully unsubscribed from strava.")
        return True


def stop_subscription():
    current_subscription = get_current_subscription()

    if current_subscription.strava_id:
        if delete_subscription(current_subscription.strava_id):
            current_subscription.delete()
    else:
        logger.warning("No subscription to stop")


def handle_event_data(strava_event_data):
    """Handle an event by parsing the data and processing it
    if it is an event type that we handle."""
    event_data = StravaEventData.model_validate(strava_event_data)

    if event_data.object_type == ObjectTypeEnum.ACTIVITY:
        strava_user = StravaUser.objects.filter(strava_id=event_data.owner_id).first()

        if strava_user is None:
            logger.warning(f"Could not find strava user for id {event_data.object_id}")
            return

        strava.request_and_import_activity(event_data.object_id, strava_user.user)
    else:
        logger.info(
            f'Received event of type "{event_data.object_type.value}" and '
            f'aspect "{event_data.aspect_type.value}". '
            f"Not handling at the moment."
        )
