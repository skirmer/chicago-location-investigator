
import googlemaps
import os
from dotenv import load_dotenv
import requests
import math
import inspect
from tools.data_model import ExactAddress, ExactCoordinates, CoordinateBoundaries

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)


class CollectPlaceData:
    def __init__(self, address:ExactAddress):
        """
        Initialize a GoogleMaps tool instance for a specific address.

        Args:
            address (str): The street address to investigate and analyze.

        Attributes:
            address (str): The provided street address.
            place_id: The Google Maps place ID for the address, obtained from the first result.
            place_coords: Coordinates for the place, initially set to None.
        """
        self.address = address
        self.place_id = self.get_place_id(address)[0]
        self.place_coords = None
        
    def get_place_id(self,address: str ="1856 South Loomis, Chicago IL"):
        """
        Retrieve the place ID for a given address using Google Maps API.

        Args:
            address (str, optional): The address to search for. Defaults to "1856 South Loomis, Chicago IL".

        Returns:
            tuple: A tuple containing the place ID as the first element. Note: Returns a tuple with trailing comma.

        Raises:
            KeyError: If the API response doesn't contain expected 'candidates' key or if no candidates are found.
            Exception: If the Google Maps API call fails or returns an error.
        """
        place = gmaps.find_place(address, input_type = 'textquery')
        return place['candidates'][0]['place_id'], 

    def get_place_details(self):
        """
        Retrieves detailed information about a place using Google Maps API.

        This method fetches comprehensive place details from Google Maps using the 
        instance's place_id attribute. It also extracts and stores the geographical 
        coordinates of the place in the instance's place_coords attribute.

        Returns:
            dict: A dictionary containing the full place details response from the 
                  Google Maps API, including geometry, address components, ratings, 
                  reviews, and other available place information.

        Raises:
            googlemaps.exceptions.ApiError: If the API request fails or returns an error.
            KeyError: If the expected structure is not present in the API response.

        Note:
            Requires the instance to have a valid place_id attribute set before calling.
            The method updates the instance's place_coords attribute as a side effect.
        """
        place = gmaps.place(self.place_id)
        self.place_coords = place['result']['geometry']['location']
        return place

    def get_nearby_places(self, radius_mi:float =.25):
        """
        Retrieve nearby places within a specified radius of the current location.
        This method uses the Google Maps Places API to find nearby locations and extracts
        relevant details for each place found within the search radius.
        Args:
            radius_mi (float, optional): Search radius in miles. Defaults to 0.25 miles.
        Returns:
            list[dict]: A list of dictionaries containing place details. Each dictionary
                        includes the following keys:
                        - geometry: Geographic location data
                        - name: Name of the place
                        - address: Vicinity/address information
                        - place_id: Unique Google Places identifier
                        - business_status: Current operational status
                        - international_phone_number: Contact phone number
                        - business_types: List of place type categories
                        - rating: User rating score
                        - price_level: Price level indicator
        Note:
            Requires get_place_details() to be called first to establish place_coords.
            Radius is converted from miles to meters (multiplied by 1609) for the API call.
        """
        _ = self.get_place_details()
        nearby = gmaps.places_nearby(self.place_coords, radius = (radius_mi * 1609))
        
        details_list = []
        for i in nearby['results']:
            details_list.append(
                {"geometry": i.get("geometry"),
                 "name": i.get("name"),
                 "address": i.get("vicinity"),
                 "place_id": i.get("place_id"),
                 "business_status": i.get("business_status"),
                 "international_phone_number": i.get("international_phone_number"),
                 "business_types": i.get("types"),
                 "rating": i.get("rating"),
                 "price_level": i.get("price_level")}
            )
        
        return details_list
    
    def get_nearby_restaurants(self, radius_mi:float):
        """
        Get nearby restaurants within a specified radius.
        Filters nearby places to return only operational restaurants.
        Args:
            radius_mi (float): Search radius in miles from the current location.
        Returns:
            list: A list of dictionaries containing restaurant information. Each dictionary
                    includes details about restaurants that are currently operational and 
                    have 'restaurant' in their business types.
        Note:
            This method relies on get_nearby_places() to retrieve initial place data,
            then filters for restaurants with 'OPERATIONAL' business status.
        """
        places = self.get_nearby_places(radius_mi=radius_mi)
        
        restaurants = [i for i in places if 'restaurant' in i['business_types'] and i['business_status'] == 'OPERATIONAL']
        return restaurants
    
    

def get_street_view(coordinates, filename=None):
    """Pass latitude and longitude of a point in a dict with format {"lat":latitude, "lng":longitude}, and this function saves an image file to disk showing the street view of that location
    
    Args:
        coordinates: Dict, with format {"lat":latitude, "lng":longitude}
  
    Returns:
        Returns the filepath for the image it has saved. File is saved to local disk.
    """
    
    # 1. Determine the location string
    if isinstance(coordinates, dict) and 'lat' in coordinates:
        # SKIP GEOCODING: We already have the points
        lat_lng = f"{coordinates['lat']},{coordinates['lng']}"
        print(f"Using provided coordinates: {lat_lng}")
    else:
        print("Input malformed or does not contain coordinates. Submit argument with format {'lat':latitude, 'lng':longitude}")
        print(f"You submitted {coordinates}.")

    # 2. Metadata Check (Direct Request)
    meta_url = "https://maps.googleapis.com/maps/api/streetview/metadata"
    meta_params = {"location": lat_lng, "key": GOOGLE_API_KEY}
    meta_response = requests.get(meta_url, params=meta_params).json()
    
    if meta_response.get("status") != "OK":
        print(f"Metadata Status: {meta_response.get('status')}")
        if "error_message" in meta_response:
            print(f"Details: {meta_response['error_message']}")
        return
    
    # 2.5 Calculate Heading
    if meta_response.get("status") == "OK":
        # Get the car's actual position from metadata
        pano_loc = meta_response['location']
        
        heading = calculate_heading(
            pano_loc['lat'], pano_loc['lng'], 
            coordinates['lat'], coordinates['lng']
        )
        
        img_params = {
            "size": "600x400",
            "location": lat_lng,
            "key": GOOGLE_API_KEY,
            "heading": heading, # Points the camera at the target!
            "pitch": 10,        # Slightly tilted up to see the building
            "fov": 90
        }

    # 3. Download Image (Direct Request)
    img_url = "https://maps.googleapis.com/maps/api/streetview"

    img_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "img")
    os.makedirs(img_folder, exist_ok=True)
    if not filename:
        filename = os.path.join(img_folder, f"street_view_{coordinates['lat']:.3f}_{coordinates['lng']:.3f}.jpg")
        short_filename = f"data/img/street_view_{coordinates['lat']:.3f}_{coordinates['lng']:.3f}.jpg"
    else:
        filename = os.path.join(img_folder, filename)
        
    img_response = requests.get(img_url, params=img_params)
    if img_response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(img_response.content)
        print(f"Success! Saved as {short_filename}")  
        return short_filename


def calculate_heading(src_lat, src_lng, dest_lat, dest_lng):
    # Math to find the angle between the Street View car and your target
    lat1, lng1, lat2, lng2 = map(math.radians, [src_lat, src_lng, dest_lat, dest_lng])
    dLng = lng2 - lng1
    y = math.sin(dLng) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLng)
    heading = math.degrees(math.atan2(y, x))
    return (heading + 360) % 360



if __name__ == "__main__":

    detail = CollectPlaceData(address="1601 W Chicago Ave").get_nearby_restaurants(radius_mi=.2)
    print(detail)
    
    # place = get_place_details()
    # print(place)

    # # Your specific coordinates
    # latlon = {'lat': 41.8561767, 'lng': -87.66149810000002}
    # get_street_view(latlon)
    
# Heading: 0 to 360 (0=North, 90=East, 180=South, 270=West).

# Pitch: -90 to 90 (0 is horizon level, positive looks up, negative looks down).    
    
    
    # place = gmaps.find_place("1856 South Loomis, Chicago IL", input_type = 'textquery')
    # print(place)
    # #place = {'candidates': [{'place_id': 'ChIJ6b3HUy0tDogR1PqCcHMOAZg'}], 'status': 'OK'}
    
    # place = gmaps.place(place['candidates'][0]['place_id'])
    # print(place)
    # # nearby = gmaps.places_nearby(place['candidates'][0])
    # # print(nearby)

    # # photo = gmaps.places_photo(place['candidates'][0]['place_id'], max_height=200)
    # # print(photo)
    # # f = open('photo', 'wb')
    # # for chunk in gmaps.places_photo(, max_width=100):
    # #     if chunk:
    # #         f.write(chunk)
    # # f.close()
    

    # # gmaps.places()

