# Generated by Django 4.2.3 on 2023-08-09 12:59

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('training', '0010_alter_session_strava_id'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Session',
            new_name='TrainingSession',
        ),
    ]
