from django.urls import path

from . import views

urlpatterns = [
    path('', views.get_strava_data, name='strava-data'),
    path('auth', views.strava_auth, name='strava-auth'),
]
