import os

import geopandas as gpd
import polyline as pl
from django.conf import settings
from django.test import TestCase
from shapely.geometry import Point
from training.maps import TrainingMap


class MunicipalityVisitsTest(TestCase):
    """Test code for finding municipalities based on coordinates."""

    @classmethod
    def setUpClass(cls):
        test_data_location = os.path.join(
            settings.BASE_DIR,
            "training",
            "tests",
            "test_data",
        )
        gpkg_file = "gemeente.gpkg"

        file_path = os.path.join(test_data_location, gpkg_file)
        try:
            gdf = gpd.read_file(file_path)
        except FileNotFoundError:
            print(f"File not found {file_path}")
            raise
        cls.training_map = TrainingMap(gdf=gdf)
        super(MunicipalityVisitsTest, cls).setUpClass()

    def test_municipality_amsterdam(self):
        """Test if coordinates for Amsterdam are found."""
        result = self.training_map.find_muni((52.36, 4.9))
        self.assertEqual(result, "Amsterdam")

    def test_municipality_oldambt(self):
        """Test if coordinates for Oldambt are found."""
        result = self.training_map.find_muni((53.20, 7.05))
        self.assertEqual(result, "Oldambt")

    def test_municipality_outside(self):
        """Test if coordinates outside of Netherlands are not found."""
        result = self.training_map.find_muni((48.85, 2.35))
        self.assertIsNone(result)

    def test_within_bounds(self):
        """Test if coordinates within bounds are checked correctly."""
        coordinate = Point(4.9, 52.36)
        result = self.training_map.check_within_bounds(coordinate)

        self.assertTrue(result)

    def test_outside_of_bounds(self):
        """Test if coordinates outside of bounds are checked correctly."""
        coordinate = Point(2.35, 48.85)
        result = self.training_map.check_within_bounds(coordinate)

        self.assertFalse(result)

    def test_get_municipalities(self):
        """Test if a list of coordinates is correctly mapped to municipalities."""
        coordinates = [(52.36, 4.9), (53.20, 7.05), (48.85, 2.35)]
        polyline = pl.encode(coordinates)

        municipalities = sorted(self.training_map.get_municipalities(polyline))
        self.assertEqual(municipalities, ["Amsterdam", "Oldambt"])
