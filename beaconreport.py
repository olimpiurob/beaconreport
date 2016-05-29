#!/usr/bin/python
#
# based on Taka Wang's work here: https://github.com/taka-wang/py-beacon
#
from datetime import datetime
from base import BaseMQTTClient
import blescan
import bluetooth._bluetooth as bluez
import calendar
import json


class Scanner(object):
    """Scanner."""
    def __init__(self, deviceId=0, loops=1):
        """Initialize scanner."""
        self.deviceId = deviceId
        self.loops = loops
        try:
            self.sock = bluez.hci_open_dev(self.deviceId)
            blescan.hci_le_set_scan_parameters(self.sock)
            blescan.hci_enable_le_scan(self.sock)
        except Exception, e:
            print e

    def scan(self):
        return blescan.parse_events(self.sock, self.loops)


class BeaconReport(BaseMQTTClient):
    """BeaconReport class"""
    def __init__(self, config_file='config'):
        super(BeaconReport, self).__init__(config_file=config_file)
        self.beacons = {}
        self.scanner = Scanner()

    def report(self, beacon, data):
        if self.mqtt_client:
            topic = self.topic_id + '%s' % beacon
            d = datetime.utcnow()
            timestamp = calendar.timegm(d.utctimetuple())
            data['tst'] = timestamp
            self.beacons[beacon]['datetime'] = d
            self.mqtt_client.publish(topic, json.dumps(data))

    def do_scan(self):
        if self.scanner:
            for beacon, data in self.scanner.scan().items():
                if beacon not in self.beacons.keys():
                    self.beacons[beacon] = {}
                self.report(beacon, data)

    def update_state(self, beacon, state):
        if self.mqtt_client:
            topic = self.topic_id + '%s' % beacon + '/state'
            self.mqtt_client.publish(topic, state)

    def check_states(self):
        now = datetime.utcnow()
        for beacon, data in self.beacons.items():
            do_update = False
            if (now - data.get('datetime')).total_seconds() < 120:
                if data.get('state') != 'home':
                    state = 'home'
                    do_update = True
            else:
                if data.get('state') != 'not_home':
                    state = 'not_home'
                    do_update = True

            if (now - data.get('last_pub')) > 120:
                do_update = True

            if do_update:
                self.update_state(beacon, state)
                data['last_pub'] = datetime.datetime.utcnow()
                data['state'] = state


if __name__ == '__main__':
    beacon_report = BeaconReport('config')
    while True:
        beacon_report.do_scan()
        beacon_report.check_states()
