import json


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.shortcuts import redirect

from .models import StravaAuth
from . import strava


@login_required(login_url=reverse_lazy('login'))
def get_strava_data(request):
    if request.method == 'GET' and 'code' in request.GET:
        strava.save_auth(request)
        return redirect(request.path)

    if StravaAuth.objects.filter(user=request.user).exists():
        strava_auth = StravaAuth.objects.get(user=request.user)
        try:
            strava.get_activities(strava_auth)
            return render(request, 'strava_import/strava_import.html')
        except Exception as e:
            print("Exception: ", e)
    else:
        print("StravaAuth object does not exist")

    return render(request, 'strava_import/strava_auth.html',
                  {'authorization_url': strava.get_authorization()})
