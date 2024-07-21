from rtd import refresh_vehicles
from amtrak import TrainTracker
import time

print('getting RTD data')
rtd_df = refresh_vehicles()
print('done')

print('getting Amtrak data')
tt = TrainTracker()
tt.get_train_data()
amtrak_df = tt.get_denver_train_df()
print('done')

print('getting RTD position updates')
time.sleep(15)
new_positions = refresh_vehicles()

position_comparison = new_positions[['vehicle_label', 'route_id', 'distance', 'vehicle_update_seconds_ago']].merge(rtd_df[['vehicle_label', 'distance', 'vehicle_update_seconds_ago']], on='vehicle_label', suffixes=['_new', '_old'], how='left').fillna(9999)
position_comparison['status'] = None
position_comparison.loc[(position_comparison['distance_new'] < 0.2) & (position_comparison['distance_old'] > 0.2), 'status'] = 'arriving'
position_comparison.loc[(position_comparison['distance_new'] < 0.2) & (position_comparison['distance_old'] < 0.2), 'status'] = 'at station'
position_comparison.loc[(position_comparison['distance_new'] > 0.2) & (position_comparison['distance_old'] < 0.2), 'status'] = 'departing'
position_comparison.loc[(position_comparison['distance_new'] > 0.2) & (position_comparison['distance_old'] > 0.2), 'status'] = 'away'

rtd_display = position_comparison.sort_values('distance_new')[['route_id', 'distance_new', 'vehicle_update_seconds_ago_new', 'status']].rename({'route_id': 'route', 'distance_new': 'distance', 'vehicle_update_seconds_ago_new': 'update_age'})

print(rtd_display)

amtrak_display = amtrak_df[['train_num', 'dest', 'origin', 'velocity', 'status', 'actual_arrival', 'scheduled_arrival', 'estimated_arrival', 'actual_departure', 'scheduled_departure', 'estimated_departure']].sort_values('scheduled_arrival')

print(amtrak_display)