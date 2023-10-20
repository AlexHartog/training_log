from datetime import datetime

import mock
import pandas as pd
from dateutil.rrule import DAILY, rrule
from django.test import TestCase
from scipy import constants

from training.graphs import DEFAULT_START_DATE, GraphsData
from training.tests.test_data.stats_tests_data import StatsTestData


class TrainingStatsTest(TestCase):
    def setUp(self):
        self.datetime_to_test = datetime(2023, 9, 8)

        self.test_data = StatsTestData(date=self.datetime_to_test)
        self.test_data.load_graph_data()

        with mock.patch('training.graphs.datetime') as mock_datetime:
            mock_datetime.today.return_value = self.datetime_to_test
            self.graph_data = GraphsData()

    def get_x_values(self, graph_name):
        return self.graph_data.data[graph_name][self.test_data.test_user.capitalize()][
            "x_values"
        ]

    def get_values(self, graph_name):
        return self.graph_data.data[graph_name][self.test_data.test_user.capitalize()][
            "y_values"
        ]

    def test_x_axis_total_hours_trained(self):
        """Test if total time trained is calculated correctly."""
        x_values_test_user = self.get_x_values("total_hours_trained")

        datelist = [
            x.isoformat()
            for x in pd.date_range(DEFAULT_START_DATE, self.datetime_to_test).tolist()
        ]

        self.assertTrue(x_values_test_user, datelist)

    def test_values_total_hours_trained(self):
        y_values_test_user = self.get_values("total_hours_trained")

        self.assertEqual(y_values_test_user[5], 0)
        self.assertEqual(y_values_test_user[121], 25200 / constants.hour)
        self.assertEqual(y_values_test_user[130], 37810 / constants.hour)

    def test_x_axis_weekly_hours_trained(self):
        x_values_test_user = self.get_x_values("weekly_hours_trained")

        expected_week_numbers = sorted(list(
            set(
                date.isocalendar()[1]
                for date in rrule(
                    DAILY, dtstart=DEFAULT_START_DATE, until=self.datetime_to_test
                )
            )
        ))

        self.assertEquals(x_values_test_user, expected_week_numbers)

    def test_values_weekly_hours_trained(self):
        values_test_user = self.get_values("weekly_hours_trained")

        self.assertEqual(values_test_user[0], 0)
        self.assertEqual(values_test_user[14], 5)
        self.assertEqual(values_test_user[18], 7110 / constants.hour)
