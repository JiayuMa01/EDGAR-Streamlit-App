from fastapi import Depends, HTTPException, FastAPI, Response, status
import pandas as pd
from typing import Annotated, List

# internal imports
from helper_functions import get_data
from models import *
from fake_auth import auth_router, get_current_user

data_router = FastAPI()

# include the auth_router
data_router.include_router(auth_router)


# -----------------
# Data Extraction
# -----------------

# paths to the repo of csv files
file_paths = [
  'data/database_csv_1',
  'data/database_csv_2',
  'data/database_csv_3',
]

# extract the data from the csv files
data = get_data(file_paths)

# -----------------
# Fake Authentication
# -----------------

from fake_auth import *
  
# -----------------
# Overview Endpoints
# -----------------

# return the rides name in the database
@data_router.get('/dashboard/rides')
def list_ride(
  current_user: Annotated[User, Depends(get_current_user)],
) -> List[compressed_ride]:
  list = []
  for ride in data:
    list.append(ride.copy())
    del(list[-1]['scenes'])
  return list

# return the GPS points of all the rides
@data_router.get('/dashboard/gps')
def get_gps_data(
  current_user: Annotated[User, Depends(get_current_user)],
) -> List[aggregated_gps]:
  points = []
  for ride in data:
    for scene in ride['scenes']:
      for sample in scene['samples']:
        for sensor in sample['sensors']:
          if sensor['lat']!=None and sensor['lon']!=None and sensor['hgt']!=None and (sensor['lat']!=0 or sensor['lon']!=0 or sensor['hgt']!=0):
            
            points.append({'Latitude': sensor['lat'],
                           'Longitude': sensor['lon'],
                           'Density': sensor['hgt'], # use height as density
                           })
  return points

# -----------------
# Data Endpoints
# -----------------

# return the merged data of the given ride
@data_router.get('/dashboard/{ride_name}')
def get_ride_data(
  ride_name: str,
  current_user: Annotated[User, Depends(get_current_user)],
) -> ride_data:
  for ride in data:
    if ride['name'] == ride_name:
      result = {'name': ride['name'],
                'duration': ride['duration'],
                'date': ride['date'],
                'time': ride['time'],
                'distance': ride['distance'],
                }
      result['num_scenes'] = len(ride['scenes'])
      result['num_samples'] = sum([len(scene['samples']) for scene in ride['scenes']])
      # create the gps_coordinates from the sensors measurment
      gps = []
      for scene in ride['scenes']:
        for sample in scene['samples']:
          for sensor in sample['sensors']:
            if sensor['lat']!=None and sensor['lon']!=None and sensor['hgt']!=None and (sensor['lat']!=0 or sensor['lon']!=0 or sensor['hgt']!=0):
              gps.append([sensor['lat'],sensor['lon']])
      result['gps_coordinates'] = gps
      result['gps_heatmap_data'] = gps
      return result
    
  raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f'Ride {ride_name} not found.'
    )
  


