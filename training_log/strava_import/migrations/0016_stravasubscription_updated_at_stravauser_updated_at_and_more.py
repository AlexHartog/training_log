# Generated by Django 4.2.4 on 2023-09-15 08:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strava_import", "0015_stravauser_country_stravauser_profile_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="stravasubscription",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="stravauser",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="stravaratelimit",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
