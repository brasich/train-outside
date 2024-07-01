from google.transit import gtfs_realtime_pb2
import requests
import plotly.express as px
import pandas as pd
import time
import json
import datetime

def grab_data():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get('https://www.rtd-denver.com/files/gtfs-rt/VehiclePosition.pb')
    feed.ParseFromString(response.content)
    return feed

def extract_entity_data(entity):
    return {
        'vehicle_update_ts': entity.vehicle.timestamp,
        'lat': entity.vehicle.position.latitude,
        'lon': entity.vehicle.position.longitude,
        'trip': entity.vehicle.trip.trip_id,
        'route_id': entity.vehicle.trip.route_id,
        'stop_id': entity.vehicle.stop_id,
        'vehicle_id': entity.vehicle.vehicle.id,
        'vehicle_label': entity.vehicle.vehicle.label
    }

def export_feed_data(feed):
    to_export = []
    export_ts = int(time.time())
    for entity in feed.entity:
        entity_dict = extract_entity_data(entity)
        entity_dict['insert_ts'] = export_ts
        to_export.append(entity_dict)

    with open(f'vehicle_positions_hist/{export_ts}.json', 'w') as f:
        json.dump(to_export, f)

while True:
    feed = grab_data()
    export_feed_data(feed)
    print(f'Export complete at {datetime.datetime.now()}')
    time.sleep(30)