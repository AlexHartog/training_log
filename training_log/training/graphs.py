import csv
from datetime import datetime

import pandas as pd
from django.contrib.auth.models import User
from django.db.models import F, Q
from training.models import TrainingSession

DEFAULT_START_DATE = datetime(2023, 5, 1)


class GraphsData:
    """This class generates data to be used by graphs."""

    def __init__(self):
        self.data = []
        self.settings = {}
        self.start_date = DEFAULT_START_DATE
        self.datelist = pd.date_range(self.start_date, datetime.today())
        self.users = User.objects.all()
        self.training_sessions = pd.DataFrame()
        self.get_training_sessions()
        self.total_trained_data = []
        self.get_total_trained_data()
        # self.write_csv()

    def get_training_sessions(self):
        """Get the training sessions ot be used in the stats."""
        filter_condition = Q(date__gte=self.start_date)

        django_training_sessions = TrainingSession.objects.filter(
            filter_condition
        ).values(user_name=F("user__username"))

        self.training_sessions = pd.DataFrame.from_records(
            django_training_sessions.values()
        )

    def write_csv(self):
        """Write the training sessions to a csv file. Intended for debugging."""
        field_names = [field.name for field in TrainingSession._meta.get_fields()]

        with open("training_sessions.csv", "w") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(field_names)

            for session in self.training_sessions:
                writer.writerow([getattr(session, field) for field in field_names])

    def get_total_trained_data(self):
        """Get the total hours trained as a cumulative sum per user."""
        self.total_trained_data = self.training_sessions.fillna(0)
        self.total_trained_data["moving_duration"] = (
            self.total_trained_data["moving_duration"] / 3600
        )
        for user in self.users:
            user_data = self.total_trained_data.loc[
                self.total_trained_data["user_name"] == user.username
            ]

            trained_data = user_data.groupby("date").moving_duration.sum()
            trained_data.index = pd.DatetimeIndex(trained_data.index)
            trained_data = trained_data.reindex(self.datelist, fill_value=0)

            values = trained_data.transform(pd.Series.cumsum).values.tolist()
            dates = [pd.to_datetime(x).isoformat() for x in trained_data.index.values]

            self.data.append(
                {"dates": dates, "values": values, "user": user.username.capitalize()}
            )
            self.settings = {"y_label": "Hours trained", "title": "Total hours trained"}
