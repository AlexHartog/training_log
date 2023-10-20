import logging

import folium
import geopandas as gpd
import polyline
from shapely.geometry import Point
from .models import MunicipalityVisits

logger = logging.getLogger(__name__)


class TrainingMap:
    def __init__(self):
        self.regional_map = self.load_regional_dataframe()

    def load_regional_dataframe(self):
        logger.info("Loading regional map")
        shapefile_path = "training_log/training/map_data/gemeente_2022_v1.shp"
        gdf = gpd.read_file(shapefile_path)  # .head(20)
        gdf = gdf[gdf["H2O"] == "NEE"]
        logger.info("Converting regional map to EPSG:4326")
        return gdf.to_crs(4326)

    def style_visited_map(self, feature):
        match feature["properties"]["checks"]:
            case ["Alex"]:
                fill_opacity = 0.5
                fill_color = "red"
            case ["Max"]:
                fill_opacity = 0.5
                fill_color = "blue"
            case ["Alex", "Max"]:
                fill_opacity = 0.5
                fill_color = "purple"
            case _:
                fill_opacity = 0
                fill_color = "white"

        return {
            "color": "gray",  # Line color
            "fillColor": fill_color,
            "fillOpacity": fill_opacity,
            "weight": 1,  # Line width (adjust as needed)
            "tooltip": feature["properties"]["GM_NAAM"],
        }

    def load_visited(self):
        visited = MunicipalityVisits.objects.all()
        return visited

    def create_training_map(self):
        # visits = MunicipalityVisits.objects.all()

        checks = {"Medemblik": ["Alex"], "Waterland": ["Alex", "Max"], "Urk": ["Max"]}

        self.regional_map["checks"] = self.regional_map["GM_NAAM"].apply(
            lambda x: checks.get(x, None)
        )
        self.regional_map["checks_string"] = self.regional_map["checks"].apply(
            lambda x: ", ".join(x or [])
        )

        geo_json = self.regional_map.to_json()

        logger.info("Creating folium")

        m = folium.Map(location=[52.13, 5.29], zoom_start=7, tiles="cartodb positron")

        cp = folium.GeoJson(
            geo_json, name="basin", style_function=self.style_visited_map
        ).add_to(m)
        folium.LayerControl().add_to(m)

        folium.GeoJsonTooltip(
            ["GM_NAAM", "checks_string"], aliases=["Gemeente", "Visited by"]
        ).add_to(cp)
        m = m._repr_html_()

        return m

    def get_municipalities(self, polyline_string):
        logger.debug(f"Checking for polyline {polyline_string}")
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
        min_lon, min_lat, max_lon, max_lat = self.regional_map.total_bounds
        return min_lat <= coordinate.y <= max_lat and min_lon <= coordinate.x <= max_lon

    def find_muni(self, coordinates, previous_match=None):
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
