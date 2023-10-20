# Generated by Django 4.2.4 on 2023-09-18 12:13

from django.db import migrations


def covnert_session_zone_type(apps, schema_editor):
    SessionZones = apps.get_model("training", "SessionZones")

    choice_mapping = {
        "hr": "HR",
        "pw": "PW",
        "pc": "PC",
    }

    for session_zone in SessionZones.objects.all():
        old_type = session_zone.zone_type

        if old_type not in choice_mapping.keys():
            continue

        new_type = choice_mapping[old_type]
        if new_type is not None:
            session_zone.zone_type = new_type
            session_zone.save()
        else:
            session_zone.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0017_alter_sessionzones_zone_type"),
    ]

    operations = [
        migrations.RunPython(covnert_session_zone_type),
    ]