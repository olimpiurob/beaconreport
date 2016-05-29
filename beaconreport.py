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
        self.scanner = Scanner()

    def report(self, topic, data):
        if self.mqtt_client:
            d = datetime.utcnow()
            timestamp = calendar.timegm(d.utctimetuple())
            data['tst'] = timestamp
            self.mqtt_client.publish(topic, json.dumps(data))

    def do_scan(self):
        if self.scanner:
            for beacon, data in self.scanner.scan().items():
                topic = self.topic_id + '%s' % beacon
                self.report(topic, data)

if __name__ == '__main__':
    beacon_report = BeaconReport('config')
    while True:
        beacon_report.do_scan()
