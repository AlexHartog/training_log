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
        self.data = {}
        self.settings = {}
        self.week_numbers = None
        self.start_date = DEFAULT_START_DATE
        self.datelist = pd.date_range(self.start_date, datetime.today())
        self.get_week_numbers()
        self.users = User.objects.all()
        self.training_sessions = pd.DataFrame()

        self.get_training_sessions()
        self.preprocess_session_data()

        self.load_graph_data()

    def load_graph_data(self):
        """Load all graph data."""
        self.get_total_trained_data()
        self.get_weekly_hours_data()

    def get_training_sessions(self):
        """Get the training sessions ot be used in the stats."""
        filter_condition = Q(date__gte=self.start_date)

        django_training_sessions = TrainingSession.objects.filter(
            filter_condition
        ).values(user_name=F("user__username"))

        self.training_sessions = pd.DataFrame.from_records(
            django_training_sessions.values()
        )

    def preprocess_session_data(self):
        """Adjust training data so that it can more easily be used to create graphs."""

        # Convert durations to hours
        self.training_sessions["moving_duration"] = (
            self.training_sessions["moving_duration"] / 3600
        )
        self.training_sessions["total_duration"] = (
            self.training_sessions["total_duration"] / 3600
        )

        # Convert date to a proper datetime
        self.training_sessions["date"] = pd.to_datetime(self.training_sessions["date"])

        # Add a week number to the data
        self.training_sessions["week_number"] = (
            self.training_sessions["date"].dt.isocalendar().week
        )

    def get_user_data(self, username):
        return self.training_sessions.loc[
            self.training_sessions["user_name"] == username
        ]

    def add_graph_data(self, graph_name, dates, values, label):
        self.data.setdefault(graph_name, []).append(
            {
                "x_values": dates,
                "y_values": values,
                "label": label,
            }
        )

    def get_week_numbers(self):
        self.week_numbers = pd.DataFrame(
            data=self.datelist.to_series().dt.isocalendar().week.unique(),
            columns=["week"],
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
        graph_name = "total_hours_trained"

        total_trained_data = self.training_sessions.fillna(0)
        total_trained_data["moving_duration"] = (
            total_trained_data["moving_duration"] / 3600
        )
        for user in self.users:
            user_data = total_trained_data.loc[
                total_trained_data["user_name"] == user.username
            ]

            trained_data = user_data.groupby("date").moving_duration.sum()
            trained_data.index = pd.DatetimeIndex(trained_data.index)
            trained_data = trained_data.reindex(self.datelist, fill_value=0)

            values = trained_data.transform(pd.Series.cumsum).values.tolist()
            dates = [pd.to_datetime(x).isoformat() for x in trained_data.index.values]

            self.add_graph_data(graph_name, dates, values, user.username.capitalize())

            self.settings[graph_name] = {
                "y_label": "Hours trained",
                "title": "Total hours trained",
            }

    def get_weekly_hours_data(self):
        """Get weekly hours trained per user."""
        graph_name = "weekly_hours_trained"

        total_trained_data = self.training_sessions.fillna(0)
        total_trained_data["moving_duration"] = (
            total_trained_data["moving_duration"] / 3600
        )
        total_trained_data["date"] = pd.to_datetime(total_trained_data["date"])
        total_trained_data["week_number"] = (
            total_trained_data["date"].dt.isocalendar().week
        )

        for user in self.users:
            trained_data = (
                self.get_user_data(user.username)
                .groupby("week_number")
                .moving_duration.sum()
            )

            trained_data = (
                trained_data.reset_index()
                .merge(
                    self.week_numbers,
                    how="right",
                    left_on="week_number",
                    right_on="week",
                )
                .fillna(0)
            )

            values = trained_data["moving_duration"].to_list()
            dates = trained_data["week"].to_list()

            self.add_graph_data(graph_name, dates, values, user.username.capitalize())

            self.settings[graph_name] = {
                "y_label": "Hours trained",
                "title": "Weekly hours trained",
                "chart_type": "bar",
                "x_type": "category",
                "x_label": "Week Number",
            }
