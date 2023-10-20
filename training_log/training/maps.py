import datetime
import logging
import os

import folium
import geopandas as gpd
import polyline
from django.contrib.auth.models import User
from shapely.geometry import Point

from .models import MunicipalityVisits
from .stats import DEFAULT_START_DATE

logger = logging.getLogger(__name__)

GDF_OUTPUT_PATH = "training_log/training/map_data/gemeente.gpkg"
SHAPEFILE_PATH = "training_log/training/map_data/gemeente_2022_v1.shp"


class TrainingMap:
    """This class is used to create a map of the municipalities
    visited during training."""

    def __init__(self, gdf=None):
        if gdf is None:
            self.regional_map = self.load_regional_dataframe()
        else:
            self.regional_map = gdf
        self.usernames = None

    def set_users(self, user_ids):
        """Set the included user names."""
        self.usernames = list(
            User.objects.filter(id__in=user_ids).values_list("username", flat=True)
        )

    def load_regional_dataframe(self):
        """Load the regional map. Load from disk if it exists.
        Otherwise create it from shapefile and save to disk."""
        if os.path.exists(GDF_OUTPUT_PATH):
            logger.info(f"Loading {GDF_OUTPUT_PATH}")
            gdf = gpd.read_file(GDF_OUTPUT_PATH)
        else:
            logger.info("Loading regional map")
            gdf = gpd.read_file(SHAPEFILE_PATH)
            gdf = gdf[gdf["H2O"] == "NEE"]
            logger.info("Converting regional map to EPSG:4326")
            gdf = gdf.to_crs(4326)
            logger.info(f"Saving to {GDF_OUTPUT_PATH}")
            gdf.to_file(filename=GDF_OUTPUT_PATH, driver="GPKG")
        return gdf

    def style_visited_map(self, feature):
        """Style regions based on the users that have visited."""
        fill_opacity = 0.2
        fill_color = "gray"

        if self.usernames and len(self.usernames) == 2:
            visits = feature["properties"]["visits"]
            if not visits:
                fill_opacity = 0.2
                fill_color = "gray"
            elif len(visits) == 2:
                fill_opacity = 0.5
                fill_color = "purple"
            elif visits[0].lower() == self.usernames[0].lower():
                fill_opacity = 0.5
                fill_color = "red"
            elif visits[0].lower() == self.usernames[1].lower():
                fill_opacity = 0.5
                fill_color = "blue"

        if self.usernames and len(self.usernames) == 1:
            if feature["properties"]["visits"]:
                fill_opacity = 0.5
                fill_color = "blue"
            else:
                fill_opacity = 0.2
                fill_color = "gray"

        return {
            "color": "gray",
            "fillColor": fill_color,
            "fillOpacity": fill_opacity,
            "weight": 1,
            "tooltip": feature["properties"]["GM_NAAM"],
        }

    @staticmethod
    def get_users_per_municipality(users, disciplines, start_date, end_date):
        """Create a dictionary of users visited per municipality."""
        visits = MunicipalityVisits.objects.select_related(
            "training_session__user"
        ).filter(
            training_session__user__in=users,
            training_session__discipline__name__in=disciplines,
            training_session__date__range=(start_date, end_date),
        )

        municipality_users_dict = {}

        for visit in visits:
            municipality = visit.municipality
            username = visit.training_session.user.username.capitalize()

            if municipality not in municipality_users_dict:
                municipality_users_dict[municipality] = []

            if username not in municipality_users_dict[municipality]:
                municipality_users_dict[municipality].append(username)

        return municipality_users_dict

    def create_training_map(
        self,
        user_ids,
        disciplines,
        start_date=DEFAULT_START_DATE,
        end_date=datetime.date.today(),
    ):
        """Create the training map using folium."""
        municipality_visits = self.get_users_per_municipality(
            user_ids, disciplines, start_date, end_date
        )
        self.set_users(user_ids)

        self.regional_map["visits"] = self.regional_map["GM_NAAM"].apply(
            lambda x: municipality_visits.get(x, None)
        )
        self.regional_map["visits_string"] = self.regional_map["visits"].apply(
            lambda x: ", ".join(x or [])
        )

        logger.info("Transforming regional map to json")
        geo_json = self.regional_map.to_json()

        logger.info("Creating folium")

        m = folium.Map(location=[52.13, 5.29], zoom_start=7, tiles="cartodb positron")

        logger.info("Adding styles and tooltips")
        cp = folium.GeoJson(
            geo_json, name="visits", style_function=self.style_visited_map
        ).add_to(m)
        folium.LayerControl().add_to(m)

        folium.GeoJsonTooltip(
            ["GM_NAAM", "visits_string"], aliases=["Gemeente", "Visited by"]
        ).add_to(cp)

        logger.info("Converting map to HTML")
        m = m._repr_html_()

        return m

    def get_municipalities(self, polyline_string):
        """Get all the municipalities from a polyline."""
        if not polyline_string:
            logger.warning("Polyline is None")
            return

        coordinates = polyline.decode(polyline_string)
        municipalities = set()
        muni = None
        for c in coordinates:
            muni = self.find_muni(c, previous_match=muni)

            if muni:
                municipalities.add(muni)

        return list(municipalities)

    def check_within_bounds(self, coordinate: Point) -> bool:
        """Check if a coordinate is within the bounds of the regional map."""
        min_lon, min_lat, max_lon, max_lat = self.regional_map.total_bounds
        return min_lat <= coordinate.y <= max_lat and min_lon <= coordinate.x <= max_lon

    def find_muni(self, coordinates, previous_match=None):
        """Find the municipality based on the coordinates."""
        coordinate = Point(coordinates[1], coordinates[0])

        if not self.check_within_bounds(coordinate):
            return

        if previous_match:
            previous_gdf = self.regional_map[
                self.regional_map["GM_NAAM"] == previous_match
            ]
            for index, municipality in previous_gdf.iterrows():
                if coordinate.within(municipality["geometry"]):
                    return municipality["GM_NAAM"]

        for index, municipality in self.regional_map.iterrows():
            if coordinate.within(municipality["geometry"]):
                return municipality["GM_NAAM"]

        return
