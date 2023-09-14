from django.contrib import admin

from .models import (Discipline, SessionZones, TrainingSession, TrainingType,
                     Zone)


class ZonesInline(admin.TabularInline):
    model = Zone

    extra = 0


class SessionZonesInline(admin.StackedInline):
    model = SessionZones

    extra = 0


class SessionZonesAdmin(admin.ModelAdmin):
    inlines = [
        ZonesInline,
    ]


class TrainingSessionAdmin(admin.ModelAdmin):
    list_filter = ["date", "discipline", "user"]

    inlines = [
        SessionZonesInline,
    ]


admin.site.register(Discipline)
admin.site.register(TrainingSession, TrainingSessionAdmin)
admin.site.register(TrainingType)
admin.site.register(SessionZones, SessionZonesAdmin)
