
from sensibo_client import SensiboClientAPI
import nest
from pprint import pprint
import sys
from time import sleep
import json
import logging

_SLEEP = 300
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


def call_sensibo():
    lgr.info('Collecting data via Sensibo API')
    _retry_throttle = 0
    while True:
        sleep(_retry_throttle)
        try:
            client = SensiboClientAPI(_S_API)
            s_loft_uid = client.devices()['Loft']
            break
        except Exception as e:
            lgr.error(e)
            lgr.warning('Retry call_sensibo with throttle of: %s' % _retry_throttle)
            _retry_throttle += 5

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


def call_nest():
    lgr.info('Collecting data via Nest API')
    _retry_throttle = 0
    while True:
        sleep(_retry_throttle)
        try:
            napi = nest.Nest(client_id=client_id, client_secret=client_secret, access_token_cache_file=access_token_cache_file)

            if napi.authorization_required:
                print('Go to ' + napi.authorize_url + ' to authorize, then enter PIN below')
                if sys.version_info[0] < 3:
                    pin = raw_input("PIN: ")
                else:
                    pin = input("PIN: ")
                napi.request_token(pin)

            home = napi.structures[0]
            break
        except IndexError:
            lgr.error('Index error')
            _retry_throttle += 5
            lgr.warning('Retry call_nest with throttle of: %s' % _retry_throttle)
        except Exception as e:
            lgr.error('Unable to connect to Nest API endpoint: %s' % e)
            _retry_throttle += 5
            lgr.warning('Retry call_nest with throttle of: %s' % _retry_throttle)

    # I have two thermostats
    m_bed = home.thermostats[0]
    loft = home.thermostats[1]

    #print loft.name
    #print loft.temperature

    # Just get the thermostat for the loft for now
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
