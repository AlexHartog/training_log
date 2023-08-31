import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from training.forms import SessionForm
from training.models import Discipline, TrainingSession


class SessionFormTest(TestCase):
    # TODO Share this function
    def create_session(
        self,
        username="testuser",
        discipline="test",
        date="2023-08-23",
        distance=100,
        moving_duration=60,
    ):
        return TrainingSession.objects.create(
            user=User.objects.create(username=username),
            discipline=Discipline.objects.create(name=discipline),
            date=date,
            distance=distance,
            moving_duration=moving_duration,
        )

    def test_valid_form(self):
        data = {
            "discipline": Discipline.objects.create(name="test"),
            "date": datetime.date.today(),
        }
        form = SessionForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        data = {
            "date": datetime.date.today(),
        }
        form = SessionForm(data)
        self.assertFalse(form.is_valid())
