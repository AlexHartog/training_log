from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from training.models import Discipline, SessionZones, TrainingSession


class TrainingSessionTest(TestCase):
    def create_discipline(self, name="test"):
        return Discipline.objects.create(name=name)

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

    def test_session_creation(self):
        session = self.create_session()

        self.assertTrue(isinstance(session, TrainingSession))

        session_string = (
            f"{session.user.username.capitalize()} did "
            f"{session.discipline} on {session.date} "
            f"({session.formatted_distance} in {session.formatted_duration})"
        )

        self.assertEqual(str(session), session_string)

    def test_discipline_creation(self):
        discipline = self.create_discipline(name="test")

        self.assertTrue(isinstance(discipline, Discipline))
        self.assertEqual(discipline.__str__(), discipline.name)


class SessionZonesTest(TestCase):
    def create_training_session(self):
        return TrainingSession.objects.create(
            user=User.objects.create(username="testuser"),
            discipline=Discipline.objects.create(name="test"),
            date=datetime.now(),
        )

    def create_session_zones(
        self,
        resource_state=2,
        points=50,
        sensor_based=False,
        zone_type="HR",
        score=60,
        custom_zones=False,
    ):
        return SessionZones.objects.create(
            session=self.create_training_session(),
            resource_state=resource_state,
            points=points,
            sensor_based=sensor_based,
            zone_type=zone_type,
            score=score,
            custom_zones=custom_zones,
        )

    def test_session_zones_creation(self):
        session_zones = self.create_session_zones(zone_type="HR")
        self.assertEqual(session_zones.zone_type, "HR")
