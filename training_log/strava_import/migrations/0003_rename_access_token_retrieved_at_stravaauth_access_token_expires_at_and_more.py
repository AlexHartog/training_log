# Generated by Django 4.2.3 on 2023-08-03 09:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strava_import", "0002_stravaauth_access_token_retrieved_at"),
    ]

    operations = [
        migrations.RenameField(
            model_name="stravaauth",
            old_name="access_token_retrieved_at",
            new_name="access_token_expires_at",
        ),
        migrations.AddField(
            model_name="stravaauth",
            name="refresh_token",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="stravaauth",
            name="access_token",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
