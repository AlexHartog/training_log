# Generated by Django 4.2.3 on 2023-08-03 09:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0009_alter_session_training_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="session",
            name="strava_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
