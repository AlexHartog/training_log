from datetime import datetime, timedelta

from django.test import TestCase
from training.stats import DEFAULT_START_DATE, AllPlayerStats, StatsPeriod
from training.tests.test_data.stats_tests_data import StatsTestData


class TrainingStatsTest(TestCase):
    def setUp(self):
        self.test_data = StatsTestData()
        self.test_data.load_regular_data()

        self.all_player_stats = AllPlayerStats(period=StatsPeriod.ALL)

    @staticmethod
    def convert_formatted_string_to_seconds(formatted_string):
        days_in_seconds = 0
        hours_in_seconds = 0
        minutes_in_seconds = 0
        if "d" in formatted_string:
            days, formatted_string = formatted_string.split("d ")
            days_in_seconds = int(days) * 86400

        if "h" in formatted_string:
            hours, formatted_string = formatted_string.split("h ")
            hours_in_seconds = int(hours) * 3600

        if "m" in formatted_string:
            minutes = formatted_string.rstrip("m")
            minutes_in_seconds = int(minutes) * 60

        return days_in_seconds + hours_in_seconds + minutes_in_seconds

    @staticmethod
    def convert_formatted_string_to_meters(formatted_string):
        without_kms = formatted_string.replace(" km", "")
        kilometers, meters = without_kms.split(".")

        return int(kilometers) * 1000 + int(meters)

    def test_total_time_trained(self):
        """Test if total time trained is calculated correctly."""
        result = self.convert_formatted_string_to_seconds(
            self.all_player_stats.stats["Total time trained"][0]
        )
        expected = self.test_data.total_time_trained

        self.assertEqual(result, expected)

    def test_time_since_last_training(self):
        """Test if time since last training is calculated correctly."""
        result = self.convert_formatted_string_to_seconds(
            self.all_player_stats.stats["Time since last training"][0]
        )
        expected = self.test_data.time_since_last_session

        # Due to rounding and calculation time there could be a one minute
        # difference between expected and result
        self.assertTrue(-61 < result - expected < 61)

    def test_calculate_weekly_hours(self):
        """Test if weekly hours are calculated correctly."""
        result = self.all_player_stats.stats["Average weekly hours"][0]

        weeks_trained = (datetime.now() - DEFAULT_START_DATE).days / 7
        expected = self.all_player_stats.formatted_duration(
            self.test_data.total_time_trained / weeks_trained
        )

        self.assertEqual(result, expected)

    def test_format_timedelta(self):
        """Test if timedelta is formatted correctly."""
        formatted_timedelta = AllPlayerStats.format_timedelta(
            timedelta(days=1, hours=10, minutes=30)
        )
        expected = "1d 10h 30m"

        self.assertEqual(formatted_timedelta, expected)

    def test_format_duration(self):
        """Test if duration is formatted correctly."""
        duration = AllPlayerStats.formatted_duration(duration=4820)
        expected = "1h 20m"

        self.assertEqual(duration, expected)

    def test_format_distance(self):
        """Test if distance is formatted correctly."""
        distance = AllPlayerStats.formatted_distance(distance=12480)
        expected = "12.48 km"

        self.assertEqual(distance, expected)

    def test_number_of_swims(self):
        """Test if number of swims is calculated correctly."""
        self.assertEqual(
            self.all_player_stats.stats["Number of swims"][0],
            self.test_data.number_of_swims,
        )

    def test_number_of_runs(self):
        """Test if number of runs is calculated correctly."""
        self.assertEqual(
            self.all_player_stats.stats["Number of runs"][0],
            self.test_data.number_of_runs,
        )

    def test_number_of_rides(self):
        """Test if number of rides is calculated correctly."""
        self.assertEqual(
            self.all_player_stats.stats["Number of rides"][0],
            self.test_data.number_of_rides,
        )

    def test_total_swimming_time(self):
        """Test if total swimming time is calculated correctly."""
        self.assertEqual(
            self.convert_formatted_string_to_seconds(
                self.all_player_stats.stats["Total swimming time"][0]
            ),
            self.test_data.total_swimming_time,
        )

    def test_total_running_time(self):
        """Test if total running time is calculated correctly."""
        self.assertEqual(
            self.convert_formatted_string_to_seconds(
                self.all_player_stats.stats["Total running time"][0]
            ),
            self.test_data.total_running_time,
        )

    def test_total_cycling_time(self):
        """Test if total cycling time is calculated correctly."""
        self.assertEqual(
            self.convert_formatted_string_to_seconds(
                self.all_player_stats.stats["Total cycling time"][0]
            ),
            self.test_data.total_cycling_time,
        )

    def test_longest_swim_time(self):
        """Test if longest swim time is calculated correctly."""
        self.assertEqual(
            self.convert_formatted_string_to_seconds(
                self.all_player_stats.stats["Longest swim (time)"][0]
            ),
            self.test_data.longest_swim_time,
        )

    def test_longest_run_time(self):
        """Test if longest run time is calculated correctly."""
        self.assertEqual(
            self.convert_formatted_string_to_seconds(
                self.all_player_stats.stats["Longest run (time)"][0]
            ),
            self.test_data.longest_run_time,
        )

    def test_longest_ride_time(self):
        """Test if longest ride time is calculated correctly."""
        self.assertEqual(
            self.convert_formatted_string_to_seconds(
                self.all_player_stats.stats["Longest ride (time)"][0]
            ),
            self.test_data.longest_ride_time,
        )

    def test_longest_swim_distance(self):
        """Test if longest swim distance is calculated correctly."""
        self.assertEqual(
            self.convert_formatted_string_to_meters(
                self.all_player_stats.stats["Longest swim (km)"][0]
            ),
            self.test_data.longest_swim_distance,
        )

    def test_longest_run_distance(self):
        """Test if longest run distance is calculated correctly."""
        self.assertEqual(
            self.convert_formatted_string_to_meters(
                self.all_player_stats.stats["Longest run (km)"][0]
            ),
            self.test_data.longest_run_distance,
        )

    def test_longest_ride_distance(self):
        """Test if longest ride distance is calculated correctly."""
        self.assertEqual(
            self.convert_formatted_string_to_meters(
                self.all_player_stats.stats["Longest ride (km)"][0]
            ),
            self.test_data.longest_ride_distance,
        )

    def test_longest_ride_empty(self):
        """Test if longest ride distance is marked as N/A if no
        rides are in the data."""
        self.assertEqual(self.all_player_stats.stats["Longest ride (time)"][1], "N/A")
        self.assertEqual(self.all_player_stats.stats["Longest ride (km)"][1], "N/A")

    def test_num_long_swims(self):
        """Test if number of long swims is calculated correctly."""
        self.assertEqual(
            self.all_player_stats.stats["Long swims (>60 mins)"][0],
            self.test_data.num_long_swims,
        )

    def test_num_long_runs(self):
        """Test if number of long runs is calculated correctly."""
        self.assertEqual(
            self.all_player_stats.stats["Long runs (>90 mins)"][0],
            self.test_data.num_long_runs,
        )

    def test_num_long_rides(self):
        """Test if number of long rides is calculated correctly."""
        self.assertEqual(
            self.all_player_stats.stats["Long rides (>180 mins)"][0],
            self.test_data.num_long_rides,
        )

    def test_last_week_data(self):
        """Test if last week period leads to correct number of sessions."""
        self.all_player_stats = AllPlayerStats(period=StatsPeriod.WEEK)

        self.assertEqual(len(self.all_player_stats.training_sessions), 2)

    def test_last_month_data(self):
        """Test if last month period leads to correct number of sessions."""
        self.all_player_stats = AllPlayerStats(period=StatsPeriod.MONTH)

        self.assertEqual(len(self.all_player_stats.training_sessions), 6)

    def test_last_three_months_data(self):
        """Test if last three month period leads to correct number of sessions."""
        self.all_player_stats = AllPlayerStats(period=StatsPeriod.THREE_MONTHS)

        self.assertEqual(len(self.all_player_stats.training_sessions), 7)

    def test_brick_count(self):
        """Test if brick session count is calculated correctly."""
        self.test_data.add_brick_test_data()
        self.all_player_stats = AllPlayerStats(period=StatsPeriod.ALL)

        self.assertEqual(
            self.all_player_stats.stats["Number of brick workouts"][0],
            self.test_data.brick_count,
        )
