from google.transit import gtfs_realtime_pb2
import requests
import pandas as pd
import time
import math
import numpy as np

def extract_entity_data(entity):
    return {
        'insert_ts': int(time.time()),
        'vehicle_update_ts': entity.vehicle.timestamp,
        'lat': entity.vehicle.position.latitude,
        'lon': entity.vehicle.position.longitude,
        'trip': entity.vehicle.trip.trip_id,
        'route_id': entity.vehicle.trip.route_id,
        'stop_id': entity.vehicle.stop_id,
        'vehicle_id': entity.vehicle.vehicle.id,
        'vehicle_label': entity.vehicle.vehicle.label
    }

def haversine_distance_to_me(lat1, lon1, lat2=39.75342747354773, lon2=-105.0009645548709):
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0
    lat1 = lat1 * math.pi / 180.0
    lat2 = lat2 * math.pi / 180.0

    a = np.sin(dLat / 2) ** 2 + np.sin(dLon / 2) ** 2 * np.cos(lat1) * np.cos(lat2)
    rad = 6371
    c = 2 * np.arcsin(np.sqrt(a))
    return rad * c

def refresh_vehicles():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get('https://www.rtd-denver.com/files/gtfs-rt/VehiclePosition.pb')
    feed.ParseFromString(response.content)

    records = []
    for entity in feed.entity:
        records.append(extract_entity_data(entity))

    rt_positions = pd.DataFrame.from_records(records)

    backyard_routes = ['113G', '113B', '117N', 'A']

    relevant_vehicles = rt_positions[rt_positions.route_id.isin(backyard_routes)].copy()

    relevant_vehicles['distance'] = haversine_distance_to_me(relevant_vehicles['lat'], relevant_vehicles['lon'])

    relevant_vehicles['insert_ts_seconds_ago'] = int(time.time()) - relevant_vehicles['insert_ts'].astype(int)
    relevant_vehicles['vehicle_update_seconds_ago'] = int(time.time()) - relevant_vehicles['vehicle_update_ts'].astype(int)

    return relevant_vehicles