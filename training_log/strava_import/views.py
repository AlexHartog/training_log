import json


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect

from .models import StravaAuth
from . import strava, strava_authentication


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
