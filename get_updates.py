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

print('RTD:')
print(rtd_df)

print('Amtrak:')
print(amtrak_df)

print('getting RTD position updates')
time.sleep(15)
new_positions = refresh_vehicles()

position_comparison = new_positions[['vehicle_label', 'route_id', 'distance', 'vehicle_update_seconds_ago']].merge(rtd_df[['vehicle_label', 'distance', 'vehicle_update_seconds_ago']], on='vehicle_label', suffixes=['_new', '_old'], how='left').fillna(9999)
position_comparison['status'] = None
position_comparison.loc[(position_comparison['distance_new'] < 0.2) & (position_comparison['distance_old'] > 0.2), 'status'] = 'arriving'
position_comparison.loc[(position_comparison['distance_new'] < 0.2) & (position_comparison['distance_old'] < 0.2), 'status'] = 'at station'
position_comparison.loc[(position_comparison['distance_new'] > 0.2) & (position_comparison['distance_old'] < 0.2), 'status'] = 'departing'
position_comparison.loc[(position_comparison['distance_new'] > 0.2) & (position_comparison['distance_old'] > 0.2), 'status'] = 'away'

updates = position_comparison[position_comparison['status'].isin(['arriving', 'departing', 'at station'])]
if len(updates) > 0:
    print(time.time())
    print(updates)

else:
    print('no trains at station')
    print(position_comparison)