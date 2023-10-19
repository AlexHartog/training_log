import geopandas as gpd
import logging
from shapely.geometry import Point
import polyline

from strava_import.schemas import StravaSession

logger = logging.getLogger(__name__)


def style_visited_map(feature):
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


def create_training_map():
    logger.info("Starting map")
    shapefile_path = "training_log/training/map_data/gemeente_2022_v1.shp"
    gdf = gpd.read_file(shapefile_path).head(20)

    gdf = gdf[gdf["H2O"] == "NEE"]

    checks = {"Medemblik": ["Alex"], "Waterland": ["Alex", "Max"], "Urk": ["Max"]}

    gdf["checks"] = gdf["GM_NAAM"].apply(lambda x: checks.get(x, None))
    gdf["checks_string"] = gdf["checks"].apply(lambda x: ", ".join(x or []))

    logger.info("Transforming")
    gdf_transformed = gdf.to_crs(4326)
    geo_json = gdf_transformed.to_json()

    logger.info("Creating folium")
    import folium

    m = folium.Map(location=[52.13, 5.29], zoom_start=7, tiles="cartodb positron")

    cp = folium.GeoJson(
        geo_json, name="basin", style_function=style_visited_map
    ).add_to(m)
    folium.LayerControl().add_to(m)

    folium.GeoJsonTooltip(
        ["GM_NAAM", "checks_string"], aliases=["Gemeente", "Visited by"]
    ).add_to(cp)
    m = m._repr_html_()

    return m


def get_municipalities(polyline_string):
    coordinates = polyline.decode(polyline_string)
    municipalities = set()
    muni = None
    for c in coordinates:
        muni = find_muni(c, previous_match=muni)

        if not muni:
            print(f"No municipality found for {c}")
            continue

        municipalities.add(muni)


def add_visits(strava_session: StravaSession):
    if not strava_session.polyline():
        logger.warning("No polyline found for strava session")
        return

    municipalities = get_municipalities(strava_session.polyline())
    print(municipalities)


def find_muni(coordinates, gdf, previous_match=None):
    coordinate = Point(coordinates[1], coordinates[0])
    # Use spatial join to find the containing municipality
    containing_municipality = None

    if previous_match:
        previous_gdf = gdf[gdf["GM_NAAM"] == previous_match]
        for index, municipality in previous_gdf.iterrows():
            if coordinate.within(municipality["geometry"]):
                return municipality["GM_NAAM"], "previous"

    for index, municipality in gdf.iterrows():
        if coordinate.within(municipality["geometry"]):
            return municipality["GM_NAAM"], "new"

    return containing_municipality
