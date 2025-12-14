import os
from dotenv import load_dotenv

load_dotenv()
YOUR_APP_TOKEN = os.getenv("YOUR_APP_TOKEN")

from geopy.geocoders import Nominatim
import math

def geocode_address(address:str):
    """Provide an address including city and state, and this function will return geocoordinates for this location.
    This is rate limited as the geocoding API is free, so don't send more than 1 request per second.

    Args: 
        address: The building address in all-caps format (e.g., '1601 W CHICAGO AVE') - unless otherwise indicated, use "CHICAGO, ILLINOIS" as the city and state.

    Returns: 
        Latitude, Longitude as tuple
    """

    app = Nominatim(user_agent="chicago_location_checker")
    location = app.geocode(address).raw

    return (float(location['lat']), float(location['lon']))

def get_proximity_to_coords(coordinates: tuple, dist_in_miles: float = .5):
    """Provide a tuple of (latitude, longitude) for a location, and this returns geocoordinates within a radius.
    This will not work on an address, so you must geocode the address before you use this function.

    Args: 
        coordinates: Tuple representing geocoordinates of place, in order latitude, longitude
    Returns: 
        dict of coordinates tuples representing the boundaries of that radius in cardinal directions
    """
    earth_radius_miles = 3958.8
    
    latitude_radians = math.radians(coordinates[0])
    longitude_radians = math.radians(coordinates[1])

    latitude_range = dist_in_miles / earth_radius_miles
    longitude_range = dist_in_miles / (earth_radius_miles * math.cos(latitude_radians))

    north_bound = math.degrees(latitude_radians + latitude_range)
    south_bound = math.degrees(latitude_radians - latitude_range)
    east_bound = math.degrees(longitude_radians + longitude_range)
    west_bound = math.degrees(longitude_radians - longitude_range)

    return {"north":north_bound, "south":south_bound, "east":east_bound, "west": west_bound}
