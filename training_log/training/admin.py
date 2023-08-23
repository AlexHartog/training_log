from django.contrib import admin

from .models import Discipline, TrainingSession, TrainingType


class TrainingSessionAdmin(admin.ModelAdmin):
    list_filter = ["date", "discipline", "user"]


admin.site.register(Discipline)
admin.site.register(TrainingSession, TrainingSessionAdmin)
admin.site.register(TrainingType)
