from pydantic import BaseModel, Field
from typing import Union, Literal

class ExactAddress(BaseModel):
    address: str = Field(None, description="The building address in all-caps format (e.g., '1601 W CHICAGO AVE')")
    house_number: str = Field(None, description="The house or building number from the address (eg, 1601)")
    street_direction: str = Field(None, description="The cardinal direction of the street, a single character, in all caps (eg N, S, E, or W)")
    street: str = Field(None, description="The street name in all-caps format (e.g., 'MAIN ST')")


class CoordinateBoundaries(BaseModel):
    coordinate_boundaries: dict = Field(None, description='The dict of the coordinate boundaries as floats in format {"north":north_bound, "south":south_bound, "east":east_bound, "west": west_bound}')    

class ExactCoordinates(BaseModel):
    coordinates: tuple = Field(None, description="Tuple containing floats, representing geocoordinates of place, in order latitude, longitude")
    latitude: float = Field(None, description="Latitude")
    longitude: float = Field(None, description="Longitude")

class LocationInput(BaseModel):
    location_type: Literal["exact_address", "coordinate_boundaries", "coordinates"]
    value: Union[ExactAddress, CoordinateBoundaries, ExactCoordinates]
