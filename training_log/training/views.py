import datetime
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from strava_import.models import StravaUser

from . import maps, stats
from .forms import SessionForm
from .graphs import GraphsData
from .models import MunicipalityVisits, SessionZones, TrainingSession

logger = logging.getLogger(__name__)


def index(request):
    """The home page for Training Log."""
    return redirect("all-stats")


class Register(CreateView):
    """View to register a new user."""

    template_name = "registration/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("register-success")

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.success_url)


class SessionList(ListView):
    """A view to show all sessions by a particular user."""

    context_object_name = "all_sessions"

    def get_queryset(self):
        username = self.kwargs.get("username")

        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise Http404("User does not exist")

        return TrainingSession.objects.filter(user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get("username")

        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise Http404("User does not exist")

        try:
            strava_user = StravaUser.objects.get(user=user)
            context["strava_user"] = strava_user
        except StravaUser.DoesNotExist:
            logger.warning(f"Strava User does not exist for {user}")

        return context


class SessionView(DetailView):
    """View to show a single training session."""

    context_object_name = "session"
    model = TrainingSession

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_zones = SessionZones.objects.filter(session=self.object)
        context["session_zones"] = session_zones

        return context


@login_required(login_url=reverse_lazy("login"))
def new_session(request):
    """View to create a new training session."""
    submitted = False
    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            try:
                session.user = request.user
            except Exception:
                pass
            if session.moving_duration:
                session.moving_duration *= 60
            session.save()
            return HttpResponseRedirect("?submitted=True")
    else:
        form = SessionForm()
        if "submitted" in request.GET:
            submitted = True

    return render(
        request, "training/new_session.html", {"form": form, "submitted": submitted}
    )


def all_stats_total(request):
    """Show stats for all users."""
    return redirect("all-stats", period="all")


def all_stats(request, period):
    """Show stats for all users."""
    try:
        period_enum = stats.StatsPeriod.get_enum_from_string(period)
    except ValueError:
        return redirect("all-stats", period="all")

    player_stats = stats.AllPlayerStats(period_enum)
    context = {
        "players": player_stats.players,
        "stats": player_stats.stats,
        "period": str(period_enum),
        "period_options": stats.StatsPeriod.options(),
    }

    return render(request, "training/all_stats.html", context=context)


def graphs(request):
    """Create graphs with training data."""
    training_data = TrainingSession.objects.filter(moving_duration__gt=0).all()
    training_dates = [
        date.isoformat() for date in list(training_data.values_list("date", flat=True))
    ]

    graphs_data = GraphsData()
    training_hours = list(training_data.values_list("moving_duration", flat=True))

    return render(
        request,
        "training/graphs.html",
        {
            "labels": training_dates,
            "data": training_hours,
            "graph_data": graphs_data.data,
            "settings": graphs_data.settings,
        },
    )


def training_map(request):
    """Create a form for loading a training map."""
    users = User.objects.all()
    disciplines = MunicipalityVisits.objects.values_list(
        "training_session__discipline__name", flat=True
    ).distinct()

    context = {
        "users": users,
        "disciplines": disciplines,
        "start_date": stats.DEFAULT_START_DATE,
        "current_date": datetime.date.today(),
    }

    return render(request, "training/training_map.html", context=context)


def load_map(request):
    """Load the actual training map based on selected values."""
    selected_users = request.POST.getlist("user_id")
    disciplines = request.POST.getlist("discipline")
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    training_map = maps.TrainingMap()
    context = {
        "map": training_map.create_training_map(
            selected_users, disciplines, start_date, end_date
        )
    }
    logger.info("Rendering")
    return render(request, "training/folium_map.html", context)


def delete_session(request):
    """Delete a session based on post data."""
    if request.method != "POST":
        raise Http404("Method not allowed")

    session_id = int(request.POST.get("session_id"))
    user = request.POST.get("user")

    logger.info(f"Deleting session {session_id} for user {user}")

    try:
        session = TrainingSession.objects.get(pk=session_id)
        session.delete()
        messages.success(request, "Session deleted")
    except TrainingSession.DoesNotExist:
        messages.error(request, "The session that was being deleted does not exist")

    return redirect("session-list", username=user)


def exclude_session(request):
    """Exclude a session based on post data."""
    if request.method != "POST":
        raise Http404("Method not allowed")

    session_id = int(request.POST.get("session_id"))
    excluded = request.POST.get("excluded")

    logger.info(f"Setting session {session_id} to {excluded}")

    try:
        session = TrainingSession.objects.get(pk=session_id)
        session.excluded = excluded
        session.save()
    except TrainingSession.DoesNotExist:
        raise Http404("The session that was being excluded does not exist")

    return redirect("session-detail", pk=session_id)
