import csv
import json
import logging
import webcolors
from datetime import datetime, timedelta

import pandas as pd
from django.contrib.auth.models import User
from django.db.models import F, Q
from training.models import TrainingSession

logger = logging.getLogger(__name__)

DEFAULT_START_DATE = datetime(2023, 5, 1)
DISCIPLINE_COLORS = {
    "Running": "green",
    "Cycling": "blue",
    "Swimming": "orange",
}


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
        self.discipline_colors = {
            discipline: self.color_name_to_hex(color)
            for discipline, color in DISCIPLINE_COLORS.items()
        }
        self.training_sessions = pd.DataFrame()

        self.get_training_sessions()
        self.preprocess_session_data()

        self.load_graph_data()

    def load_graph_data(self):
        """Load all graph data."""
        disciplines = self.training_sessions["discipline_name"].unique()
        self.create_total_trained_data_graph()
        self.create_total_trained_data_graph(disciplines=disciplines)
        self.create_weekly_trained_data_graph()
        self.create_weekly_trained_data_graph(disciplines=disciplines)

    def get_training_sessions(self):
        """Get the training sessions ot be used in the stats."""
        filter_condition = Q(date__gte=self.start_date) & Q(excluded=False)

        django_training_sessions = TrainingSession.objects.filter(
            filter_condition
        ).values(user_name=F("user__username"), discipline_name=F("discipline__name"))

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

    def get_user_data(self, username, discipline=None):
        """Get data for a user and an optional discipline."""
        user_data = self.training_sessions.loc[
            self.training_sessions["user_name"] == username
        ]

        if discipline:
            user_data = user_data.loc[user_data["discipline_name"] == discipline]

        return user_data

    def add_graph_data(self, graph_name, dates, values, label, color=None):
        """Add graph data to the data dictionary."""
        self.data.setdefault(graph_name, {})[label] = json.dumps(
            {
                "x_values": dates,
                "y_values": values,
                "color": color,
            }
        )

    def get_week_numbers(self):
        """Get the week numbers for the training sessions."""
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

    def get_total_data(self, user, discipline=None):
        """Get the total trained data for a user and optional discipline."""
        total_trained_data = self.training_sessions.fillna(0)

        user_data = total_trained_data.loc[
            total_trained_data["user_name"] == user.username
        ]

        if discipline:
            user_data = user_data.loc[user_data["discipline_name"] == discipline]

        trained_data = user_data.groupby("date").moving_duration.sum()
        trained_data.index = pd.DatetimeIndex(trained_data.index)
        trained_data = trained_data.reindex(self.datelist, fill_value=0)

        dates = [pd.to_datetime(x).isoformat() for x in trained_data.index.values]
        values = trained_data.transform(pd.Series.cumsum).values.tolist()

        return dates, values

    def create_total_trained_data_graph(self, disciplines=None):
        """Get the total hours trained as a cumulative sum per user."""

        if disciplines is None:
            graph_name = "total_hours_trained"
        else:
            graph_name = "total_hours_trained_disciplines"

        for discipline in [None] if disciplines is None else disciplines:
            user_count = 0
            for user in self.users:
                if discipline:
                    graph_color = self.get_color(discipline, user_count)
                    graph_label = f"{user.username.capitalize()} - {discipline}"
                else:
                    graph_label = f"{user.username.capitalize()}"
                    graph_color = None

                dates, values = self.get_total_data(user, discipline)

                logger.info(f"Adding graph data")
                self.add_graph_data(
                    graph_name,
                    dates,
                    values,
                    graph_label,
                    color=graph_color,
                )
                user_count += 1

        self.settings[graph_name] = {
            "y_label": "Hours trained",
            "title": f"Total hours trained {'per discipline ' if disciplines is not None else ''}",
        }

    @staticmethod
    def adjust_color(hex_color, adjustment_factor):
        """Adjust a color by a factor."""
        hex_color = hex_color.lstrip("#")
        rgb = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]

        for i in range(3):
            rgb[i] = round(rgb[i] * adjustment_factor)
            rgb[i] = max(0, min(255, rgb[i]))

        new_hex_color = "#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2])
        return new_hex_color

    def get_color(self, discipline, user_count):
        """Get a color for a discipline and user."""
        return self.adjust_color(
            self.discipline_colors[discipline],
            0.8 + user_count / (len(self.users) - 1),
        )

    @staticmethod
    def color_name_to_hex(color_name):
        """Convert a color name to a hex color."""
        try:
            return webcolors.name_to_hex(color_name)
        except ValueError:
            return None

    def get_weekly_data(self, user, discipline=None):
        """Get data totals per week."""
        # TODO: How to manage different years, include year to weeknumber
        trained_data = (
            self.get_user_data(user.username, discipline=discipline)
            .groupby(["week_number"])
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

        if discipline:
            _, current_weeknumber, _ = datetime.now().isocalendar()
            trained_data = trained_data.loc[
                trained_data["week"] >= current_weeknumber - 12
            ]

        values = trained_data["moving_duration"].to_list()
        dates = trained_data["week"].to_list()

        return values, dates

    def create_weekly_trained_data_graph(self, disciplines=None):
        """Get weekly hours trained per user and optionally per discipline."""

        graph_name = (
            f"weekly_hours_trained{'_disciplines' if disciplines is not None else ''}"
        )

        for discipline in [None] if disciplines is None else disciplines:
            user_count = 0
            for user in self.users:
                if discipline:
                    graph_color = self.get_color(discipline, user_count)
                    graph_label = f"{user.username.capitalize()} - {discipline}"
                else:
                    graph_label = f"{user.username.capitalize()}"
                    graph_color = None

                values, dates = self.get_weekly_data(user, discipline)

                self.add_graph_data(
                    graph_name,
                    dates,
                    values,
                    graph_label,
                    color=graph_color,
                )

                user_count += 1

        self.settings[graph_name] = {
            "y_label": "Hours trained",
            "title": f"Weekly hours trained { 'per discipline' if disciplines is not None else ''}",
            "chart_type": "bar",
            "x_type": "category",
            "x_label": "Week Number",
        }
