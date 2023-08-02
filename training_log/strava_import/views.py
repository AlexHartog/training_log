import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

from .models import StravaAuth
import strava


@login_required(login_url=reverse_lazy('login'))
def get_strava_data(request):
    if request.method == 'GET' and 'code' in request.GET:
        strava.save_auth(request)

    if StravaAuth.objects.filter(user=request.user).exists():
        strava_auth = StravaAuth.objects.get(user=request.user)
        print("StravaAuth object exists")
        print(strava_auth)
        activities = strava.get_activities(strava_auth.access_token)
        print("We've imported ", len(activities), " activities")
        for activity in activities:
            print("Activity: ", activity)
            json_formatted_str = json.dumps(activity, indent=2)

            print(json_formatted_str)
        return render(request, 'strava_import/strava_import.html')

    print("StravaAuth object does not exist")
    return render(request, 'strava_import/strava_auth.html',
                  {'authorization_url': strava.get_access_token()})
