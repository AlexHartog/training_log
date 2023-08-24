from datetime import date

from django import forms
from django.forms import ModelForm

from .models import TrainingSession


class SessionForm(ModelForm):
    """A form to create a new training session."""

    required_css_class = "required"

    class Meta:
        """The meta class."""

        model = TrainingSession
        fields = [
            "discipline",
            "date",
            "moving_duration",
            "distance",
            "training_type",
            "notes",
        ]
        labels = {
            "moving_duration": "Duration (minutes)",
            "distance": "Distance (km)",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "value": date.today()}),
        }
