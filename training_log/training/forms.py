from datetime import date

from django import forms
from django.forms import ModelForm

from .models import Session


class SessionForm(ModelForm):
    required_css_class = 'required'

    class Meta:
        model = Session
        fields = [
            'discipline', 'date', 'duration', 'distance',
            'training_type', 'notes'
        ]
        labels = {
            'duration': 'Duration (minutes)',
            'distance': 'Distance (km)',
        }
        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date', 'value': date.today()}),
        }
