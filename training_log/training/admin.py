from django.contrib import admin

from .models import Discipline, Training, TrainingType

admin.site.register(Discipline)
admin.site.register(Training)
admin.site.register(TrainingType)
