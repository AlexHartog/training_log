from datetime import date

from django import forms
from django.forms import ModelForm

from .models import TrainingSession


class SessionForm(ModelForm):
    required_css_class = 'required'

    class Meta:
        model = TrainingSession
        fields = [
            'discipline', 'date', 'total_duration', 'distance',
            'training_type', 'notes'
        ]
        labels = {
            'total_duration': 'Duration (minutes)',
            'distance': 'Distance (km)',
        }
        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date', 'value': date.today()}),
        }
