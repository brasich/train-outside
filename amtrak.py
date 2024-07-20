import requests
import json
from hashlib import pbkdf2_hmac
import base64
import binascii
from Crypto.Cipher import AES
import string
import pandas as pd

class TrainTracker:
    def __init__(self):
        metadata = requests.get('https://maps.amtrak.com/rttl/js/RoutesList.json').text
        public_key_index = 0
        for route in json.loads(metadata):
            try:
                public_key_index += route['ZoomLevel']
            except KeyError:
                pass
        
        public_key_metadata = requests.get('https://maps.amtrak.com/rttl/js/RoutesList.v.json').text
        public_key_metadata = json.loads(public_key_metadata)
        public_key = public_key_metadata['arr'][public_key_index]
        
        salt = public_key_metadata['s'][len(public_key_metadata['s'][0])]
        init_vec = public_key_metadata['v'][len(public_key_metadata['v'][0])]

        self.cryptoInitializers= {
            'PUBLIC_KEY': public_key,
            'CRYPTO_SALT': binascii.unhexlify(salt),
            'CRYPTO_IV': binascii.unhexlify(init_vec)
            }

    def decrypt(self, data, keyDerivationPassword):
        cipherText = base64.b64decode(data)
        cryptoInitializers = self.cryptoInitializers

        key = pbkdf2_hmac('sha1', keyDerivationPassword.encode(), cryptoInitializers['CRYPTO_SALT'], 1000, 16)

        decipher = AES.new(key=key, mode=AES.MODE_CBC, iv=cryptoInitializers['CRYPTO_IV'])

        return decipher.decrypt(cipherText).decode()

    def get_train_data(self):
        rawData = requests.get('https://maps.amtrak.com/services/MapDataService/trains/getTrainsData').text
        cryptoInitializers = self.cryptoInitializers
        MASTER_SEGMENT = 88

        privateKeyCipher = rawData[-MASTER_SEGMENT:]
        encryptedTrainData = rawData[:-MASTER_SEGMENT]

        private_key = self.decrypt(privateKeyCipher, cryptoInitializers['PUBLIC_KEY']).split('|')[0]

        train_data_string = self.decrypt(encryptedTrainData, private_key).replace('\x0c', '')
        train_data = json.loads(''.join([c for c in train_data_string if c in string.printable]))
        
        self.train_data = train_data


    def get_station_indicies(self):
        keys = self.train_data['features'][0]['properties'].keys()
        look_from_idx = len('Station')
        indices = [int(key[look_from_idx:]) for key in keys if 'Station' in key]
        indices.sort()
        return indices

    def does_train_stop_at_station(self, train_dict, station_code):
        station_indices = self.get_station_indicies()
        for idx in station_indices:
            try:
                station = json.loads(train_dict['Station' + str(idx)])
            except TypeError:
                continue
            if station['code'] == station_code:
                return True
        
    def get_station_info(self, train_dict, station_code):
        station_indices = self.get_station_indicies()
        for idx in station_indices:
            try:
                station = json.loads(train_dict['Station' + str(idx)])
            except TypeError:
                continue
            if station['code'] == station_code:
                return station
        
    def find_denver_trains(self):
        train_data = self.train_data
        trains = [train['properties'] for train in train_data['features']]
        return [train for train in trains if self.does_train_stop_at_station(train, 'DEN')]

    def parse_station_data(self, station_data):
        return_dict = {}
        if 'postdep' in station_data.keys():
            return_dict['status'] = 'departed'
            return_dict['actual_arrival'] = station_data['postarr']
            return_dict['scheduled_arrival'] = station_data['scharr']
            return_dict['estimated_arrival'] = None
            return_dict['actual_departure'] = station_data['postdep']
            return_dict['scheduled_departure'] = station_data['schdep']
            return_dict['estimated_departure'] = None
        elif 'postarr' in station_data.keys():
            return_dict['status'] = 'arrived'
            return_dict['actual_arrival'] = station_data['postarr']
            return_dict['scheduled_arrival'] = station_data['scharr']
            return_dict['estimated_arrival'] = None
            return_dict['actual_departure'] = None
            return_dict['scheduled_departure'] = station_data['schdep']
            return_dict['estimated_departure'] = station_data['estdep']
        else:
            return_dict['status'] = 'enroute'
            return_dict['actual_arrival'] = None
            return_dict['scheduled_arrival'] = station_data['scharr']
            return_dict['estimated_arrival'] = station_data['estarr']
            return_dict['actual_departure'] = None
            return_dict['scheduled_departure'] = station_data['schdep']
            return_dict['estimated_departure'] = station_data['estdep']
        return return_dict

    def get_train_summary(self, train_dict):
        denver_station_summary = self.parse_station_data(self.get_station_info(train_dict, 'DEN'))
        return_dict = {
            'train_num': train_dict['TrainNum'],
            'heading': train_dict['Heading'],
            'dest': train_dict['DestCode'],
            'origin': train_dict['OrigCode'],
            'route': train_dict['RouteName'],
            'state': train_dict['TrainState'],
            'velocity': train_dict['Velocity'],
        }
        return_dict.update(denver_station_summary)
        return return_dict

    def get_denver_train_df(self):
        denver_trains = self.find_denver_trains()

        train_df = pd.DataFrame.from_records([self.get_train_summary(train_dict) for train_dict in denver_trains])
        for col in ['actual_arrival', 'scheduled_arrival', 'estimated_arrival', 'actual_departure', 'scheduled_departure', 'estimated_departure']:
            train_df[col] = pd.to_datetime(train_df[col]).dt.strftime('%a %b %d, %I:%M%p')

        return train_df