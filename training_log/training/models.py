from django.db import models
from django.contrib.auth.models import User


class Discipline(models.Model):
    """A discipline that can be practiced."""
    name = models.CharField(max_length=200)

    def __str__(self):
        """Return a string representation of the model."""
        return self.name


class TrainingType(models.Model):
    """A type of training."""
    name = models.CharField(max_length=200)

    def __str__(self):
        """Return a string representation of the model."""
        return self.name


class Training(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    date = models.DateField()
    duration = models.DurationField()
    distance = models.FloatField()
    training_type = models.ForeignKey(TrainingType, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return f"{self.user.name} did {self.discipline} on {self.date}"
