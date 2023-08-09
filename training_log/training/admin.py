from django.contrib import admin

from .models import Discipline, TrainingSession, TrainingType

admin.site.register(Discipline)
admin.site.register(TrainingSession)
admin.site.register(TrainingType)
