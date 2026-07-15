import os
from dotenv import load_dotenv

load_dotenv()
OPEN_DATA_APP_TOKEN = os.getenv("OPEN_DATA_APP_TOKEN")

from geopy.geocoders import Nominatim, ArcGIS
import math
import time
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderQuotaExceeded, GeocoderServiceError
from diskcache import Cache
from pathlib import Path

_CACHE_DIR = Path(__file__).resolve().parent.parent / ".geocode_cache"
geocode_cache = Cache(str(_CACHE_DIR))

@geocode_cache.memoize()
def _geocode_address_cached(address: str):    
    # app = Nominatim(user_agent="chicago_location_investigator")
    app = ArcGIS(timeout=10)
    
    max_retries = 3
    retry_delay = 4  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Geocoding location {address}")
            location = app.geocode(address)#.raw
            if location is None:
                raise ValueError(f"Could not geocode {address}.")

            return (location.latitude, location.longitude) #(float(location['lat']), float(location['lon']))
        except (GeocoderTimedOut, GeocoderUnavailable, GeocoderQuotaExceeded, GeocoderServiceError):
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2 
            else:
                raise 
        except Exception as e:
            raise e

def geocode_address(address: str):
    """Provide an address including city and state, and this function will return geocoordinates for this location.

    Args: 
        address: The building address in all-caps format (e.g., '1601 W CHICAGO AVE') - unless otherwise indicated, use "CHICAGO, ILLINOIS" as the city and state.

    Returns: 
        Latitude, Longitude as tuple
    """
    try:
        return _geocode_address_cached(" ".join(address.split()).upper())
    except ValueError as e:
        return str(e)
    
@geocode_cache.memoize()
def _geocode_intersection_cached(street_1: str, street_2: str):    
    app = ArcGIS(timeout=10)
    
    max_retries = 3
    retry_delay = 4  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Geocoding intersection of {street_1} and {street_2}")
            location = app.geocode(f"{street_1} and {street_2}, CHICAGO, IL")

            if location is None:
                raise ValueError(f"Could not geocode {street_1} and {street_2}, CHICAGO, IL.")

            return (location.latitude, location.longitude)
        except (GeocoderTimedOut, GeocoderUnavailable, GeocoderQuotaExceeded, GeocoderServiceError):
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2 
            else:
                raise 
        except Exception as e:
            raise e

def geocode_intersection(street_1: str, street_2: str):
    """Get coordinates for a street intersection / corner (e.g. 'the corner of Monroe and State').
    Use this when the user names two cross streets rather than a specific address.

    Args: 
        street_1: First street name (e.g., 'MONROE')
        street_2: Second street name (e.g., 'STATE')

    Returns: 
        Latitude, Longitude as tuple
    """
    try:
        return _geocode_intersection_cached(street_1.upper(), street_2.upper())
    except ValueError as e:
        return str(e)


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
