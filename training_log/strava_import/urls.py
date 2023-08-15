from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="strava-index"),
    path("import_data", views.get_strava_data, name="strava-data"),
    path("save_auth", views.save_strava_auth, name="save-strava-auth"),
    path("strava_auth", views.strava_auth, name="strava-auth"),
    path(
        "auto_import/<int:enable>/", views.enable_auto_import, name="strava-auto-import"
    ),
]
