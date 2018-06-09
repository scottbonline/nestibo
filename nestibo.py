
from sensibo_client import SensiboClientAPI
import nest
from pprint import pprint
import sys
from time import sleep
import json
import logging

_SLEEP = 5
_VALID_SENSIBO_TEMPS = [86, 84, 82, 81, 79, 77, 75, 73, 72, 70, 68, 66, 64, 63, 61]
_CREDENTIALS = 'creds.json'

try:
    with open(_CREDENTIALS) as f:
        creds = json.load(f)
        # Sensibo creds
        _S_API = creds['sensibo_API']
        _S_ROOM = creds['sensibo_room']
        # Nest creds
        client_id = creds['nest_id']
        client_secret = creds['nest_secret']
        access_token_cache_file = creds['nest_cache']
except:
    lgr.error('Invalid creds.json file')
    sys.exit(1)


def lager(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler('log.txt', mode='w')
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    logging.getLogger("requests").setLevel(logging.WARNING)
    return logger

lgr = lager('sensibo')



"""
Sensibo section
"""
def call_sensibo():
    lgr.info('Collecting data via Sensibo API')
    try:
        client = SensiboClientAPI(_S_API)
    except requests.exceptions.RequestException as e:
        lgr.error(e)

    s_loft_uid = client.devices()['Loft']
    # ac_state reference - remove
    ref = {
        u'on': True, 
        u'nativeTargetTemperature': 21, 
        u'fanLevel': u'auto', 
        u'temperatureUnit': u'F', 
        u'targetTemperature': 70, 
        u'nativeTemperatureUnit': u'C', 
        u'mode': u'cool', 
        u'swing': u'stopped'
    }
    # hardcoded to Loft room for now
    return client, s_loft_uid


"""
Nest Section
"""
def call_nest():
    lgr.info('Collecting data via Nest API')
    napi = nest.Nest(client_id=client_id, client_secret=client_secret, access_token_cache_file=access_token_cache_file)

    if napi.authorization_required:
        print('Go to ' + napi.authorize_url + ' to authorize, then enter PIN below')
        if sys.version_info[0] < 3:
            pin = raw_input("PIN: ")
        else:
            pin = input("PIN: ")
        napi.request_token(pin)


    for structure in napi.structures:
        continue
        '''
        print ('Structure %s' % structure.name)
        print ('    Away: %s' % structure.away)
        print ('    Devices:')
        print type(structure)

        for device in structure.thermostats:
            print ('        Device: %s' % device.name)
            print ('            Temp: %0.1f' % device.temperature)
'''
    # Just get the thermostat for the loft
    loft = structure.thermostats[1]
    return loft

class Nestibo():
    # Coontrol class for syncing the temp
    
    def __init__(self):
        # get the controller objects
        self.sensibo_loft, self.s_loft_uid = call_sensibo()
        self.nest_loft = call_nest()
        # set some common variables
        self.nest_target_adj = None
        self.nest_target = self.nest_loft.target
        self.sensibo_target = self.sensibo_loft.pod_ac_state(self.s_loft_uid)['targetTemperature']
        self.sensibo_ac_state = self.sensibo_loft.pod_ac_state(self.s_loft_uid)

    def temp_mangler(self):
        # Nest supports tons of temperature settings, my heat pump does not :(
        if self.nest_target in _VALID_SENSIBO_TEMPS:
            self.nest_target_adj = self.nest_target 
        elif self.nest_target >= 61 and self.nest_target <= 86:
            self.nest_target_adj = self.nest_target - 1
        elif self.nest_target < 61:
            self.nest_target_adj = 61
        elif self.nest_target> 86:
            self.nest_target_adj = 86
        return self.nest_target_adj

    def check_mode(self, controller):
        if controller == 'nest':
            print self.nest_loft.mode

    def sync_temp(self):
        lgr.info('Nest target temp is: %s' % self.nest_target)
        self.nest_target_adj = self.temp_mangler()
        lgr.info('Nest adjusted target temp is: %s ' % self.nest_target_adj)
        lgr.info('Sensibo target temp is: %s' % self.sensibo_target)
        if self.nest_target_adj != self.sensibo_target:
            lgr.info('Changing the temperature from %s to %s' % (self.sensibo_target, self.nest_target_adj))
            self.sensibo_loft.pod_change_ac_state(self.s_loft_uid, self.sensibo_ac_state, "targetTemperature", self.nest_target_adj)
        else:
            lgr.info('No change in target temperature detected')

    def get_temp(self):
        lgr.info('Room temperature according to Nest is: %s' % self.nest_loft.temperature)
        return self.nest_loft.temperature

def main():
    
    while True:
        lgr.info('Waiting %s seconds....' % _SLEEP)
        sleep(_SLEEP)
        foo = Nestibo()
        foo.sync_temp()
        foo.get_temp()

        
if __name__ == "__main__":
    main()
