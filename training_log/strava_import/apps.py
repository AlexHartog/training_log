from django.apps import AppConfig
import os


class StravaImportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "strava_import"

    def ready(self):
        from . import strava

        if os.environ.get("RUN_MAIN"):
            print("We can now run the sync")
            # TODO: Should we check and request subscription?
            # strava.subscribe_if_needed()
