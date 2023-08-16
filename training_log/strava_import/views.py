import datetime

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages

from .models import StravaAuth
from training.models import TrainingSession
from . import strava, strava_authentication

DAYS_BACK = 10
MANUAL_IMPORT_COUNT = 1


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
    }
    return render(request, "strava_import/index.html", context=context)


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
def get_strava_data(request):
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
        print("We don't have proper authorization yet")

    return redirect("strava-auth")
