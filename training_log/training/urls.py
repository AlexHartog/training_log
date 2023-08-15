from django.urls import path

from . import views
from .views import SessionView, SessionList


urlpatterns = [
    path("", views.index, name="index"),
    path("new_session/", views.new_session, name="new-session"),
    path("sessions", SessionList.as_view(), name="session-list"),
    path("session/<int:pk>", SessionView.as_view(), name="session-detail"),
    path("all_stats/", views.all_stats, name="all-stats"),
]
