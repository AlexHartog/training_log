# Generated by Django 4.2.4 on 2023-09-15 07:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    replaces = [
        ("training", "0001_initial"),
        ("training", "0002_rename_training_session"),
        ("training", "0003_alter_session_duration"),
        ("training", "0004_auto_20230802_1120"),
        ("training", "0005_auto_20230802_1130"),
        ("training", "0006_alter_session_duration"),
        ("training", "0007_remove_session_duration_session_average_hr_and_more"),
        ("training", "0008_session_strava_id"),
        ("training", "0009_alter_session_training_type"),
        ("training", "0010_alter_session_strava_id"),
        ("training", "0011_rename_session_trainingsession"),
        ("training", "0012_trainingsession_start_date"),
        ("training", "0013_alter_trainingsession_options"),
        ("training", "0014_sessionzones_zone"),
        ("training", "0015_alter_sessionzones_custom_zones"),
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Discipline",
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
                ("name", models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name="TrainingType",
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
                ("name", models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name="Session",
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
                ("date", models.DateField()),
                ("duration_old", models.DurationField()),
                ("distance", models.FloatField()),
                ("notes", models.TextField(blank=True)),
                ("date_added", models.DateTimeField(auto_now_add=True)),
                (
                    "discipline",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="training.discipline",
                    ),
                ),
                (
                    "training_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="training.trainingtype",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("duration", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.RemoveField(
            model_name="session",
            name="duration_old",
        ),
        migrations.RemoveField(
            model_name="session",
            name="duration",
        ),
        migrations.AddField(
            model_name="session",
            name="average_hr",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="session",
            name="average_speed",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="session",
            name="max_hr",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="session",
            name="max_speed",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="session",
            name="moving_duration",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="session",
            name="strava_updated",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="session",
            name="total_duration",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="session",
            name="distance",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="session",
            name="training_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="training.trainingtype",
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="strava_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.RenameModel(
            old_name="Session",
            new_name="TrainingSession",
        ),
        migrations.AddField(
            model_name="trainingsession",
            name="start_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterModelOptions(
            name="trainingsession",
            options={"ordering": ["-date"]},
        ),
        migrations.CreateModel(
            name="SessionZones",
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
                ("resource_state", models.IntegerField(blank=True, null=True)),
                ("points", models.FloatField(blank=True, null=True)),
                ("sensor_based", models.BooleanField(default=True)),
                ("zone_type", models.CharField()),
                ("score", models.IntegerField(blank=True, null=True)),
                ("custom_zones", models.BooleanField(blank=True, null=True)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="training.trainingsession",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Zone",
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
                ("min", models.FloatField()),
                ("max", models.FloatField()),
                ("time", models.IntegerField()),
                (
                    "session_zones",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="training.sessionzones",
                    ),
                ),
            ],
        ),
    ]
