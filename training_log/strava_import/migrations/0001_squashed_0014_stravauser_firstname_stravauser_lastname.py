# Generated by Django 4.2.4 on 2023-09-15 07:45

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    replaces = [
        ("strava_import", "0001_initial"),
        ("strava_import", "0002_stravaauth_access_token_retrieved_at"),
        (
            "strava_import",
            "0003_rename_access_token_retrieved_at_stravaauth_access_token_expires_at_and_more",
        ),
        ("strava_import", "0004_stravaauth_auto_import"),
        ("strava_import", "0005_stravatypemapping"),
        ("strava_import", "0006_alter_stravatypemapping_discipline"),
        ("strava_import", "0007_stravaactivityimport"),
        ("strava_import", "0008_stravaactivityimport_imported_at"),
        ("strava_import", "0009_stravaratelimit"),
        ("strava_import", "0010_stravasubscription_stravauser"),
        ("strava_import", "0011_stravasubscription_strava_id_and_more"),
        ("strava_import", "0012_stravauser_city_stravauser_premium_and_more"),
        ("strava_import", "0013_rename_resource_status_stravauser_resource_state"),
        ("strava_import", "0014_stravauser_firstname_stravauser_lastname"),
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("training", "0010_alter_session_strava_id"),
        ("training", "0011_rename_session_trainingsession"),
    ]

    operations = [
        migrations.CreateModel(
            name="StravaAuth",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=200)),
                ("access_token", models.CharField(blank=True, max_length=200)),
                (
                    "scope",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(blank=True, max_length=200),
                        size=None,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "access_token_expires_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("refresh_token", models.CharField(blank=True, max_length=200)),
                ("auto_import", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="StravaTypeMapping",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("strava_type", models.CharField(max_length=200)),
                (
                    "discipline",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="training.discipline",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StravaActivityImport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("strava_id", models.BigIntegerField()),
                ("type", models.CharField(max_length=200)),
                ("json_data", models.JSONField()),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("imported_at", models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="StravaRateLimit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("short_limit", models.IntegerField()),
                ("daily_limit", models.IntegerField()),
                ("short_limit_usage", models.IntegerField()),
                ("daily_limit_usage", models.IntegerField()),
                ("updated_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="StravaSubscription",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("enabled", models.BooleanField(default=False)),
                ("callback_url", models.URLField(blank=True, null=True)),
                (
                    "verify_token",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("AC", "Active"),
                            ("VA", "Validated"),
                            ("CR", "Created"),
                        ],
                        max_length=2,
                    ),
                ),
                ("strava_id", models.BigIntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="StravaUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("strava_id", models.BigIntegerField()),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("city", models.CharField(blank=True, max_length=200, null=True)),
                ("premium", models.BooleanField(blank=True, null=True)),
                ("resource_state", models.IntegerField(blank=True, null=True)),
                ("sex", models.CharField(blank=True, max_length=200, null=True)),
                ("summit", models.BooleanField(blank=True, null=True)),
                ("username", models.CharField(blank=True, max_length=200, null=True)),
                ("weight", models.FloatField(blank=True, null=True)),
                ("firstname", models.CharField(blank=True, max_length=200, null=True)),
                ("lastname", models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
    ]