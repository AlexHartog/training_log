from django.forms import ModelForm
from .models import Discipline


class QuoteForm(ModelForm):
    required_css_class = 'required'

    class Meta:
        model = Discipline
        fields = ['name']
