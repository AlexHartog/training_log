import datetime
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from training.models import TrainingSession

from . import (
    strava,
    strava_authentication,
    strava_start_time_sync,
    strava_subscription_manager,
)
from .models import StravaAuth, StravaSubscription

logger = logging.getLogger(__name__)

DAYS_BACK = 10
MANUAL_IMPORT_COUNT = 100


def admin_check(user):
    return user.is_superuser


@login_required(login_url=reverse_lazy("login"))
def index(request):
    if strava_authentication.needs_authorization(request.user):
        return redirect("strava-auth")

    imported_sessions = TrainingSession.objects.filter(
        user=request.user,
        strava_updated__gte=timezone.now() - datetime.timedelta(days=DAYS_BACK),
    ).order_by("-strava_updated", "-date")
    user_auth = StravaAuth.objects.get(user=request.user)

    context = {
        "imported_sessions": imported_sessions,
        "days_back": DAYS_BACK,
        "user_auth": user_auth,
        "admin": request.user.is_superuser,
        "strava_subscribed": strava_subscription_manager.get_current_subscription_enabled(),
    }
    return render(request, "strava_import/index.html", context=context)


@user_passes_test(admin_check)
def sync_start_times(request):
    strava_start_time_sync.strava_start_time_sync()
    return redirect("strava-index")


@login_required(login_url=reverse_lazy("login"))
def strava_auth(request):
    http_host = request.META["HTTP_HOST"]

    authorization_url = strava_authentication.get_authorization_url(http_host=http_host)

    context = {}
    if authorization_url:
        context["authorization_url"] = strava_authentication.get_authorization_url(
            http_host=http_host
        )
    else:
        messages.error(
            request,
            "Something went wrong with the authorization. "
            "Please contact the administrator.",
        )

    return render(request, "strava_import/strava_auth.html", context=context)


@login_required(login_url=reverse_lazy("login"))
def enable_auto_import(request, enable: int):
    user_auth = StravaAuth.objects.get(user=request.user)
    user_auth.auto_import = True if enable == 1 else False
    user_auth.save()
    return redirect("strava-index")


@login_required(login_url=reverse_lazy("login"))
def save_strava_auth(request):
    if request.method == "GET" and "code" in request.GET:
        strava_authentication.save_auth(request)
        return redirect("strava-data")


@login_required(login_url=reverse_lazy("login"))
def get_strava_data(request, user=None):
    if request.method == "GET" and "code" in request.GET:
        strava_authentication.save_auth(request)
        return redirect(request.path)

    if not strava_authentication.needs_authorization(request.user):
        context = {
            "imported_sessions": strava.get_activities(
                request.user, MANUAL_IMPORT_COUNT
            )
        }
        return render(request, "strava_import/strava_import.html", context)
    else:
        logger.warning("We don't have proper authorization yet")

    return redirect("strava-auth")


@user_passes_test(admin_check)
def subscribe_strava(request, subscribe: int):
    if subscribe:
        strava_subscription_manager.start_subscription(request)
    else:
        strava_subscription_manager.stop_subscription()

    return redirect("strava-admin")


@csrf_exempt
def activity_feed(request):
    """Handle activity feed. This can either be POST for validating the request or
    GET for a data event."""
    # TODO: Is there a better solution than to make this CSRF exempt?

    if request.method == "GET":
        verify_token = request.GET.get("hub.verify_token")
        strava_subscription = StravaSubscription.objects.first()

        if not strava_subscription:
            logger.error("No strava subscription found")
            return HttpResponseBadRequest("No strava subscription found")

        if verify_token != strava_subscription.verify_token:
            logger.error("Invalid verify token")
            return HttpResponseBadRequest("Invalid verify token")

        strava_subscription.state = StravaSubscription.SubscriptionState.VALIDATED
        strava_subscription.save()

        response_data = {"hub.challenge": request.GET.get("hub.challenge")}
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    elif request.method == "POST":
        content_type = request.META.get("CONTENT_TYPE")

        if content_type != "application/json":
            logger.error(f"Unexpected content type: {content_type}")
            return HttpResponseBadRequest("Unexpected content type: ", content_type)

        try:
            data = json.loads(request.body)
            strava_subscription_manager.handle_event_data(data)
        except json.JSONDecodeError:
            logger.error("Data is not valid JSON")
            return HttpResponseBadRequest("Data is not valid JSON")

        return HttpResponse("OK")

    return HttpResponseBadRequest("Unexpected request method: ", request.method)


@user_passes_test(admin_check)
def strava_admin(request):
    """Create data for an admin page. Includes user data."""
    users_with_strava_auth = User.objects.prefetch_related("stravaauth_set").all()
    users = []
    for user in users_with_strava_auth:
        new_user = {"user": user, "strava_auth": None}
        if user.stravaauth_set.exists():
            for strava_auth in user.stravaauth_set.all():
                new_user["strava_auth"] = strava_auth
        users.append(new_user)

    context = {
        "strava_subscribed": strava_subscription_manager.get_current_subscription_enabled(),
        "strava_users": users,
    }

    return render(request, "strava_import/strava_admin.html", context=context)


@user_passes_test(admin_check)
def admin_import_data(request):
    """Importing data as an admin for a user."""
    if request.method != "POST":
        raise Http404

    username = request.POST.get("username")
    num_sessions = int(request.POST.get("num_sessions"))
    user_to_import = User.objects.get(username__iexact=username)

    imported_sessions = strava.get_activities(user_to_import, num_sessions)

    logger.info(f"Imported {len(imported_sessions)} sessions")

    # TODO: Can we use messages to display imports

    return redirect("strava-admin")


@user_passes_test(admin_check)
def admin_athlete_update(request):
    """Update athlete data as an admin for a user."""
    if request.method != "POST":
        raise Http404

    username = request.POST.get("username")

    user_to_update = User.objects.get(username__iexact=username)
    strava_auth = strava_authentication.get_authentication(user_to_update)

    if not strava_auth:
        raise strava_authentication.NoAuthorizationException()

    strava.get_athlete_data(strava_auth)

    return redirect("strava-admin")
