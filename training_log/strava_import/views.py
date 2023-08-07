import json
import datetime

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect

from .models import StravaAuth
from training.models import Session
from . import strava, strava_authentication
from .utils import get_timezone_aware_dt

DAYS_BACK = 10


@login_required(login_url=reverse_lazy('login'))
def index(request):
    if strava_authentication.needs_authorization(request.user):
        return render(request, 'strava_import/strava_auth.html',
                      {'authorization_url': strava_authentication.get_authorization_url()})

    imported_sessions = Session.objects.filter(user=request.user, strava_updated__gte=get_timezone_aware_dt(datetime.datetime.now()-datetime.timedelta(days=DAYS_BACK)))
    user_auth = StravaAuth.objects.get(user=request.user)

    context = {'imported_sessions': imported_sessions, 'days_back': DAYS_BACK, 'user_auth': user_auth}
    return render(request, 'strava_import/index.html', context=context)


@login_required(login_url=reverse_lazy('login'))
def enable_auto_import(request, enable: int):
    user_auth = StravaAuth.objects.get(user=request.user)
    user_auth.auto_import = True if enable == 1 else False
    user_auth.save()
    return redirect('strava-index')


@login_required(login_url=reverse_lazy('login'))
def strava_auth(request):
    if request.method == 'GET' and 'code' in request.GET:
        strava_authentication.save_auth(request)
        return redirect('strava-data')


@login_required(login_url=reverse_lazy('login'))
def get_strava_data(request):
    if request.method == 'GET' and 'code' in request.GET:
        strava_authentication.save_auth(request)
        return redirect(request.path)

    if not strava_authentication.needs_authorization(request.user):
        context = {'imported_sessions': []}
        # try:
        context['imported_sessions'] = strava.get_activities(request.user)
        # except Exception as e:
        #     print("Exception: ", e)
        #     messages.add_message(request, messages.ERROR, 'Error importing data')
        return render(request, 'strava_import/strava_import.html', context)
    else:
        print("We don't have proper authorization yet")

    return render(request, 'strava_import/strava_auth.html',
                  {'authorization_url': strava_authentication.get_authorization_url()})
