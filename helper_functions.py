import pandas as pd
from datetime import datetime
from math import radians, cos, sin, asin, sqrt, isnan, isinf
from typing import Tuple, List, Dict
import json

# Function to handle NaN and infinite values
def handle_special_floats(data):
    if isinstance(data, list):
        return [handle_special_floats(item) for item in data]
    elif isinstance(data, dict):
        return {key: handle_special_floats(value) for key, value in data.items()}
    elif isinstance(data, float) and (isnan(data) or isinf(data)):
        return None
    else:
        return data
    
# Extract all important data lists
def get_data(dir_paths: list) -> List[Dict]:
    rides_data = []
    # iterete through each directory
    for i, path in enumerate(dir_paths):
        # read the csv files
        dir_rides = pd.read_csv(f"{path}/rides.csv", header=None, names=['token', 'name'], skiprows=1).astype({'token':int}).to_dict(orient='records')
        dir_scenes_list = pd.read_csv(f"{path}/scenes.csv", header=None, names=['token', 'ride_token', 'dir_name'], skiprows=1).astype({'token':int,'ride_token':int})
        dir_sample_list = pd.read_csv(f"{path}/samples.csv", header=None, names=['token', 'scene_token', 'timestamp', 'prev_sample_token'], skiprows=1).dropna(subset=['scene_token']).astype({'token':int,'scene_token':int})
        dir_sensor_list = pd.read_csv(f"{path}/sensor_data.csv", header=None, names=[
            'token', 'timestamp', 'sample_token', 'scene_token', 'measurement_type', 'calibrated_sensor_name',
            'sensor_data_type'], skiprows=1, low_memory=False).dropna(subset=['sample_token']).astype({'token':int,'scene_token':int, 'sample_token':int})
        dir_gps_data = pd.read_csv(f"{path}/gps_data.csv", header=None,
                                names=['token', 'lat', 'lon', 'hgt', 'lat_std', 'lon_std', 'hgt_std'], skiprows=1)
        for ride in dir_rides:
            # RIDES
            ride['directory_token'] = i
            # SCENES
            ride['scenes'] = dir_scenes_list[dir_scenes_list['ride_token'] == ride['token']].to_dict(orient='records')
            # SAMPLES
            for scene in ride['scenes']:
                scene['samples'] = dir_sample_list[dir_sample_list['scene_token'] == scene['token']].to_dict(orient='records')
            # SENSORS
                for sample in scene['samples']:
                    sample['sensors'] = dir_sensor_list[(dir_sensor_list['scene_token'] == scene['token']) & (dir_sensor_list['sample_token'] == sample['token'])]
            # GPS
            # Merge Gps with sensor data on token
                    sample['sensors'] = pd.merge(sample['sensors'],dir_gps_data,on='token',how='left').to_dict(orient='records')
            if len(ride['scenes']) > 0:
                    rides_data.append(ride)
                    
    # DURATION / TIME
    # Extract the duration from the sensor data for each scene -> timestamp example: 2023-09-29 14:48:46.745031
    for ride in rides_data:
        times = sorted(
            [datetime.strptime(sample['timestamp'], "%Y-%m-%d %H:%M:%S.%f") for sample in scene['samples'] for scene in ride['scenes']],
            key=lambda x: x
            )
        ride['duration'] = (times[-1] - times[0]).total_seconds()
        ride['date'] = times[0].strftime("%Y-%m-%d")
        ride['time'] = times[0].strftime("%H:%M:%S")

        # DISTANCE
        ride['distance'] = calculate_total_distance(ride)
        ride['num_scenes'] = len(ride['scenes'])
        ride['num_samples'] = sum([len(scene['samples']) for scene in ride['scenes']])
            
    return handle_special_floats(rides_data)


# Calculate total distance from a ride element in the return object of merge_data
def calculate_total_distance(ride: dict) -> float:
    distance = 0.0
    for scene in ride['scenes']:
        for sample in scene['samples']:
            coords = sorted(
                [sensor for sensor in sample['sensors'] if not isnan(sensor['lat'])],
                key=lambda x: datetime.strptime(x['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            )
            for i in range(1, len(coords),1):
                distance += haversine(coords[i]['lat'], coords[i]['lon'], coords[i-1]['lat'], coords[i-1]['lon'])
    return distance


# Haversine formula to calculate distances between two points on the earth in km
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Convert degrees to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    # Cal Distance using haversine forumla
    # Source: https://www.geeksforgeeks.org/program-distance-two-points-earth/
    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers
    r = 6371
    return c * r


if __name__ == '__main__':
    file_paths = [
        'data/database_csv_1',
        'data/database_csv_2',
        'data/database_csv_3',
    ]

    with open('data.json', 'w') as f:
        json.dump(get_data(file_paths), f, indent=4)
