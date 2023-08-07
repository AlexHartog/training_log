from django.contrib import admin

from .models import StravaAuth, StravaTypeMapping

# Register your models here.
admin.site.register(StravaAuth)
admin.site.register(StravaTypeMapping)
