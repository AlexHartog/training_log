import json

from django.contrib import admin
from django.db import models
from django.forms import widgets
from django_admin_listfilter_dropdown.filters import DropdownFilter

from .models import (StravaActivityImport, StravaAuth, StravaRateLimit,
                     StravaSubscription, StravaTypeMapping, StravaUser)


class PrettyJSONWidget(widgets.Textarea):
    """This class creates a nice format for JSON fields."""

    def format_value(self, value):
        try:
            value = json.dumps(json.loads(value), indent=2, sort_keys=True)
            row_lengths = [len(r) for r in value.split("\n")]
            self.attrs["rows"] = min(max(len(row_lengths) + 2, 10), 30)
            self.attrs["cols"] = min(max(max(row_lengths) + 2, 40), 120)
            return value
        except Exception as e:
            print("Error while formatting JSON: {}".format(e))
            return super(PrettyJSONWidget, self).format_value(value)


class StravaActivityImportAdmin(admin.ModelAdmin):
    list_filter = (("strava_id", DropdownFilter),)
    formfield_overrides = {models.JSONField: {"widget": PrettyJSONWidget}}


class StravaUserAdmin(admin.ModelAdmin):
    readonly_fields = ("updated_at",)


admin.site.register(StravaAuth)
admin.site.register(StravaTypeMapping)
admin.site.register(StravaActivityImport, StravaActivityImportAdmin)
admin.site.register(StravaRateLimit)
admin.site.register(StravaUser, StravaUserAdmin)
admin.site.register(StravaSubscription)
