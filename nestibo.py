
from sensibo_client import SensiboClientAPI
import nest
from pprint import pprint
import sys
from time import sleep
import json
import logging


# load credentials from creds.json
try:
    with open('creds.json') as f:
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


logging.basicConfig(level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
lgr = logging.getLogger(__name__)

_VALID_SENSIBO_TEMPS = [86, 84, 82, 81, 79, 77, 75, 73, 72, 70, 68, 66, 64, 63, 61]

"""
Sensibo section
"""
def call_sensibo():
    client = SensiboClientAPI(_S_API)
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


def change_sensibo_target_temp(new_temp):
    # check if it validated
    if new_temp == 1:
        lgr.error('Invalid temp: %s. Valid entries are %s' % (new_temp, _VALID_SENSIBO_TEMPS))
        return 1
    else:
        client, s_loft_uid = call_sensibo()
        # get the current ac_state
        ac_state = client.pod_ac_state(s_loft_uid)
        # change to target temperature
        client.pod_change_ac_state(s_loft_uid, ac_state, "targetTemperature", new_temp)


def temp_mangler(nest_temp):
    # Nest supports tons of temperature settings, my heat pump does not :()
    if nest_temp in _VALID_SENSIBO_TEMPS:
        return nest_temp
    if nest_temp >= 61 and nest_temp <= 86:
        nest_temp = nest_temp - 1
        return nest_temp
    if nest_temp < 61:
        return 61
    if nest_temp > 86:
        return 86
    return 1



"""
Nest Section
"""
def call_nest():
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

def main():

    while True:
        sleep(2)

        nest_loft = call_nest()
        sensibo_loft, s_loft_uid = call_sensibo()
        
        # Get Nest information
        nest_info = {
            'cur_temp': nest_loft.temperature,
            'raw_target_temp': nest_loft.target,
            'target_temp': temp_mangler(nest_loft.target), # hate this
            'mode'    : nest_loft.mode,
        }

        # Get Sensibo information
        sensibo_info = {
            'cur_temp': None, # Sensibo doesn't track the internal thermostat of the heatpump
            'target_temp': sensibo_loft.pod_ac_state(s_loft_uid)['targetTemperature'],
            'mode': sensibo_loft.pod_ac_state(s_loft_uid)['mode'] # future use
        }
        lgr.info('Current Nest info: %s' % nest_info)
        lgr.info('Current Sensibo info: %s' % sensibo_info)
        
        if nest_info['target_temp'] != sensibo_info['target_temp']:
            lgr.info('Changing Sensibo from %s to %s' % (sensibo_info['target_temp'], nest_info['target_temp']))
            change_sensibo_target_temp(nest_info['target_temp'])
        else:
            lgr.info('No change in temperature')
        
if __name__ == "__main__":
    main()
