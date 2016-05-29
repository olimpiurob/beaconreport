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
import os


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
        self.beacons = self.get_known_beacons()
        self.scanner = Scanner()

    def get_known_beacons(self):
        beacons = {}
        with open("known_devices", "a+") as file:
            file.seek(0)
            for device in file:
                device = device.strip()
                if device not in beacons.keys():
                    beacons[device] = {}
        return beacons

    def add_known_beacon(self, mac_addr):
        with open("known_devices", "ab") as file:
            file.write(mac_addr)
            file.write('\n')

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
                    self.add_known_beacon(beacon)
                self.report(beacon, data)

    def update_state(self, beacon, state):
        if self.mqtt_client:
            topic = self.topic_id + '%s' % beacon + '/state'
            self.mqtt_client.publish(topic, state)

    def check_states(self):
        now = datetime.utcnow()
        for beacon, data in self.beacons.items():
            do_update = False
            state = data.get('state')
            if data.get('datetime') and (now - data.get('datetime')).total_seconds() < 120:
                if state != 'home':
                    state = 'home'
                    do_update = True
            else:
                if state != 'not_home':
                    state = 'not_home'
                    do_update = True

            if (now - data.get('last_pub', now)).total_seconds() > 120:
                do_update = True

            if do_update:
                self.update_state(beacon, state)
                data['last_pub'] = datetime.utcnow()
                data['state'] = state

if __name__ == '__main__':
    beacon_report = BeaconReport('config')
    while True:
        beacon_report.do_scan()
        beacon_report.check_states()
