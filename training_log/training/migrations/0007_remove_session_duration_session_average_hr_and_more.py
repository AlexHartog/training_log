# Generated by Django 4.2.3 on 2023-08-03 08:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0006_alter_session_duration"),
    ]

    operations = [
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
    ]
