# Generated by Django 4.2.4 on 2023-09-11 13:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strava_import", "0007_stravaactivityimport"),
    ]

    operations = [
        migrations.AddField(
            model_name="stravaactivityimport",
            name="imported_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
