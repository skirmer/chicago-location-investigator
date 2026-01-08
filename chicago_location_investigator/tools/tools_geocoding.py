import os
from dotenv import load_dotenv

load_dotenv()
OPEN_DATA_APP_TOKEN = os.getenv("OPEN_DATA_APP_TOKEN")
from chicago_location_investigator.tools.data_model import LocationInput, ExactAddress, ExactCoordinates, CoordinateBoundaries
from geopy.geocoders import Nominatim
import math
import time
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

def geocode_address(location:LocationInput):
    """Converts a human-readable street address into (latitude, longitude) coordinates.
    CRITICAL: Use this tool whenever you have a street address but the target tool requires a 'coordinates' or 'ExactCoordinates' object. Do not attempt to guess or hallucinate coordinates yourself.    This is rate limited as the geocoding API is free, so don't send more than 1 request per second.

    Args: 
        location:
            location_type = "exact_address"
                value.address must be provided
    Returns: 
        ExactCoordinates object
    """
    if isinstance(location.value, ExactAddress):
        address = location.value.address
    else:
        print("Malformed input provided")
        
    app = Nominatim(user_agent="chicago_location_investigator")
    
    max_retries = 3
    retry_delay = 4  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Geocoding location {address}")
            location = app.geocode(address).raw
            return ExactCoordinates(coordinates = (float(location['lat']), float(location['lon'])))
        except (GeocoderTimedOut, GeocoderUnavailable):
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2 
            else:
                raise 
        except Exception as e:
            raise e

def get_proximity_to_coords(location:LocationInput, dist_in_miles: float = .5):
    """Provide a tuple of (latitude, longitude) in the form of ExactCoordinates object for a location, and this returns geocoordinates within a radius.
    This will not work on an address, so you must geocode the address before you use this function.

    Args: 
        location:
            location_type = "coordinates"
                value.coordinates must be provided
    Returns: 
        CoordinateBoundaries object representing the boundaries of that radius in cardinal directions
    """
    if isinstance(location.value, ExactCoordinates):
        coordinates = location.value.coordinates
    else:
        print("Malformed input provided")
        

    earth_radius_miles = 3958.8
    
    latitude_radians = math.radians(coordinates[0])
    longitude_radians = math.radians(coordinates[1])

    latitude_range = dist_in_miles / earth_radius_miles
    longitude_range = dist_in_miles / (earth_radius_miles * math.cos(latitude_radians))

    north_bound = math.degrees(latitude_radians + latitude_range)
    south_bound = math.degrees(latitude_radians - latitude_range)
    east_bound = math.degrees(longitude_radians + longitude_range)
    west_bound = math.degrees(longitude_radians - longitude_range)

    return CoordinateBoundaries(coordinates={"north":north_bound, "south":south_bound, "east":east_bound, "west": west_bound})
