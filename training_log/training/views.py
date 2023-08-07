from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import Session
from .forms import SessionForm


def index(request):
    """The home page for Training Log."""
    return render(request, 'training/index.html')


class Register(CreateView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('register-success')

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.success_url)


class SessionList(LoginRequiredMixin, ListView):
    login_url = reverse_lazy('login')
    context_object_name = 'all_sessions'

    def get_queryset(self):
        return Session.objects.filter(user=self.request.user)


class SessionView(LoginRequiredMixin, DetailView):
    login_url = reverse_lazy('login')
    context_object_name = 'session'

    def get_queryset(self):
        session = Session.objects.filter(user=self.request.user)
        return session


@login_required(login_url=reverse_lazy('login'))
def new_session(request):
    submitted = False
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            try:
                session.user = request.user
            except Exception:
                pass
            session.save()
            return HttpResponseRedirect('?submitted=True')
    else:
        form = SessionForm()
        if 'submitted' in request.GET:
            submitted = True

    return render(request, 'training/new_session.html',
                  {'form': form, 'submitted': submitted})
