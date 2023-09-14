# Generated by Django 4.2.4 on 2023-09-14 07:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strava_import", "0010_stravasubscription_stravauser"),
    ]

    operations = [
        migrations.AddField(
            model_name="stravasubscription",
            name="strava_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="stravasubscription",
            name="callback_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="stravasubscription",
            name="state",
            field=models.CharField(
                choices=[("AC", "Active"), ("VA", "Validated"), ("CR", "Created")],
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name="stravasubscription",
            name="verify_token",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
