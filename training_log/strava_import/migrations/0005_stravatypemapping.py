# Generated by Django 4.2.3 on 2023-08-07 13:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0010_alter_session_strava_id"),
        ("strava_import", "0004_stravaauth_auto_import"),
    ]

    operations = [
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
                        on_delete=django.db.models.deletion.CASCADE,
                        to="training.discipline",
                    ),
                ),
            ],
        ),
    ]
