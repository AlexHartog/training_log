# Generated by Django 4.2.3 on 2023-08-02 09:19

from django.db import migrations, models

def migrate_time_to_positive_int(apps, schema_editor):
    MyModel = apps.get_model('training', 'session')

    for mm in MyModel.objects.all():
        print("MM: ", mm)
        duration_old = mm.duration_old
        duration_new = duration_old.total_seconds() / 60
        mm.duration = duration_new
        mm.save()

class Migration(migrations.Migration):

    dependencies = [
        ('training', '0002_rename_training_session'),
    ]

    operations = [
        migrations.RenameField(
            model_name='session',
            old_name='duration',
            new_name='duration_old',
        ),
        migrations.AddField(
            model_name='session',
            name='duration',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(migrate_time_to_positive_int),
        migrations.RemoveField(
            model_name='session',
            name='duration_old',
        )
    ]