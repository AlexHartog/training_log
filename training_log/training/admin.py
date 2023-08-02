from django.contrib import admin

from .models import Discipline, Session, TrainingType

admin.site.register(Discipline)
admin.site.register(Session)
admin.site.register(TrainingType)
