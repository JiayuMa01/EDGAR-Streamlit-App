from pydantic import BaseModel
from typing import List

class compressed_ride(BaseModel):
    token: int
    name: str
    directory_token: int
    duration: float
    date: str
    time: str
    distance: float
    num_scenes: int
    num_samples: int
    
class aggregated_gps(BaseModel):
    Latitude: float
    Longitude: float
    Density: float

class ride_data(BaseModel):
    name: str
    duration: float
    date: str
    time: str
    distance: float
    num_scenes: int
    num_samples: int
    gps_coordinates: List[List[float]]
    gps_heatmap_data: List[List[float]]
