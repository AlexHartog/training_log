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
    path("start_time_sync", views.sync_start_times, name="strava-start-time-sync"),
    path(
        "strava_subscribe/<int:subscribe>/",
        views.subscribe_strava,
        name="strava-subscribe",
    ),
    path("activity_feed", views.activity_feed, name="strava-activity-feed"),
    path("strava_admin", views.strava_admin, name="strava-admin"),
    path(
        "admin_import_data/",
        views.admin_import_data,
        name="admin-import-data",
    ),
    path(
        "admin_athlete_update",
        views.admin_athlete_update,
        name="admin-athlete-update",
    ),
    path("parse_data", views.admin_parse_data, name="parse-data"),
]
