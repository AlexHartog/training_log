from django.shortcuts import render

from .models import Training


def index(request):
    """The home page for Training Log."""
    return render(request, 'training/index.html')
